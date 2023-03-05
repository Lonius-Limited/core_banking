from email.policy import default
import frappe, datetime, calendar
from frappe.desk.query_report import run
from frappe import _
from frappe.utils.background_jobs import enqueue
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
	get_reports,
	payroll_gl_accrual,
	get_net_pay_totals,
)
from frappe.desk.query_report import run


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
		"debit_in_account_currency": flt(total, precision),
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
def submit_approved_slips():
	slips=frappe.db.sql("SELECT name FROM `tabSalary Slip` WHERE docstatus=0 AND journal_entry IS NOT NULL AND payroll_entry IN (SELECT name FROM `tabPayroll Entry` WHERE workflow_state='Approved') LIMIT 50", as_dict=1)
	if not slips: return
	# docs = [frappe.get_doc('Salary Slip',slip.get('name')) for slip in slips]
	list(map(lambda x: dispatch_email(x.get("name")),slips))
	# for doc in docs:
	#     employee = doc.get('employee')
	#     email = frape.get_value('Employee', employee, 'prefered_email')
	#     send_email(salary_slip)

def dispatch_email(salary_slip):
	print("Starting...")
	doc = frappe.get_doc('Salary Slip',salary_slip)
	employee = doc.get('employee')
	email = frappe.get_value('Employee', employee, 'prefered_email')
	payroll_month = calendar.month_name[doc.get("start_date").month]
	payroll_year = doc.get("start_date").year
	content = """<div class="ql-editor">
			<p>Hello {}</p>
			<p><br></p>
			<p>Please find your attached payslip for {} {}.</p>
			<p><br></p>
			<blockquote>NB: Ignore if you had already received this before.</blockquote>
			<blockquote>NB: Your Password is your Employee Number.</blockquote>
			<p><br></p>
			<p><br></p>
			<p>MANAGEMENT,</p>
			<p>MTRH PENSIONS SCHEME.</p>

			<p><br></p>
		</div>""".format(doc.get("employee_name"),payroll_month, payroll_year )
	print(content)
	frappe.enqueue(
		method=frappe.sendmail,
		now=True,
		reference_doctype='Salary Slip',
		reference_name=doc.get('name'),
		recipients=[email],
		cc="dsmwaura@gmail.com",
		subject='{} {} Payslip'.format(payroll_month, payroll_year),
		message = content,
		attachments = [frappe.attach_print(doc.doctype, doc.name, print_format="MTRHSPS Salary Slip", password=doc.get("employee"))]
	)
	# //print(email_args)
	# frappe.enqueue(method=frappe.sendmail, queue='short', timeout=300, **email_args)
	if doc.docstatus==1: return  
	doc.submit()
def process_approved_payrolls(doc, state):
	docname = doc.name
	if doc.get("workflow_state") == "Pending Approval":
		try:
			post_payroll_journal(docname)
		except Exception as e:
			frappe.throw(f"{e}")
	if doc.get("workflow_state") == "Approved":
		journal_entry = frappe.get_value(
			"Salary Slip", dict(payroll_entry=docname), "journal_entry"
		)
		if not journal_entry:
			frappe.throw(
				"Sorry, no accounting entries have been posted for approval, please click 'Send to Draft'."
			)
		jv = frappe.get_doc("Journal Entry", journal_entry)
		try:
			process_payroll_payments(jv, doc)
		except Exception as e:
			frappe.throw(f"{e}")


def process_payroll_payments(jv, payroll_entry_doc):  # (jv:doc,payroll_entry_doc:doc)
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
		pe.party_type = "Supplier"
		pe.party = default_payroll_party()
		####
		pe.title = "Payroll Deduction - {}".format(account_name)

		pe.payroll_entry = payroll_entry

		pe.custom_remarks = 1

		formatted_total = frappe.format(total, dict(fieldtype="Currency"))

		pe.remarks = "Being payment of {} to Payroll deduction: {} Transaction reference no {} dated {}".format(
			formatted_total, account_name, payroll_entry, posting_date
		)

		pe.save(ignore_permissions=True)

		payments.append(pe.name)
	payments_html = list(
		map(
			lambda x: "<a href='/app/payment-entry/{}' style='color:green'>{}</a><br><br>".format(
				x, x
			),
			payments,
		)
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


@frappe.whitelist()
def account_components_in_payroll_entry(account, payroll_entry, payment_entry=None):
	payroll_summary = get_reports(payroll_entry)
	components = [
		x.get("parent")
		for x in frappe.get_all(
			"Salary Component Account", filters=dict(account=account), fields=["*"]
		)
	]
	response =[]

	for component in components:
		report_name ="Company totals per Component"
		filters = dict(salary_component=component, payroll_entry=payroll_entry)
		pl = run(report_name, filters, user="Administrator")
		res = pl.get('result')
		
		if not res : return []
		data = [x for x in res if not isinstance(x,list)]
		list(map(lambda b:response.append(b),data))
	# # if payroll_entry:
	# heading = '<table class="table table-striped"><tr><td>Employee ID</td><td>Employee Name</td><td>Amount</td></tr>'
	# body_list = list(
	# 	map(
	# 		lambda employee: "<tr><td>{}</td><td>{}</td><td>{} {}</td></tr>".format(employee.get("employee"),employee.get("employee_name"),)
	# 	)
	# )
	return response

	
