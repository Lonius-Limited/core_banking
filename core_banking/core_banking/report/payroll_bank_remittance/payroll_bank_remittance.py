# Copyright (c) 2022, Lonius Limited and contributors
# For license information, please see license.txt

# import frappe

# Copyright (c) 2013, mtrh_devs@gmail.com and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	data = []
	filter_bank = filters.get('bank_name')
	def filter_func(value):
		return not filter_bank or value.get('bank_name') == filter_bank
	payroll_entry_number = filters.get('payroll_entry')
	salary_slips = frappe.get_all('Salary Slip', filters={'payroll_entry': payroll_entry_number }, fields=['*'])

	for slip in salary_slips:
		employee = slip.get('employee')
		employee_doc = frappe.get_doc('Employee', employee)
		new_data = {}
		new_data['employee'] = employee_doc.get('name')
		new_data['employee_name'] = employee_doc.get('employee_name')
		new_data['bank_name'] = employee_doc.get('bank') or employee_doc.get('bank_name')
		new_data['bank_code'] = employee_doc.get('bank_code')
		new_data['bank_branch_code'] = employee_doc.get('bank_branch_code') or employee_doc.get('branch_code')
		new_data['bank_branch_name'] = employee_doc.get('branch_name')
		new_data['bank_account_number'] = employee_doc.get('bank_ac_no')
		new_data['net_pay'] = slip.get("net_amount")
		# new_data['net_pay'] = (slip.total_taxable_earnings + slip.total_non_taxable_earnings + slip.total_non_cash_benefits)-slip.total_deduction
		data.append(new_data)

	options = list(dict.fromkeys([x.get('bank_name') for x in data])) 
	columns = [{
		"fieldname": "employee",
		"label": "Employee",
		"fieldtype": "Link",
		"options": "Employee",
		"width": 150
	}, {
		"fieldname": "employee_name",
		"label": "Employee Name",
		"fieldtype": "Data",
		"width": 150
	},{
		"fieldname": "bank_name",
		"label": "Bank Name",
		"fieldtype": "Select",
		"options": options,
		"width": 150
	},{
		"fieldname": "bank_branch_code",
		"label": "Bank Branch Code",
		"fieldtype": "Bank Branch",
		"width": 150
	},{
		"fieldname": "bank_branch_name",
		"label": "Bank Branch Name",
		"fieldtype": "Data",
		"width": 150
	},{
		"fieldname": "bank_account_number",
		"label": "Account Number",
		"fieldtype": "Data",
		"width": 150
	},{
		"fieldname": "net_pay",
		"label": "Net Pay",
		"fieldtype": "Currency",
		"width": 150
	}]

	return columns, list(filter(filter_func, data))

@frappe.whitelist()
def get_banks():
	sql = "SELECT DISTINCT bank_name FROM `tabEmployee` where bank_name is not null order by bank_name"
	data = frappe.db.sql(sql, as_dict=True)
	return [x.get('bank_name') for x in data]
# select bank_name, SUM(total_taxable_earnings + total_non_taxable_earnings + total_non_cash_benefits - total_deduction) from `tabSalary Slip` group by bank_name;

