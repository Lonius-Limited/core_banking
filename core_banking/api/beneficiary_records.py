import frappe
from frappe.utils import now_datetime, today, flt
import traceback, json
from core_banking.api.customer import create_beneficiary


def _default_invoice_item():
    _item = frappe.db.get_single_value("Core Banking Settings", "default_invoice_item")
    if not _item:
        args = dict(
            doctype="Item",
            item_code="SHIF Contribution",
            item_name="SHIF Contribution",
            item_group="Services",
            maintain_stock=0,
        )
        frappe.get_doc(args).insert()
        _settings = frappe.get_doc("Core Banking Settings")
        _settings.set("default_invoice_item", "SHIF Contribution")
        _settings.save()
        frappe.db.commit()
        _item = "SHIF Contribution"
    return _item


@frappe.whitelist()
def post_payment_notification(**kwargs):
    try:
        if isinstance(kwargs, str):
            kwargs = json.loads(kwargs)
        kwargs.pop("cmd", None)
        cr_number = kwargs.pop("id", None)
        other_identifiers = kwargs.pop("other_identifications")
        _household_id = list(
            filter(
                lambda x: x.get("identification_type") == "Household Number",
                other_identifiers,
            )
        )[0]["identification_number"]
        identification_type = kwargs.get("identification_type")
        identification_number = kwargs.get("identification_number")
        amount = kwargs.get("amount")

        missing_fields = []
        if not (cr_number or identification_number):
            missing_fields.append("CR Number or ID Number")
        if not amount:
            missing_fields.append("Amount")

        if missing_fields:
            return {
                "status": False,
                "message": f"Either of the following field(s) are required: {', '.join(missing_fields)}",
            }

        try:
            amount = flt(amount)
        except ValueError:
            return {"status": False, "message": "Invalid amount provided"}
        #Check if customer exists and create if not
        customer_args = dict(name=cr_number)
        if identification_number:
            customer_args = dict(
                custom_identification_type=identification_type,
                custom_identification_number=identification_number,
            )
        _customer = frappe.db.get_value("Customer", customer_args)
        if not _customer:
            create_beneficiary_payload = {
                **kwargs,
                "id": cr_number,
                "household_number": _household_id,
            }
            _customer = create_beneficiary(**create_beneficiary_payload)
            # return dict(status="Pending", reason="We have scheduled")

        customer_name = _customer
        # Sales Invoice
        invoice = frappe.new_doc("Sales Invoice")
        invoice.customer = customer_name
        invoice.date = today()
        invoice.posting_time = now_datetime().time()
        invoice.append(
            "items",
            {
                "item_code": _default_invoice_item(),
                "qty": 1,
                "rate": amount,
                "amount": amount,
            },
        )
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
        payment_entry.paid_to = frappe.get_value(
            "Account",
            {"account_type": "Cash", "company": invoice.company, "is_group": 0},
            "name",
        )
        payment_entry.paid_from = invoice.debit_to

        # payment link to invoice
        payment_entry.append(
            "references",
            {
                "reference_doctype": "Sales Invoice",
                "reference_name": invoice.name,
                "total_amount": amount,
                "outstanding_amount": amount,
                "allocated_amount": amount,
            },
        )

        payment_entry.insert()
        payment_entry.submit()

        frappe.db.commit()

        return {
            "status": True,
            "message": "Generated successfully",
            "entry_ref": payment_entry.name,
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(traceback.format_exc(), "Entry Generation Error")
        return {"status": False, "message": str(e)}
