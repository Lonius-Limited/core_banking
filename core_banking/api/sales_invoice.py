import frappe
from frappe.utils import now_datetime, today, flt
import traceback

@frappe.whitelist()
def create_sales_invoice(**kwargs):
    try:
        cr_number = kwargs.get('cr_number')
        amount = kwargs.get('amount')
        identification_number = kwargs.get('id_number')

        if not identification_number or not amount:
            # frappe.throw("CR Number and Amount are required")
            return {"status": False, "message": "Both ID number and Amount are required"}

        try:
            amount = flt(amount)
        except ValueError:
            # frappe.throw("Invalid amount provided")
            return {"status": False, "message": "Invalid amount provided"}

        if not frappe.db.exists("Customer", identification_number):
            # frappe.throw(f"Customer with CR Number {cr_number} does not exist")
            return {"status": False, "message": f"Customer with ID Number {identification_number} does not exist"}

        # Sales Invoice
        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = identification_number
        invoice.date = today()
        invoice.posting_time = now_datetime().time()
        invoice.append("items", {
            "item_code": "SHA PAYMENT",
            "qty": 1,
            "rate": amount,
            "amount": amount
        })
        invoice.insert()
        invoice.submit()

        # Payment Entry
        payment_entry = frappe.new_doc("Payment Entry")
        payment_entry.payment_type = "Receive"
        payment_entry.posting_date = today()
        payment_entry.mode_of_payment = "Cash"
        payment_entry.party_type = "Customer"
        payment_entry.party = identification_number
        payment_entry.party_name = identification_number
        payment_entry.paid_amount = amount
        payment_entry.received_amount = amount
        payment_entry.reference_no = invoice.name
        payment_entry.reference_date = today()

        # company and currency details
        payment_entry.company = invoice.company
        payment_entry.paid_to_account_currency = invoice.currency
        payment_entry.paid_from_account_currency = invoice.currency
        payment_entry.source_exchange_rate = 1
        payment_entry.target_exchange_rate = 1

        # accounts
        payment_entry.paid_to = frappe.get_value("Account", {"account_type": "Cash", "company": invoice.company, "is_group": 0}, "name")
        payment_entry.paid_from = invoice.debit_to

        # payment link to invoice
        payment_entry.append("references", {
            "reference_doctype": "Sales Invoice",
            "reference_name": invoice.name,
            "total_amount": amount,
            "outstanding_amount": amount,
            "allocated_amount": amount
        })

        payment_entry.insert()
        payment_entry.submit()

        frappe.db.commit()

        return {
            "status": True,
            "message": "Sales Invoice created and paid successfully",
            "invoice": invoice.name,
            "payment_entry": payment_entry.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(traceback.format_exc(), "Sales Invoice and Payment Creation Error")
        # frappe.throw(traceback.format_exc())
        return {"status": False, "message": str(e), "traceback": traceback.format_exc()}
    