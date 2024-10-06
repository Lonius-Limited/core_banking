import frappe, requests, json
from datetime import datetime, timedelta
from core_banking.api.customer import create_beneficiary
from core_banking.api.eligibility_llm import UHCEligibilityStatement
import requests


class HIE:
    def __init__(self) -> None:
        _doc = frappe.get_doc("Core Banking Settings")
        self.hie_base_url = _doc.get("hie_url")
        self.hie_user_name = _doc.get("hie_username")
        self.hie_password = _doc.get_password("hie_password")

    def fetch_cr_by_identifiers(self, **kwargs):
        payload = json.dumps(kwargs)
        response = requests.get(
            "{}/client-registry/fetch-client-basic?payload={}".format(
                self.hie_base_url, payload
            ),
            auth=(self.hie_user_name, self.hie_password),
        )
        return response.json()

    # def create_beneficiary_record(self):


class MeansTesting:
    def __init__(self, _cr_number) -> None:
        self.cr_number = _cr_number

    def fetch_member_mt(self):
        # Return the same payload
        print(self.cr_number)
        uri ="/user-means-testing-bsc"
        _hie  = HIE()
        response = requests.get(
            "{}/{}?id={}".format(
                _hie.hie_base_url, uri, self.cr_number
            ),
            auth=(_hie.hie_user_name, _hie.hie_password),
        )
        if response.status_code!= 200: return dict(means_testing_done=0)
        _obj = response.json()["message"][0]
        _obj["means_testing_done"] = 1
        return _obj



@frappe.whitelist()
def member_statement_v2(**kwargs):
    payload = kwargs
    if isinstance(payload, str):
        payload = json.loads(payload)
    payload.pop("cmd", None)


    param_values = {}
    

    cr_number = payload.pop("id", None)
    # Fetch client first locally
    customer_args = dict(name=cr_number)
    identification_type = payload.get("identification_type")
    identification_number = payload.get("identification_number")
    if identification_number:
        customer_args = dict(
            custom_identification_type=identification_type,
            custom_identification_number=identification_number,
        )
    _customer = frappe.db.get_value("Customer", customer_args)

    household_number = ""
    employment_type = ""
    # return _customer
    _client_obj = {}
    if not _customer:
        print("Did not find customer {}, going to HIE...".format(_customer))
        _res = HIE().fetch_cr_by_identifiers(**payload)
        if not _res.get("message"):
            return dict(
                eligible=0,
                reason="Client Records for requested Identifiers were not found.",
                possible_solution="Client to Register for Social Health Authority using valid identifiers",
            )
        client = _res.get("message")
        if client.get("total") < 1:
            return dict(
                eligible=0,
                reason="Client Records for requested Identifiers were not found.",
                possible_solution="Client to Register for Social Health Authority using valid identifiers",
            )
        # return client
        _client_obj = client.get("result")[0]
        employment_type = _client_obj.get("employment_type")
        full_name = "{} {}".format(
            _client_obj.get("first_name"), _client_obj.get("last_name")
        )

        hh = [
            x
            for x in _client_obj.get("other_identifications")
            if x.get("identification_type") == "Household Number"
        ]
        if not hh:
            return dict(
                eligible=0,
                reason="Client has not been assigned a valid SHA / Household Number.",
                possible_solution="Client to Register for Social Health Authority using valid identifiers or obtain support in the generation of Household Number",
            )
        household_number = hh[0]
        # "id",
        # "identification_type",
        # "identification_number",
        # "full_name",
        # "household_number",
        # "employment_type",
        param_values = dict(token_api_email="api@safaricom.co.ke",password="jPaVx9#C3]",document_type="3", document_number=_client_obj.get("id") )
        _customer = _client_obj.get("id")
        enqueue_create_beneficiary(
            **dict(
                id=_client_obj.get("id"),
                identification_number=identification_number,
                identification_type=identification_type,
                full_name=full_name,
                household_number=household_number.get("identification_number"),
                employment_type=employment_type,
            )
        )
        # create_beneficiary
    else:
        _res = HIE().fetch_cr_by_identifiers(**payload) # Just to get employer details
        client = _res.get("message")
        _client_obj = client.get("result")[0] or {}
        
        doc = frappe.get_doc("Customer", _customer)
        household_number = dict(
            identification_number=doc.get("customer_group")
        )  # Backward compatibility
        employment_type = doc.get("custom_employment_status")
        full_name = doc.get("custom_customer_full_name")
        
        param_values = dict(token_api_email="api@safaricom.co.ke",password="jPaVx9#C3]",document_type="3", document_number=_customer )
        
    _ep_response = {**thatFunction(**param_values)}
    
    print(_customer)
    r = MeansTesting(_customer)
    
    

    return {
       
        **member_eligibility(
            household_id=household_number, employment_type=employment_type
        ),
        **UHCEligibilityStatement(
            identification_number=identification_number
        ).nhif_eligibility(),
        **_ep_response,
        "means_testing_details": r.fetch_member_mt(),
         "full_name": full_name,
        "client_portal_details": {
            "employment_type": _client_obj.get("employment_type") or "Unspecified",
            "employer_name" : _client_obj.get("employer_name"),
        }
        
    }


def member_eligibility(household_id=None, employment_type=""):
    from erpnext.accounts.utils import get_balance_on

    # Declaration on EP

    # Fetch member eligibility by Household Number
    policy_period = 364
    if employment_type == "Employed":
        policy_period = 29
    invoices = frappe.db.get_all(
        "Sales Invoice",
        filters=dict(
            customer_group=household_id.get("identification_number"),
            docstatus=["NOT IN", ["0", "2"]],
        ),
        order_by="due_date DESC",
        fields=[
            "name as reference",
            "grand_total as amount_due",
            "MONTHNAME(due_date) as month",
            "YEAR(due_date) as year",
            "customer_group as household_id",
            "customer as member_id",
            "status",
        ],
        # page_length =
    )

    if not invoices:
        if employment_type == "Employed":
            return dict(
                eligible=0,
                reason="Employer by-product for this member not found.",
                possible_solution="Employer to submit by-product for Eligibility processing",
            )
        return dict(
            eligible=0,
            reason="SHA Premium Assessment records for this member not found",
            possible_solution="Member to complete profile and SHA assessment forms on Afyayangu.go.ke",
        )

    customers = [
        x.get("name")
        for x in frappe.db.get_all(
            "Customer",
            filters=dict(customer_group=household_id.get("identification_number")),
        )
    ]

    hh_balance = 0.00
    for customer in customers:
        _bal = get_balance_on(party=customer, party_type="Customer")
        hh_balance += _bal
        # print(customer, _bal)
    eligible = 0
    if hh_balance <= 0:
        eligible = 1
    # eligible_to = ""
    _payload = dict(unpaid=hh_balance, eligible=eligible, statement=invoices)
    if eligible:
        valid_customers = [x.get("member_id") for x in invoices]
        filter_args = dict(party=["IN", valid_customers])
        latest_payment = frappe.db.get_value(
            "Payment Entry", filter_args, ["posting_date as policy_start"], as_dict=1
        )
        # year_later = datetime.t
        _p_start = latest_payment.get("policy_start")
        _p_end = _p_start + timedelta(
            days=policy_period
        )  # Will be replaced with relativeTimeDelta
        latest_payment["policy_start"] = str(_p_start)

        _payload = {**_payload, **latest_payment, "policy_end": str(_p_end)}
    return _payload


def enqueue_create_beneficiary(**kwargs):
    queue_args = kwargs
    print("Enqueueing with {}".format(queue_args))
    frappe.enqueue(
        "core_banking.api.customer.create_beneficiary",  # python function or a module path as string
        queue="default",  # one of short, default, long
        timeout=None,  # pass timeout manually
        is_async=1,  # if this is True, method is run in worker
        now=0,  # if this is True, method is run directly (not in a worker)
        job_name=None,  # specify a job name
        enqueue_after_commit=False,  # enqueue the job after the database commit is done at the end of the request
        at_front=False,  # put the job at the front of the queue
        **queue_args,  # kwargs are passed to the method as arguments
    )


def thatFunction(**kwargs):
    # Get token
    print(kwargs)
    token_url = "https://prd-ms-sha-payments.sha.go.ke/backend/api/v1/auth/apiUser"
    token_payload = {
        "email": kwargs.get("token_api_email"),
        "password": kwargs.get("password"),
    }

    try:
        token_response = requests.post(token_url, json=token_payload)

        if token_response.status_code != 200:
            return {"error": "Failed to obtain access token {}".format(token_response.__dict__)}

        access_token = token_response.json().get("accessToken")

        # Use token to check eligibility
        validate_url = (
            "https://prd-ms-sha-payments.sha.go.ke/backend/api/v1/coverage/validate"
        )
        validate_payload = {
            "documentType": kwargs.get("document_type"),
            "documentNumber": kwargs.get("document_number"),
        }
        headers = {"Authorization": f"Bearer {access_token}"}

        validate_response = requests.post(
            validate_url, json=validate_payload, headers=headers
        )

        _ep_response = validate_response.json()

        if validate_response.status_code == 400:
            return dict(eligible_employee=0, ep_code=400)

        if "isEmployed" in list(_ep_response.keys()):
            return dict(eligible_employee=1, policy_end_employer=_ep_response.get("NhifPrepaidEnd"), ep_code=validate_response.status_code)
        if "error" in list(_ep_response.keys()):
            return dict(eligible_employee=0, ep_code=validate_response.status_code)
    except Exception as e:
        return dict(eligible_employee=0, ep_code=validate_response.status_code, reason="Error connecting to Employer portal")