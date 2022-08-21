# Copyright (c) 2022, Lonius Limited and contributors
# For license information, please see license.txt

# import frappe

import frappe
import json


def get_columns(salary_component_group):
	return [
		{
			"fieldname": frappe.scrub(x.get("salary_component")),
			"fieldtype": "Currency",
			"label": x.get("salary_component"),
			"default_value": 0.0
			# "options": "Salary Component",
		}
		for x in frappe.get_all(
			"Salary Component Group Detail",
			filters=dict(parent=salary_component_group),
			fields=["*"],
			order_by='idx'
		)
	]


def get_data(payroll_entry):
	db_values = frappe.get_all('Salary Slip Repository', fields=[
							   '*'], filters={'payroll_entry': payroll_entry}, order_by='employee')
	data = [{**json.loads(x.get('json_dump')), **x, 'id_number': frappe.db.get_value('Employee', x.get('employee'),
																					 'passport_number'), 'kra_pin': frappe.db.get_value('Employee', x.get('employee'), 'kra_pin')} for x in db_values]
	
	return data


def execute(filters=None):
	fetched_columns = get_columns(filters.get("salary_component_group"))
	columns = [{
		"fieldname": "employee",
		"fieldtype": "Link",
		"label": "Employee",
		"options": "Employee",
		"width": 150
	}, {
		"fieldname": "employee_name",
		"fieldtype": "Data",
		"label": "Employee Name",
		"width": 150
	}, {
		"fieldname": "id_number",
		"fieldtype": "Data",
		"label": "ID Number",
		"width": 150
	}, {
		"fieldname": "kra_pin",
		"fieldtype": "Data",
		"label": "KRA PIN",
		"width": 150
	}, *fetched_columns, {
		"fieldname": "total",
		"fieldtype": "Currency",
		"label": "Total",
		"width": 150
	}]

	# from_date, to_date = frappe.get_value("Payroll Entry", )
	column_keys = [x.get('fieldname') for x in fetched_columns]
	data = get_data(
		filters.get("payroll_entry"))
	output_data = []
	for item in [x for x in data if any(item in column_keys for item in list(x.keys()))]:
		new_item = {**item}
		total = 0.0
		for key in column_keys:
			if key not in item:
				new_item[key] = 0.0
			total+=new_item[key]
		new_item['total'] = total
		# Sum
		output_data.append(new_item)
	return columns, output_data
