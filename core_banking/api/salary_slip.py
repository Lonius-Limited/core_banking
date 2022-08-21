
import json
import multiprocessing as mp
from datetime import datetime
from warnings import filters
from core_banking.core_banking_payroll.salary_slip import computations

import frappe
from erpnext.payroll.doctype.payroll_entry.payroll_entry import (
	PayrollEntry,
	create_salary_slips_for_employees,
	get_existing_salary_slips,
)
from frappe.model import workflow
from frappe.share import add
from frappe.utils.data import nowdate, get_link_to_form, get_url_to_form
import psycopg2

from frappe.utils import (
	add_days,
	cint,
	cstr,
	date_diff,
	flt,
	formatdate,
	get_first_day,
	getdate,
	money_in_words,
	rounded,
)

def flatten_this_slip(payroll_entry='', slip=None, count=0):
	# return
	frappe.msgprint(slip.get("name"), "Adding to Analytics")
	dn = slip.get("employee") + "-" + payroll_entry
	if frappe.get_value("Salary Slip Repository", dn):
		frappe.get_doc("Salary Slip Repository", dn).delete(ignore_permissions=True)
	# net_pay = 0.00 + (
	# 	slip.get("total_taxable_earnings")
	# 	+ slip.get("total_non_taxable_earnings")
	# 	+ slip.get("total_non_cash_benefits")
	# 	- slip.get("total_deduction")
	# )
	doc = frappe.get_doc("Salary Slip", slip.get("name"))
	consolidated, nonpayrollbenefits,total_deductions = computations(doc)
	net_pay = consolidated - total_deductions or 0.0
	args = dict(
		employee=slip.employee, payroll_entry=payroll_entry, salary_slip=slip.name
	)
	
	dump_args = []
	earnings = [
		dict(
			salary_component=x.get("salary_component"),
			amount=x.get("amount"),
			type="Earning",
			idx=x.get("idx"),
			additional_salary=x.get("additional_salary"),
		)
		for x in doc.get("earnings")
	]
	deductions = [
		dict(
			salary_component=x.get("salary_component"),
			amount=x.get("amount"),
			type="Deduction",
			idx=x.get("idx"),
			additional_salary=x.get("additional_salary"),
		)
		for x in doc.get("deductions")
	]
	dump_args = [*earnings, *deductions]
	information = [
		dict(
			salary_component=x.get("salary_component"),
			amount=x.get("amount"),
			type="Information",
			idx=x.get("idx"),
		)
		for x in doc.get("information")
		if x.get("amount") > 0
	]

	if not dump_args:
		return
	payload = get_flat_repo(dump_args, information)
	# payload = dump_args[0]
	# type(dump_args)
	# return
	# for b in list(payload.keys()):
	# 	if type(payload.get(b)) in [datetime]:
	# 		payload[b] = payload.pop(b).strftime("%Y-%m-%d")
	payload["net_pay"] = net_pay
	args["doctype"] = "Salary Slip Repository"
	args["json_dump"] = json.dumps(payload)
	print("At {0}".format(count))
	frappe.get_doc(args).insert()
	frappe.db.commit()
def get_flat_repo(lst, information):
	#    return [x.get("salary_component"): x.get("amount") for x in lst][0]
	output = {}
	for item in lst:
		component = frappe.scrub(item.get("salary_component"))
		amount = item.get("amount")
		output[component] = amount
	for info in information:
		if not info.get("salary_component"):
			continue
		component = frappe.scrub(info.get("salary_component"))
		amount = info.get("amount")
		field = f"{component}_bal"
		output[field] = amount
	return output
def flatten_salary_slips():
	payroll_entry = "January 2022 Payroll"
	count = 0
	for slip in frappe.get_all(
		"Salary Slip", filters=dict(payroll_entry=payroll_entry), fields=["*"]
	):
		count += 1
		flatten_this_slip(payroll_entry=payroll_entry, slip=slip, count=count)

