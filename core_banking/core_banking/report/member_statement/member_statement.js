// Copyright (c) 2022, Lonius Limited and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Member Statement"] = {
	"filters": [
		{
            fieldname: 'member',
            label: __('Member'),
            fieldtype: 'Link',
            options: 'Member',
			reqd: 1
            // default: frappe.defaults.get_user_default('company')
        },
        // {
        //     fieldname: 'member_name',
        //     label: __('Member Name'),
        //     fieldtype: 'Data',
        //     read_only:1,
        //     fetch_from: member.member_name
        //     // options: 'Member Name',
		// 	// reqd: 1
            
        //     // default: frappe.defaults.get_user_default('company')
        // },
		{
            fieldname: 'type_of_contribution',
            label: __('Type of Contribution'),
            fieldtype: 'Link',
            options: 'Item',
			"get_query" : function(){
				// var branch = frappe.query_report_filters_by_name.branch.get_value();
				return{
					"doctype": "Item",
					"filters":{
						"is_stock_item":0,
					}
				}
			}
            // default: frappe.defaults.get_user_default('company')
        },
		{
            fieldname: 'date_from',
            label: __('Date From'),
            fieldtype: 'Date',
			reqd:1
            // options: 'Member',
            // default: frappe.defaults.get_user_default('company')
        },
		{
            fieldname: 'date_to',
            label: __('Date To'),
            fieldtype: 'Date',
			reqd: 1
            // options: 'Member',
            // default: frappe.defaults.get_user_default('company')
        },
		

	]
};
