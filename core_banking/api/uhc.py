import frappe, requests, json
from datetime import datetime, timedelta

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
class Member:
    def __init__(self) -> None:
        pass
    def fetch_member_by_cr_number():
        # Return the same payload
        pass

@frappe.whitelist()
# Pass Natural Identifiers
def member_statement(**kwargs):
    payload = kwargs
    if isinstance(payload, str):
        payload = json.loads(payload)
    payload.pop("cmd", None)
    _res = HIE().fetch_cr_by_identifiers(**payload)
    if not _res.get("message") : return dict(eligible=0,reason="Client Records for requested Identifiers were not found.", possible_solution="Client to Register for Social Health Authority using valid identifiers")
    client = _res.get("message")
    if client.get("total") < 1:
        return dict(eligible=0,reason="Client Records for requested Identifiers were not found.", possible_solution="Client to Register for Social Health Authority using valid identifiers")
    _client_obj = client.get("result")[0]
    employment_type = _client_obj.get("employment_type")
    full_name = "{} {}".format(_client_obj.get("first_name"),_client_obj.get("last_name"))
    
    hh = [
        x
        for x in _client_obj.get("other_identifications")
        if x.get("identification_type") == "Household ID"
    ]
    if not hh:
        return {}
    return {**member_eligibility(household_id=hh[0], employment_type=employment_type), "full_name":full_name}


def member_eligibility(household_id=None, employment_type=""):
    from erpnext.accounts.utils import get_balance_on
    # Fetch member eligibility by household ID
    policy_period = 364
    if employment_type == "Employed":
        policy_period = 29
    invoices = frappe.db.get_all(
        "Sales Invoice",
        filters=dict(
            customer_group=household_id.get("identification_number"), docstatus=["NOT IN", ["0", "2"]]
            
        ),
        order_by ="due_date DESC",
        fields=["name as reference", "grand_total as amount_due" , "MONTHNAME(due_date) as month", "YEAR(due_date) as year",  "customer_group as household_id", "customer as member_id","status"],
        # page_length =
    )
    
        
    if not invoices:
        if employment_type =="Employed":
            return dict(eligible=0,reason="Employer by-product for this member not found.",possible_solution="Employer to submit by-product for Eligibility processing")
        return dict(eligible=0,reason="SHA Premium Assessment records for this member not found", possible_solution="Member to complete profile and SHA assessment forms on Afyayangu.go.ke")
    
    customers = [x.get("name") for x in frappe.db.get_all("Customer", filters=dict(customer_group=household_id.get("identification_number")))]
    
    hh_balance = 0.00
    for customer in customers:
        _bal = get_balance_on(party=customer, party_type="Customer")
        hh_balance += _bal
        # print(customer, _bal)
    eligible = 0
    if hh_balance <= 0 : eligible =1
    # eligible_to = ""
    _payload = dict(unpaid=hh_balance, eligible=eligible, statement=invoices)
    if eligible:
        valid_customers = [x.get("member_id") for x in invoices]
        filter_args = dict(party=["IN",valid_customers])
        latest_payment = frappe.db.get_value("Payment Entry", filter_args,["posting_date as policy_start"], as_dict=1)
        # year_later = datetime.t
        _p_start = latest_payment.get("policy_start")
        _p_end = _p_start + timedelta(days=policy_period) #Will be replaced with relativeTimeDelta
        latest_payment["policy_start"] = str(_p_start)
        
        _payload ={**_payload, **latest_payment, "policy_end":str(_p_end)}
    return _payload
    
    
