// Copyright (c) 2022, Lonius Limited and contributors
// For license information, please see license.txt
/* eslint-disable */

// Copyright (c) 2016, mtrh_devs@gmail.com and contributors
// For license information, please see license.txt
/* eslint-disable */

const getOptions = () => {
	const res = frappe.call({
		method: 'core_banking.core_banking.report.payroll_bank_remittance.payroll_bank_remittance.get_banks',
		async: false,
	})
	// console.log(res.responseJSON.message)
	return res.responseJSON.message
}

frappe.query_reports["Payroll Bank Remittance"] = {
	"filters": [
		{
			"fieldname": "payroll_entry",
			"label": __("Payroll Entry"),
			"fieldtype": "Link",
			"options": "Payroll Entry",
			"reqd": 1
		},{
        "fieldname": "bank_name",
        "label": "Bank Name",
        "fieldtype": "Select",
		"options": getOptions(),
        "width": 150
    }
	]
};
