import frappe, json, os
from pathlib import Path
import pandas as pd
import numpy as np
from datetime import date

# TBC


def search_nhif_record(**kwargs):
    payload = kwargs
    if isinstance(payload, str):
        payload = json.loads(payload)
    payload.pop("cmd", None)
    # dict(id_number ="2345", phone_number="072828828")
    rec = frappe.db.get_value("NHIF Prepaid Client Record", payload)
    return rec or ""



def enqueue_nhif_data_import():
    offset = 0
    limit = 13000
    site_name = frappe.local.site  # Automatically fetches the current site name
    # file_name = "paid_up_employed_members_truncated_csv.csv"  # Change this to your file name
    file_name = "nhif_migr_test_2.csv"
    file_path = frappe.utils.get_site_path("public", "files", file_name)
    
    
    try:
        # Open the file
        df = pd.read_csv(file_path)
        # return df.to_json()
        for i in range(931):
            start=offset
            end = offset + limit
            queue_args = dict(_dataframe=df[start:end])
            frappe.enqueue(
                "core_banking.utils.nhif_employees_migration.upload_nhif_with_os", # python function or a module path as string
                queue="default" , # one of short, default, long
                timeout=None, # pass timeout manually
                is_async= 1, # if this is True, method is run in worker
                now = 0 , # if this is True, method is run directly (not in a worker) 
                job_name=None, # specify a job name
                enqueue_after_commit=False, # enqueue the job after the database commit is done at the end of the request
                at_front=False, # put the job at the front of the queue
                **queue_args, # kwargs are passed to the method as arguments
            )
            offset += limit
    except Exception as e:
        print(f"Error opening file: {e}")
def upload_nhif_with_os(**kwargs):#0-13000
        df = kwargs.get("_dataframe")
        # df = df.drop(["Unnamed: 0"], axis=1)
        df = df.replace(np.nan, None)
        count = 0
        # return str(df.columns)
        for idx, row in df.iterrows():
            try:
                count += 1
                # print(row.get("PHONE_NUMBER"))
                # continue
                # if search_nhif_record(id_number=row.get("ID_NUMBER")):
                #     continue
                # if count > 15: break
                if not (row.get("ID No") or row.get("Full Name")):
                    continue
                # print(row.get("ID_NUMBER"), row.get("IPRS_DOB"), row.get("PHONE_NUMBER"))
                insert_args = {
                    "doctype": "NHIF Prepaid Client Record",  # Replace with your actual DocType name
                    "id_no": row.get("ID No"),
                    "nhif_no": row.get("NHIF No"),
                    "full_name": row.get("Full Name", None),
                    "total_amount": row.get("Total Amount", None),
                    "no_of_months": row.get("No of Months", None),
                }
                doc = frappe.get_doc(insert_args)
                doc.db_insert()
                frappe.db.commit()
            except Exception as e:
                continue
