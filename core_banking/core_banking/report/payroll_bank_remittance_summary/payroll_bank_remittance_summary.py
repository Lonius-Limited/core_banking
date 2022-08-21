# Copyright (c) 2022, Lonius Limited and contributors
# For license information, please see license.txt

# import frappe

import frappe

def execute(filters=None):
	columns = [{
		'fieldname': 'bank_name',
		'fieldtype': 'Data',
		'label': 'Bank Name',
		'width': 250
	}, {
		'fieldname': 'amount',
		'fieldtype': 'Currency',
		'label': 'Amount',
		'width': 250
	}]
	payroll_entry = filters.get('payroll_entry')
	sql = f"select UPPER(bank_name) as bank_name, sum(net_amount) as amount from `tabSalary Slip` where payroll_entry = '{payroll_entry}' group by bank_name order by bank_name asc"
	data = frappe.db.sql(sql, as_dict=1)
	return columns, data
