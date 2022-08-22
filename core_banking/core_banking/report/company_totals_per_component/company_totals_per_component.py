# Copyright (c) 2013, loniusdevs@gmail.com and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
	columns = [{
		"fieldname": "employee",
		"fieldtype": "Link",
		"label": "Employee",
		"options": "Employee",
		"width": 150
		},{
		"fieldname": "employee_name",
		"fieldtype": "Data",
		"label": "Employee Name",
		"width": 150
		},{
		"fieldname": "salary_slip",
		"fieldtype": "Link",
		"label": "Salary Slip",
		"options": "Salary Slip",
		"width": 150
		},{
		"fieldname": "salary_component",
		"fieldtype": "Link",
		"label": "Salary Component",
		"options": "Salary Component",
		"width": 150
		},{
		"fieldname": "id_number",
		"fieldtype": "Data",
		"label": "ID Number",
		"width": 150
		}, {
		"fieldname": "kra_pin",
		"fieldtype": "Data",
		"label": "KRA PIN",
		"width": 150
		}, {
		"fieldname": "amount",
		"fieldtype": "Currency",
		"label": "Amount",
		"width": 150
		},]
	data = []

	component = filters.get('salary_component')
	payroll_entry = filters.get('payroll_entry')

	sql = f"select slip.employee, slip.employee_name, slip.name as salary_slip, detail.salary_component, detail.amount, employee.passport_number as id_number, employee.kra_pin from `tabSalary Detail` detail inner join `tabSalary Slip` slip on slip.name = detail.parent inner join `tabEmployee` employee on employee.name = slip.employee where detail.salary_component = '{component}' and slip.payroll_entry = '{payroll_entry}'"

	data =  frappe.db.sql(sql, as_dict=1)


	return columns, data
