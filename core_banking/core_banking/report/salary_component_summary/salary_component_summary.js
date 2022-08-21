// Copyright (c) 2022, Lonius Limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Salary Component Summary"] = {
	"filters": [
		{
			"fieldname": "salary_component_group",
			"label": __("Salary Component Group"),
			"fieldtype": "Link",
			"options": "Salary Component Group",
			"reqd": 1,
			"get_query": function(){
				return{
					filters: [
						["Salary Component Group", "docstatus", "=", 1]
					]
				}
			}
		},
		{
			"fieldname": "payroll_entry",
			"label": __("Payroll Entry"),
			"fieldtype": "Link",
			"options": "Payroll Entry",
			"reqd": 1
		},
	]
};
