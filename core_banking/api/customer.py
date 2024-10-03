import frappe
from frappe.utils import now_datetime
import traceback


@frappe.whitelist()
def create_customer(**kwargs):
    try:
        required_fields = [
            "cr_number",
            "household_number",
            "customer_name",
            "identification_number",
        ]
        missing_fields = [field for field in required_fields if not kwargs.get(field)]

        if missing_fields:
            return {
                "status": False,
                "message": f"Missing required fields: {', '.join(missing_fields)}",
                "missing_fields": missing_fields,
            }

        cr_number = kwargs["cr_number"]
        household_number = kwargs["household_number"]
        customer_name = kwargs["customer_name"]
        identification_number = kwargs["identification_number"]

        # Check if customer with cr_number already exists
        if frappe.db.exists("Customer", {"customer_name": cr_number}):
            return {
                "status": False,
                "message": f"Customer with CR Number {cr_number} already exists.",
            }

        # Check if customer group (household) exists, create if not
        if not frappe.db.exists("Customer Group", household_number):
            customer_group = frappe.new_doc("Customer Group")
            customer_group.customer_group_name = household_number
            customer_group.parent_customer_group = "All Customer Groups"
            customer_group.insert()

        # Create customer
        customer = frappe.get_doc(
            {
                "doctype": "Customer",
                "customer_name": identification_number,
                "customer_full_names": customer_name,
                # "cr_number": cr_number,
                "customer_type": "Individual",
                "customer_group": household_number,
                "territory": "Kenya",
                "identification_type": "National ID",
                "identification_number": identification_number,
            }
        )

        customer.insert()

        frappe.db.commit()
        return {
            "status": True,
            "message": "Customer created successfully",
            "customer": customer.name,
        }

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(traceback.format_exc(), "Customer Creation Error")
        return {"status": False, "message": str(e), "traceback": traceback.format_exc()}


def create_beneficiary(**kwargs):
    mandatory_fields = [
        "id",
        "identification_type",
        "identification_number",
        "full_name",
        "household_number",
        "employment_type",
    ]
    _missing_variables = []
    for k in mandatory_fields:
        if k not in list(kwargs.keys()):
            _missing_variables.append(k)
    if _missing_variables: frappe.throw("Missing values {}".format(_missing_variables))
    
    # Check if customer group (household) exists, create if not
    if not frappe.db.exists("Customer Group",  kwargs.get("household_number")):
        customer_group = frappe.new_doc("Customer Group")
        customer_group.customer_group_name =  kwargs.get("household_number")
        customer_group.parent_customer_group = "All Customer Groups"
        customer_group.insert()
    # Begin transaction 
    customer_args = {
                "doctype": "Customer",
                "customer_name": kwargs.get("id"),
                "custom_customer_full_name": kwargs.get("full_name"),
                # "cr_number": cr_number,
                "customer_type": "Individual",
                "customer_group": kwargs.get("household_number"),
                "territory": "Kenya",
                "custom_identification_type": kwargs.get("identification_type"),
                "custom_identification_number": kwargs.get("identification_number"),
                "custom_employment_status": kwargs.get("employment_type")
            }
    customer = frappe.get_doc(customer_args)
    customer.db_insert()
    frappe.db.commit()
    return customer.get("name")
    
        
