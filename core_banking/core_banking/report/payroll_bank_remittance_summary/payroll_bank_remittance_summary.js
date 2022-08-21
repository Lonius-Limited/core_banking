// Copyright (c) 2022, Lonius Limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Payroll Bank Remittance Summary"] = {
	"filters": [{
		"fieldname": "payroll_entry",
		"label": __("Payroll Entry"),
		"fieldtype": "Link",
		"options": "Payroll Entry",
		"reqd": 1
	},]
};

