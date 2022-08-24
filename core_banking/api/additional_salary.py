import frappe, json

@frappe.whitelist()
def update_additional_salary(payload):
    data = json.loads(payload)

    if data.get("update_amount"):
        sql = "UPDATE `tabAdditional Salary` SET amount ={} WHERE name ='{}' AND docstatus=1 ;".format(data.get("amount"),data.get("name"))
        frappe.db.sql(sql)
        frappe.db.commit()
    return data
    # {'update_amount': 1, 'amount': 62758, 'update_balance': 0, 'amount_payable': 0, 'confirmation': '203', 'name': 'HR-ADS-22-03-00001'}
@frappe.whitelist()
def stop_additional_salary(docname,stop_date):
    frappe.msgprint("Stopping {} effective {}".format(docname,stop_date))
    sql = "UPDATE `tabAdditional Salary` SET to_date ='{}' WHERE name ='{}' AND docstatus=1 ;".format(stop_date,docname)
    frappe.db.sql(sql)
    frappe.db.commit()
    data = dict(docname=docname,stop_date=stop_date)
    return data