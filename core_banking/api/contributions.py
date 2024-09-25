import frappe, json

def make_contribution(**kwargs):
    """
    Returns a payment_entry_reference, amount_paid and customer_id
    """
    payload = kwargs
    if isinstance(payload, str):
        payload = json.loads(payload)
    # Check if customer exists
    id_type, id_number =  payload.get("identification_type") or "National ID", payload.get("identification_number")
    id = payload.get("id") #CR Number
    customer = []
    if id:
        customer = frappe.db.get_all("Customer", filters=dict(cr_number=id)) or []
    else:
        customer = frappe.db.get_all("Customer", filters=dict(identification_number=id_number, identification_type=id_type)) or []
    if len(customer<0):
        customer_args = dict(doctype="Customer")
        customer = create_customer(customer_args)
    #Create Payment entry against customer
    payment_args = dict(doctype="Payment Entry")
def create_customer(**customer_args):
     #Create customer
    customer = frappe.get_doc(customer_args).save(ignore_permissions=1)
@frappe.whitelist()
def generate_bulk_payment_advice(**kwargs):
    """
    Accepts a JSON document that has:
    - Employer, Sponsoring organization and other meta-data such as Payroll Ref etc. 
    - A list of employees, sponsored persons etc
    
    Returns a Sales Invoice Reference and an amount.
    """
    pass
@frappe.whitelist()
def make_payment_confirmation(reference=None, amount=0.00):
    """
    Receive an invoice_reference and amount.
    Loops through linked Advice
    """
    try:
        if not reference: frappe.throw("Sorry, please provide the payment reference. Ensure you create the number with the appropriate check digit.")
        invoice = frappe.get_doc("Sales Invoice", reference)
        total = invoice.get("total")
        if total != amount:
            frappe.throw("Sorry, the amount does not match the amount in the invoice")
        # Schedule
    except Exception as e:
        frappe.throw("{}".format(e))
