import frappe, requests, json


class HIE:
    def __init__(self) -> None:
        _doc = frappe.get_doc("Core Banking Settings")
        self.hie_base_url = _doc.get("hie_url")
        self.hie_user_name = _doc.get("hie_username")
        self.hie_password = _doc.get_password("hie_password")

    def fetch_cr_by_identifiers(self, **kwargs):
        payload = json.dumps(kwargs)
        response = requests.get(
            "{}/client-registry/fetch-client?payload={}".format(
                self.hie_base_url, payload
            ),
            auth=(self.hie_user_name, self.hie_password),
        )
        return response.json()


@frappe.whitelist()
# Pass Natural Identifiers
def member_statement(**kwargs):
    payload = kwargs
    if isinstance(payload, str):
        payload = json.loads(payload)
    payload.pop("cmd", None)
    _res = HIE().fetch_cr_by_identifiers(**payload)
    client = _res.get("message")
    if client.get("total") < 0:
        return {}
    _client_obj = client.get("result")[0]
    hh = [
        x
        for x in _client_obj.get("other_identifications")
        if x.get("identification_type") == "Household ID"
    ]
    if not hh:
        return {}
    return member_eligibility(household_id=hh[0])


def member_eligibility(household_id=None):
    from erpnext.accounts.utils import get_balance_on
    # Fetch member eligibility by household ID
    invoices = frappe.db.get_all(
        "Sales Invoice",
        filters=dict(
            customer_group=household_id.get("identification_number"), docstatus=["NOT IN", ["0", "2"]]
            
        ),
        order_by ="due_date DESC",
        fields=["name as reference", "grand_total as amount_due" , "MONTHNAME(due_date) as month", "YEAR(due_date) as year", "customer_group as household_id", "customer as member_id","status"]
    )
    if not invoices: return (dict(eligible=0,reason="Invoice Records not found"))
    
    customers = [x.get("name") for x in frappe.db.get_all("Customer", filters=dict(customer_group=household_id.get("identification_number")))]
    
    hh_balance = 0.00
    for customer in customers:
        _bal = get_balance_on(party=customer, party_type="Customer")
        hh_balance += _bal
        # print(customer, _bal)
    eligible = 0
    if hh_balance <= 0 : eligible =1
    return dict(unpaid=hh_balance, eligible=eligible, statement=invoices)
    
    