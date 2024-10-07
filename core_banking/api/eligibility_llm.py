import frappe
from datetime import datetime, timedelta
from dateutil import parser

class UHCEligibilityStatement:
    def __init__(self, **kwargs) -> None:
        _doc = frappe.get_doc("Core Banking Settings")
        self.insurance_transition_date = _doc.get("nhif_transition_date")
        self.eligibibility_check_input = kwargs
        self.process_nhif_eligibility =_doc.get("process_nhif_eligibility")

    def nhif_eligibility(self):
        if not self.process_nhif_eligibility: return {}
        in_transition_record = frappe.db.get_value(
            "NHIF Prepaid Client Record",
            dict(id_no=self.eligibibility_check_input.get("identification_number")),
        )
        if not in_transition_record:
            return dict(eligible_nhif=0, transition_status="{} Not in NHIF transition records".format(self.eligibibility_check_input.get("identification_number")))

        _nhif_record = frappe.get_doc(
            "NHIF Prepaid Client Record", in_transition_record
        )

        months_valid = float(_nhif_record.get("no_of_months") or 1.0 ) or 1.0

        _days = int(months_valid * 30) - 1

        valid_until = parser.parse(str(self.insurance_transition_date), fuzzy=True) + timedelta(days=_days)

        eligible_nhif = 0
        if datetime.now() <= valid_until:
            eligible_nhif =1
        return dict(
            eligible_nhif = eligible_nhif,
            months_valid=months_valid,
            transition_date=str(self.insurance_transition_date),
            valid_until = str(valid_until),
            nhif_no=_nhif_record.get("nhif_no"),
            total_amount =_nhif_record.get("total_amount") or 0.0
        )
