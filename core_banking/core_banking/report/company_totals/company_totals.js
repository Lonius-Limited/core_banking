// Copyright (c) 2022, Lonius Limited and contributors
// For license information, please see license.txt
/* eslint-disable */



frappe.query_reports["Company Totals"] = {
	"filters": [
		{
			"fieldname": "payroll_entry",
			"label": __("Payroll Entry"),
			"fieldtype": "Link",
			"options": "Payroll Entry",
			"reqd": 1
		},
		{
			"fieldname": "report_type",
			"label": __("Report Type"),
			"fieldtype": "Select",
			"options": "Taxable Earnings \nNon Cash Benefits \nRelief \nDeductions \nNet Pay",
			"reqd": 1
		}
	]
};


// frappe.ui.form.on('Payroll Entry', {
// 	refresh(frm) {
// 		frm.add_custom_button(__('Generate Report'), function(){
// 			if(frm.doc.name) {
// 				frappe.call({
// 					method: 'hris.hris.report.company_totals.company_totals.update_reports',
// 					args: {
// 						payroll_entry: 'HR-PRUN-2021-00026',
// 					},
// 					callback: ({ message }) => {
// 						console.log(message)
// 					}
// 				})
// 			}
// 		}, __("Report"));
// 	}
// })
