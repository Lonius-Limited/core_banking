from email.policy import default
import frappe
from frappe.desk.query_report import run
from frappe import _
from frappe.utils import (
	DATE_FORMAT,
	add_days,
	add_to_date,
	cint,
	comma_and,
	date_diff,
	flt,
	getdate,
)
from core_banking.core_banking.report.company_totals.company_totals import (
	payroll_gl_accrual,
	get_net_pay_totals,
)


def set_title_field(doc, state):
	if doc.get("payroll_month"):
		return doc
	title = frappe.utils.formatdate(doc.get("start_date"), "MMMM, yyyy")
	doc.set("payroll_month", title + " Payroll")


@frappe.whitelist()
def close_payroll(payroll_entry):
	# Submit Payroll Slips
	filters = dict(payroll_entry=payroll_entry, docstatus=0)
	fields = ["name"]
	unsubmitted = [
		frappe.get_doc("Salary Slip", x.get("name"))
		for x in frappe.get_all("Salary Slip", filters=filters, fields=fields)
	]
	count = len(unsubmitted)
	if count < 20:
		list(map(lambda x: x.submit(), unsubmitted))
		doc = frappe.get_doc("Payroll Entry", payroll_entry)
		doc.db_set("salary_slips_submitted", 1)
	else:
		# schedule for later(TBD as at 7/31)
		pass


@frappe.whitelist()
def post_payroll_journal(payroll_entry):
	try:
		entry = get_payroll_entry_accrual(payroll_entry)
		entry.save()
		entry.submit()
		update_html_journal_details(payroll_entry, entry.get("accounts"))
		update_slips(payroll_entry, entry.name)
		return entry
	except Exception as e:
		frappe.db.rollback()
		frappe.throw(f"{e}")


def update_html_journal_details(payroll_entry, accounts: list):
	html = payroll_html(accounts)
	sql = "UPDATE `tabPayroll Entry` SET journal_details='{}' WHERE name ='{}'".format(
		html, payroll_entry
	)
	frappe.db.sql(sql)
	return html


def payroll_html(accounts: list):
	html = """
	<div class="container">
	<table class = "table table-responsive table-striped">
	  <thead>
	<tr>
	  <th>Account</th>
	  <th>Debit</th>
	  <th>Credit</th>
	</tr>
  </thead><tbody>
	"""
	total_dr_cr = 0.0
	for row in accounts:
		debit = frappe.format(
			row.get("debit_in_account_currency") or 0.0, dict(fieldtype="Currency")
		)
		credit = frappe.format(
			row.get("credit_in_account_currency") or 0.0, dict(fieldtype="Currency")
		)
		total_dr_cr += float(row.get("debit_in_account_currency") or 0.0) + float(
			row.get("credit_in_account_currency") or 0.0
		)
		html += "<tr><td>{}</td><td>{}</td><td>{}</td></tr>".format(
			row.get("account"), debit, credit
		)
	formatted_total = frappe.format(total_dr_cr / 2, dict(fieldtype="Currency"))
	footer = "<tfoot><tr><td>Totals:</td><td>{}</td><td>{}</td></tr></tfoot>".format(
		formatted_total, formatted_total
	)
	html += f"</tbody>{footer}<table></div>"
	return html


def update_slips(payroll_entry, journal_entry):
	sql = "UPDATE `tabSalary Slip` set journal_entry='{}' WHERE payroll_entry='{}';"
	frappe.db.sql(sql.format(journal_entry, payroll_entry))


@frappe.whitelist()
def get_payroll_entry_accrual(payroll_entry):
	args = payroll_gl_accrual(payroll_entry)
	earnings = get_earnings_account_details(payroll_entry, args, "earnings") or []
	deductions = get_earnings_account_details(payroll_entry, args, "deductions") or []
	# frappe.throw(f"{earnings} \n {deductions}")
	company_sponsored = get_company_contributions(payroll_entry, args)
	doc = frappe.get_doc("Payroll Entry", payroll_entry)
	if earnings or deductions:
		accounts = []

		journal_entry = frappe.new_doc("Journal Entry")
		journal_entry.voucher_type = "Journal Entry"
		journal_entry.user_remark = _(
			"Accrual Journal Entry for salaries from {0} to {1}"
		).format(doc.start_date, doc.end_date)
		journal_entry.company = doc.company
		journal_entry.posting_date = doc.posting_date

		accounts = earnings + deductions + company_sponsored

		journal_entry.set("accounts", accounts)

		# frappe.throw(f"{payroll_html(accounts)}")
		return journal_entry
	return []


def get_salary_component_account(doc, salary_component):  # payroll entry document
	account = frappe.db.get_value(
		"Salary Component Account",
		{"parent": salary_component, "company": doc.company},
		"account",
	)

	# if not account:
	# 	frappe.throw(_("Please set account in Salary Component {0}")
	# 		.format(salary_component))
	return account or frappe.get_value(
		"Company", doc.company, "default_payroll_payable_account"
	)


def get_earnings_account_details(payroll_entry, args, component_type):
	def _get_gl_sum(account: str, gl_entries: list):
		filtered = list(filter(lambda x: x.get("account") == account, gl_entries))
		gl_sum = 0.00
		for b in filtered:
			gl_sum += float(b.get("total"))
		return gl_sum

	accounts = []
	doc = frappe.get_doc("Payroll Entry", payroll_entry)
	context = (
		args.get("taxable") if component_type == "earnings" else args.get("deductions")
	)
	for component in context:
		salary_component = component.get("salary_component")
		if (
			str(
				frappe.get_value(
					"Salary Component", salary_component, "is_company_contribution"
				)
				or ""
			)
			== "1"
		):
			continue
		gl = get_salary_component_account(doc, salary_component)
		accounts.append(dict(account=gl, **component))
	for component in args.get("relief"):
		salary_component = component.get("salary_component")
		gl = get_salary_component_account(doc, salary_component)
		if (
			not str(
				frappe.get_value(
					"Salary Component", salary_component, "is_company_contribution"
				)
				or ""
			)
			== "1"
		):
			continue
	for component in args.get("non_cash"):
		salary_component = component.get("salary_component")
		gl = get_salary_component_account(doc, salary_component)
		if (
			not str(
				frappe.get_value(
					"Salary Component", salary_component, "is_company_contribution"
				)
				or ""
			)
			== "1"
		):
			continue
	if component_type == "deductions":
		net_pay = get_net_pay_totals(payroll_entry)
		salary_component = "Net Pay"
		gl = get_salary_component_account(doc, salary_component)
		accounts.append(dict(account=gl, total=net_pay[0].get("total")))
	# total = reduce(lambda x, y: x + y, accounts)
	gl_accounts = list(dict.fromkeys([x.get("account") for x in accounts]))
	# frappe.throw(f"The accounts: {gl_accounts}")
	journal = []
	for acc in gl_accounts:
		total = _get_gl_sum(acc, accounts)
		journal.append(dict(account=acc, value=total))
	# return journal
	return update_journal_entry(journal, component_type, doc)


def get_company_contributions(payroll_entry, args):
	def _get_gl_sum(account: str, gl_entries: list):
		filtered = list(filter(lambda x: x.get("account") == account, gl_entries))
		gl_sum = 0.00
		for b in filtered:
			gl_sum += float(b.get("total"))
		return gl_sum

	# context  = args.get('relief') + args.get('non_cash')
	doc = frappe.get_doc("Payroll Entry", payroll_entry)
	accounts = []
	for component in args.get("relief"):
		salary_component = component.get("salary_component")
		gl = get_salary_component_account(doc, salary_component)
		if (
			str(
				frappe.get_value(
					"Salary Component", salary_component, "is_company_contribution"
				)
				or "0"
			)
			== "1"
		):
			accounts.append(dict(account=gl, **component))
	for component in args.get("non_cash"):
		salary_component = component.get("salary_component")
		gl = get_salary_component_account(doc, salary_component)
		if (
			str(
				frappe.get_value(
					"Salary Component", salary_component, "is_company_contribution"
				)
				or "0"
			)
			== "1"
		):
			accounts.append(dict(account=gl, **component))
	gl_accounts = list(dict.fromkeys([x.get("account") for x in accounts]))
	journal = []
	for acc in gl_accounts:
		total = _get_gl_sum(acc, accounts)
		journal.append(dict(account=acc, value=total))
	return get_relief_accounts(journal, doc)


def update_journal_entry(journal_entry, component_type, payroll_entry):
	precision = frappe.get_precision(
		"Journal Entry Account", "debit_in_account_currency"
	)
	for acc in journal_entry:
		amt = acc.get("value")
		obj = {
			"debit_in_account_currency": flt(amt, precision),
			"exchange_rate": flt(1),
			"cost_center": payroll_entry.cost_center,
			"project": payroll_entry.project,
			"reference_type": "Payroll Entry",
			"reference_name": payroll_entry.name,
		}
		if component_type in ["deductions", "relief", "non_cash"]:
			obj["credit_in_account_currency"] = flt(amt, precision)
			obj.pop("debit_in_account_currency")
		acc.update(obj)
	return journal_entry


def get_relief_accounts(journal_entry, payroll_entry):
	precision = frappe.get_precision(
		"Journal Entry Account", "debit_in_account_currency"
	)
	total = 0.0
	for acc in journal_entry:
		amt = acc.get("value") or 0.0
		total += amt
		obj = {
			"credit_in_account_currency": flt(amt, precision),
			"exchange_rate": flt(1),
			"cost_center": payroll_entry.cost_center,
			"project": payroll_entry.project,
			"reference_type": "Payroll Entry",
			"reference_name": payroll_entry.name,
		}
		acc.update(obj)
	default_salary_component_expense = frappe.get_value(
		"Company", payroll_entry.company, "default_company_contribution_account"
	)
	expense_obj = {
		"account": default_salary_component_expense,
		"value": total,
		"debit_in_account_currency": flt(amt, precision),
		"exchange_rate": flt(1),
		"cost_center": payroll_entry.cost_center,
		"project": payroll_entry.project,
		"reference_type": "Payroll Entry",
		"reference_name": payroll_entry.name,
	}
	journal_entry.append(expense_obj)
	return journal_entry


def override_salary_slip_submit(doc, state):
	print("Doing no other stuff")
	return doc


def process_approved_payrolls(doc, state):
	docname = doc.name
	if doc.get("workflow_state") == "Pending Approval":
		try:
			post_payroll_journal(docname)		
		except Exception as e:
			frappe.throw(f"{e}")
	if  doc.get("workflow_state") == "Approved":
		journal_entry = frappe.get_value("Salary Slip",dict(payroll_entry=docname),"journal_entry")
		if not journal_entry: frappe.throw("Sorry, no accounting entries have been posted for approval, please click 'Send to Draft'.")
		jv = frappe.get_doc("Journal Entry",journal_entry)
		try:
			process_payroll_payments(jv, doc)
		except Exception as e:
			frappe.throw(f"{e}")
def process_payroll_payments(jv, payroll_entry_doc):#(jv:doc,payroll_entry_doc:doc)
	posting_date = payroll_entry_doc.get("posting_date")
	payroll_entry = payroll_entry_doc.get("name")
	# frappe.throw(f"{posting_date}")
	accounts = [
		x for x in jv.get("accounts") if x.get("credit_in_account_currency") > 0.0
	]
	distinct_accounts = list(dict.fromkeys([x.get("account") for x in accounts]))
	
	company = jv.get("company")
	default_cash_account = frappe.get_value("Company", company, "default_cash_account")

	def _get_gl_sum(account, accounts):
		return (
			sum(
				[
					x.get("credit_in_account_currency")
					for x in accounts
					if x.get("account") == account
				]
			)
			or 0.0
		)

	payments = []
	for acc in distinct_accounts:
		total = _get_gl_sum(acc, accounts)
		account_name = frappe.get_value("Account", acc, "account_name")
		pe = frappe.new_doc("Payment Entry")
		pe.payment_type = "Pay"
		pe.company = company
		pe.posting_date = posting_date
		pe.paid_from = default_cash_account
		pe.paid_to = acc
		pe.paid_amount = total
		pe.received_amount = total
		pe.reference_no = payroll_entry
		pe.reference_date = posting_date
		pe.party_type = ("Supplier")
		pe.party = default_payroll_party()
		####
		pe.title = "Payroll Deduction - {}".format(account_name)

		pe.custom_remarks = 1

		formatted_total = frappe.format(total, dict(fieldtype="Currency"))

		pe.remarks = "Being payment of {} to Payroll deduction: {} Transaction reference no {} dated {}".format(
		    formatted_total, account_name, payroll_entry, posting_date
		)

		pe.save(ignore_permissions=True)

		payments.append(pe.name)
	payments_html = list(
	    map(lambda x: "<a href='/app/payroll-entry/{}' style='color:green'>{}</a>".format(x,x), payments)
	)
	frappe.msgprint(
	    "<h4>Posted {} payment documents:</h4>{}".format(
	        len(payments_html), "".join(payments_html)
	    )
	)
def default_payroll_party():
	default = "Payroll Deductions"
	if not frappe.get_value("Supplier", default):
		args = dict(
			doctype="Supplier",
			supplier_name=default,
			supplier_group="Services",
			supplier_type="Company",
		)
		frappe.get_doc(args).insert()
	return default
