# Copyright (c) 2022, Lonius Limited and contributors
# For license information, please see license.txt

import frappe
from frappe import _

# from pkgutil import get_data


def execute(filters=None):
	
	columns, data = get_columns(), get_data(filters)
	return columns, data
def get_columns():
	#posting_date,contribution_type, contribution
	return [
		{
			"label": _("Posting Date"),
			"fieldtype": "Date",
			"fieldname": "posting_date",
			# "options": "Account",
			"width": 100
		},
		{
			"label": _("Contribution Type"),
			"fieldtype": "Link",
			"fieldname": "contribution_type",
			"options": "Item",
			"width": 300
		},
		{
			"label": _("Contribution/Settlement"),
			"fieldtype": "Currency",
			"fieldname": "contribution",
			# "options": "Account",
			"width": 200
		},
		{
			"label": _("Reference"),
			"fieldtype": "Link",
			"fieldname": "reference",
			"options": "Sales Invoice",
			"width": 200
		},
		{
			"label": _("Narration"),
			"fieldtype": "Data",
			"fieldname": "narration",
			# "options": "Sales Invoice",
			"width": 400
		},
	]
def get_data(filters):
	contribution_cond = ""
	customer = frappe.get_value('Member', filters.get("member"),'customer')
	# frappe.msgprint(customer)
	if filters.get("type_of_contribution"):
		contribution_cond = "AND item_code = '{}'".format(filters.get("type_of_contribution"))
	sales_inv_cond = "SELECT name FROM `tabSales Invoice`  WHERE customer = '{}' AND docstatus = 1 AND posting_date BETWEEN '{}' AND '{}' ".format(customer, filters.get("date_from"), filters.get("date_to"))
	query ="SELECT CAST(creation AS DATE) as posting_date, item_code as contribution_type, amount as contribution, parent as reference,'-' as narration FROM `tabSales Invoice Item`  WHERE parent IN ({}) {} AND amount > 0.0 ORDER BY creation DESC".format(sales_inv_cond,contribution_cond)
	# frappe.msgprint(f"{filters}")
	payload = frappe.db.sql(query, as_dict=1)
	for row in payload:
		remarks = frappe.get_value('Sales Invoice', row.get('reference'),'remarks')
		row.narration = remarks or ''
	out =  frappe.db.get_all("Payment Entry",filters=dict(docstatus=1,party_type='Member', party=filters.get("member"),payment_type='Pay'), fields=['paid_amount','posting_date','name','remarks'])
	# out =  frappe.db.get_all("Payment Entry",filters=dict(docstatus=1,party_type='Member', party=filters.get("member"),payment_type='Pay',posting_date=["BETWEEN",[filters.get("date_from"),filters.get("date_to")]]), fields=['paid_amount','posting_date','name','remarks'])
	if not out: return payload

	for transaction in out:
		payload.append(
			dict(
				posting_date=transaction.get('posting_date'),
				contribution_type="<b style='color:red'>Withdrawal</b>",
				contribution=float(transaction.get('paid_amount'))*-1,
				reference = transaction.get('name'),
				narration = transaction.get('remarks')
				)
			)
	# return payload
	return sorted(payload, key = lambda i: i['posting_date'], reverse=True)