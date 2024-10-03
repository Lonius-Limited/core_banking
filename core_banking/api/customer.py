import frappe
from frappe.utils import now_datetime
import traceback

@frappe.whitelist()
def create_customer(**kwargs):
    try:
        required_fields = ['cr_number', 'household_number', 'customer_name', 'identification_number']
        missing_fields = [field for field in required_fields if not kwargs.get(field)]

        if missing_fields:
            return {
                "status": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "missing_fields": missing_fields
            }

        cr_number = kwargs['cr_number']
        household_number = kwargs['household_number']
        customer_name = kwargs['customer_name']
        identification_number = kwargs['identification_number']

        # Check if customer with cr_number already exists
        if frappe.db.exists("Customer", {"customer_name": cr_number}):
            return {
                "status": False,
                "message": f"Customer with CR Number {cr_number} already exists.",
                "customer": cr_number
            }
        
        # Check if customer group (household) exists, create if not
        if not frappe.db.exists("Customer Group", household_number):
            customer_group = frappe.new_doc("Customer Group")
            customer_group.customer_group_name = household_number
            customer_group.parent_customer_group = "All Customer Groups"
            customer_group.insert()

        # Create customer
        customer = frappe.get_doc({
            "doctype": "Customer",
            # "customer_full_name": customer_name,
            "customer_name": cr_number,
            "customer_type": "Individual",
            "customer_group": household_number,
            "territory": "Kenya",
            "identification_type": "National ID",
            "identification_number": identification_number
        })
       
        customer.insert()

        frappe.db.commit()
        return {
            "status": True,
            "message": "Customer created successfully",
            "customer": customer.name
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(traceback.format_exc(), "Customer Creation Error")
        return {
            "status": False,
            "message": str(e),
            "traceback": traceback.format_exc()
        }