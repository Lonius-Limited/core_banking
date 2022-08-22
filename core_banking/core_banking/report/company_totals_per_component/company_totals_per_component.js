// Copyright (c) 2016, mtrh_devs@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Company totals per Component"] = {
	"filters": [
		{
			"fieldname": "payroll_entry",
			"label": __("Payroll Entry"),
			"fieldtype": "Link",
			"options": "Payroll Entry",
			"reqd": 1
		},{
			"fieldname": "salary_component",
			"label": __("Salary Component"),
			"fieldtype": "Link",
			"options": "Salary Component",
			"reqd": 1
		},
	]
};
