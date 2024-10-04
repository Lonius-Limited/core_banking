import frappe
from frappe.utils import now_datetime, today, flt
import traceback

@frappe.whitelist()
def post_payment_notification(**kwargs):
    try:
        cr_number = kwargs.get('cr_number')
        id_number = kwargs.get('id_number')
        amount = kwargs.get('amount')

        args = dic

        missing_fields = []
        if not (cr_number or id_number):
            missing_fields.append("CR Number or ID Number")
        if not amount:
            missing_fields.append("Amount")

        if missing_fields:
            return {
                "status": False, 
                "message": f"The following field(s) are required: {', '.join(missing_fields)}"
            }

        try:
            amount = flt(amount)
        except ValueError:
            return {"status": False, "message": "Invalid amount provided"}

        # Get Customer
        # if cr_number:
        #     if not frappe.db.exists("Customer", cr_number):
        #         return {"status": False, "message": f"Customer with CR Number {cr_number} does not exist"}
        #     customer_name = cr_number
        # else:
        #     customer = frappe.get_list("Customer", filters={"cr_number": id_number}, fields=["name"])
        #     if not customer:
        #         return {"status": False, "message": f"Customer with CR Number {id_number} does not exist"}
        #     customer_name = customer[0].name



        # Sales Invoice
        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = customer_name
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
        payment_entry.party = customer_name
        payment_entry.party_name = customer_name
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
            "message": "Generated successfully",
            "entry_ref": payment_entry.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(traceback.format_exc(), "Entry Generation Error")
        return {"status": False, "message": str(e), "traceback": traceback.format_exc()}