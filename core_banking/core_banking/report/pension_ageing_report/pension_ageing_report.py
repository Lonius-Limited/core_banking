# Copyright (c) 2022, Lonius Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from core_banking.api.member import get_member_net_contribution
from datetime import datetime, date, timedelta
def execute(filters=None):
	columns, data = get_columns(), get_data(filters)
	return columns, data
def get_columns():
	#Member|Member Name|Net Contribution|Date of Joining|Membership Status|DOB|Date of Retirement|YTR|
	return [
		{
			"label": _("Member"),
			"fieldtype": "Link",
			"fieldname": "member",
			"options": "Member",
			"width": 100
		},
		{
			"label": _("Member Name"),
			"fieldtype": "Data",
			"fieldname": "member_name",
			# "options": "Member",
			"width": 250
		},
		{
			"label": _("Net Contribution"),
			"fieldtype": "Currency",
			"fieldname": "net_contribution",
			"default": 0.00,
			"width": 200
		},{
			"label": _("Date of Joining"),
			"fieldtype": "Date",
			"fieldname": "date_of_joining",
			# "options": "Account",
			"width": 200
		},{
			"label": _("Membership Status"),
			"fieldtype": "Data",
			"fieldname": "membership_status",
			# "options": "Account",
			"width": 150
		},{
			"label": _("Date of Birth"),
			"fieldtype": "Date",
			"fieldname": "date_of_birth",
			# "options": "Account",
			"width": 200
		},
		{
			"label": _("Date of Retirement"),
			"fieldtype": "Date",
			"fieldname": "date_of_retirement",
			# "options": "Account",
			"width": 200
		},{
			"label": _("Years to Retirement"),
			"fieldtype": "Int",
			"fieldname": "years_to_retirement",
			# "options": "Account",
			"width": 100
		},
		{
			"label": _("Gender"),
			"fieldtype": "Link",
			"fieldname": "gender",
			"options": "Gender",
			"width": 100
		},
		{
			"label": _("Persons With Disability"),
			"fieldtype": "Check",
			"fieldname": "persons_with_disability",
			# "options": "Account",
			"default" : 0,
			"width": 50
		},
	]
def get_data(filters):
	# Member|Member Name|Net Contribution|Date of Joining|Membership Status|DOB|Date of Retirement|YTR|
	member_cond =""
	if filters.get("member"):
		member_cond ="AND name='{}'".format(filters.get("member"))
	query = """SELECT name as member, member_name,'' AS net_contribution,date_of_joining,membership_status,date_of_birth,date_of_retirement,'' AS years_to_retirement, gender,persons_with_disability FROM `tabMember` WHERE membership_type='{}' {} ;""".format(filters.get("sponsor"),member_cond)
	result = frappe.db.sql(query, as_dict=1)

	for row in result:
		balance =0.0
		balance = get_member_net_contribution(row.get("member"))
		retirement =row.get("date_of_retirement")
		ytr = retirement.year - date.today().year
		##Replace fields
		row.net_contribution = balance
		row.years_to_retirement = ytr

		m_status = row.membership_status
		
		status_color_code = 'green' if m_status == 'Active' else 'red'

		row.membership_status = "<b style='color:{}'>{}</b>".format(status_color_code,m_status)

	return result