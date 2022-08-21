// Copyright (c) 2022, Lonius Limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Pension Ageing Report"] = {
	"filters": [
		{
            fieldname: 'sponsor',
            label: __('Sponsor'),
            fieldtype: 'Link',
            options: 'Membership Type',
			reqd: 1
            // default: frappe.defaults.get_user_default('company')
        },
		{
            fieldname: 'member',
            label: __('Member'),
            fieldtype: 'Link',
            options: 'Member',
			// reqd: 1
            // default: frappe.defaults.get_user_default('company')
        },
	]
};
