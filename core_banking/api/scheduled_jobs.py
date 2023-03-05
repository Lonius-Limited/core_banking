import frappe, datetime

def execute():
	# INSERT SCHEDULED JOB FOR REQUESTING REQUIRED DRUGS
	the_job = 'payroll_entry.submit_approved_slips'
	if not frappe.get_value("Scheduled Job Type",the_job):
		doc = frappe.get_doc({
			"name": the_job,
			"owner": "Administrator",
			"creation": datetime.datetime.now(),
			"docstatus": 0,
			"stopped": 0,
			"method": "core_banking.api.payroll_entry.submit_approved_slips",
			"frequency": "Cron",
			"cron_format": "*/5 * * * *",
			"create_log": 1,
			"doctype": "Scheduled Job Type",
		})
		doc.insert()