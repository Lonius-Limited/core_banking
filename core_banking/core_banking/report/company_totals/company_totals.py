# Copyright (c) 2022, Lonius Limited and contributors
# For license information, please see license.txt

# import frappe


import frappe
from frappe.core.page.background_jobs.background_jobs import get_info
from frappe.utils.background_jobs import enqueue

columns = [{
	"fieldname": "salary_component",
	"label": "Salary Component",
	"fieldtype": "Link",
	"options": "Salary Component",
	"width": 500
}, {
	"fieldname": "component_type",
	"label": "Component Type",
	"fetch_from": "salary_component.type",
	"fieldtype": "Data",
	"width": 150
}, {
	"fieldname": "total",
	"label": "Totals",
	"fieldtype": "Currency",
	"width": 300
}]

def get_earnings(summation, component_types):
	data = []
	for key in summation:
		if component_types.get(key) == 'Earning' and key not in ['Taxable Income','NSSF Relief','Pension Relief', 'Pension Company - Earning', 'NSSF Company - Earning', 'UTILITY BENEFITS COMPEARN']:
			if str(frappe.get_value("Salary Component",component_types.get(key),'is_relief'))=='1': continue
			new_dict = {
				'salary_component': key,
				'total': summation.get(key),
				'component_type': component_types.get(key)
			}
			data.append(new_dict)
	return data

def get_non_cash_benefits(summation):
	data = []
	for key in summation:
		component = frappe.get_doc('Salary Component', key)
		# is_relief = component.get('is_relief') == 1
		# do_not_include_in_total = component.get('do_not_include_in_total')
		component_type = component.get('type')
		condition =  key in ['UTILITY BENEFITS COMPEARN', 'Pension Company - Earning', 'NSSF Company - Earning']
		if condition:
			new_dict = {
				'salary_component': key,
				'total': summation.get(key),
				'component_type': component_type
			}
			data.append(new_dict)
	return data

def get_relief(summation):
	# frappe.msgprint(f"{summation}")
	components = summation.keys()
	data = []	
	def _append_to_list(key, amount, component_type):
		if frappe.get_value('Salary Component',key,'type')!='Earning': return
		data.append(dict(salary_component=key,total=amount,component_type = component_type))
		return data
	filtered = list(filter(lambda x: str(frappe.db.get_value('Salary Component', x,'is_relief'))=='1',summation))
	list(map(lambda x: _append_to_list(x,summation.get(x),frappe.get_value('Salary Component', x,'type')),filtered))
	
	# for key in summation:
	# 	component = frappe.get_doc('Salary Component', key)
	# 	is_relief = component.get("is_relief")
	# 	component_type = component.get('type')
	# 	condition =  is_relief
	# 	if condition:
	# 		new_dict = {
	# 			'salary_component': key,
	# 			'total': summation.get(key),
	# 			'component_type': component_type
	# 		}
	# 		data.append(new_dict)
	return data

def get_net_pay(summation):
	data = []
	for key in summation:
		if key == 'Net Pay':
			new_dict = {
				'salary_component': key,
				'total': summation.get(key),
				'component_type': 'Earning'
			}
			data.append(new_dict)
	return data

def get_deductions(summation, component_types):
	data = []
	for key in summation:
		component = frappe.get_doc('Salary Component', key)
		# is_relief = component.get('is_relief')
		excluded_components = ['Gross PAYE', 'Personal Relief', 'Insurance Relief']
		if component.get('type') == 'Deduction' and key not in excluded_components:
			new_dict = {
				'salary_component': key,
				'total': summation.get(key),
				'component_type': component_types[key]
			}
			data.append(new_dict)
	return data

def sort_func(dictionary):
	return dictionary['salary_component']

def get_data_func(filters=None):
	component_types = {}
	summation = {}
	
	salary_slips = frappe.get_all('Salary Slip', filters={'payroll_entry': filters.get('payroll_entry')}, fields=['*'])
	for slip in salary_slips:
		salary_details = frappe.get_all('Salary Detail', filters={
			'parent': slip.get('name')}, fields=['*'])
		
		for detail in salary_details:
			component_name = detail.get('salary_component')
			detail_amount = detail.get('amount')
			if not component_types.get(component_name):
				salary_component = frappe.get_doc(
					'Salary Component', component_name)
				component_type = salary_component.get('type')
				component_types[component_name] = component_type
			existing_ammount = summation.get(component_name) or 0
			summation[component_name] = existing_ammount + detail_amount
	data = []
	
	if filters.get('report_type').strip() == 'Taxable Earnings':
		data = get_earnings(summation=summation, component_types=component_types)
	elif filters.get('report_type').strip() == 'Non Cash Benefits':
		data = get_non_cash_benefits(summation=summation)
	elif filters.get('report_type').strip() == 'Relief':
		data = get_relief(summation)
	elif filters.get('report_type').strip() == 'Net Pay':
		data = get_net_pay(summation)
	else:
		data = get_deductions(summation, component_types=component_types)
	data.sort(key=sort_func)
	return data

def execute(filters=None):
	return columns, get_data_func(filters=filters)


def generate_html(data):
	output = '<table style="width: 100%; border-collapse: collapse;" border="1"><thead><tr>'
	component = columns[0].get('label')
	amount = 'Amount'
	output += f'<th style="width: 100%; padding: 4px">{component}<th><th style="width: 200px; text-align: center;">{amount}</th></tr><thead><tbody>'
	
	for row in data:
		component = row.get('salary_component')
		_type = row.get('component_type')
		amount = row.get('total')
		output += f'<tr><td style="width: 100%; padding: 4px; text-transform: uppercase">{component}<td/><td style="width: 200px; text-align: right;">{frappe.utils.fmt_money(amount,currency="")}</td></tr>'

	values = [x.get('total') for x in data]
	totals = sum(values)
	output += f'<tr><td style="width: 100%; padding: 4px; font-weight: bold;">Total<td/><th style="width: 200px; text-align: right; font-weight: bold;">{frappe.utils.fmt_money(totals)}</th></tr>'
	output += '<tbody></table>'
	return output

# def background_job(payroll_entry):
#     # return '>>>>>>>>>>'
#     def queued_job():
#         earnings = get_data_func(filters={'payroll_entry': payroll_entry, 'report_type': 'Taxable Earnings' })
#         # return earnings
#         # return frappe.msgprint(str(earnings))
#         deductions = get_data_func({'payroll_entry': payroll_entry, 'report_type': 'Deductions' })
#         non_cash_benefits = get_data_func({'payroll_entry': payroll_entry, 'report_type': 'Non Cash Benefits' })
#         relief = get_data_func({'payroll_entry': payroll_entry, 'report_type': 'Relief' })
#         taxable_earnings = generate_html(earnings)
#         non_cash_benefits_html = generate_html(non_cash_benefits)
#         relief_html = generate_html(relief)
#         doctype =  frappe.get_doc('Payroll Entry', payroll_entry)
#         doctype.taxable_earning = taxable_earnings
#         doctype.non_cash_benefits = non_cash_benefits_html
#         doctype.less_relief = relief_html
#         doctype.deductions = generate_html(deductions)
#         doctype.save()
#         return { 'taxable_earning': taxable_earnings, 'non_cash_benefits': non_cash_benefits_html, 'less_relief': relief_html,'deductions': generate_html(deductions) }
#     return queued_job
	
# @frappe.whitelist()
# def update_reports(payroll_entry):
#     enqueued_jobs = [d.get("job_name") for d in get_info()]
#     # frappe.msgprint(str(enqueued_jobs))
#     # frappe.msgprint(str('Job Queued'))
#     # deductions = get_data_func({'payroll_entry': payroll_entry, 'report_type': 'Taxable Earnings' })
#     if payroll_entry not in enqueued_jobs:
#         enqueue(
# 				background_job(payroll_entry),
# 				queue="default",
# 				timeout=6000,
# 				event="generate_payroll_report",
# 				job_name=payroll_entry,
# 				# data_import=self.name,
# 				now=frappe.conf.developer_mode or frappe.flags.in_test,
# 			)
#     return {}

def get_net_pay_totals(entry):
	salary_slips = frappe.get_all('Salary Slip', filters={'payroll_entry': entry }, fields=['*'])
	output = {
		'salary_component': 'Net Pay',
		'component_type': 'Earning',
		'total': 0.0
	}
	for slip in salary_slips:
		# doc = frappe.get_doc('Salary Slip', slip.get('name'))
		net_pay = slip.get("net_amount") #(slip.get('total_taxable_earnings') + slip.get('total_non_taxable_earnings') + slip.get('total_non_cash_benefits'))-slip.get('total_deduction')
		output['total'] += net_pay
	frappe.msgprint(f"{output}")
	return [output]

# @frappe.read_only()
def get_run_reports(payroll_entry):
	
	from frappe.desk.query_report import run
	report_name = "Company Totals"
	filters = {
		'payroll_entry': payroll_entry,
		'report_type': 'Relief'
	}
	relief = run(report_name, filters, user="Administrator").get('result')[:-1]
	taxable = run(report_name, {**filters, 'report_type': 'Taxable Earnings'}, user="Administrator").get('result')[:-1]
	# print(taxable, '===========>', relief)
	non_cash = run(report_name, {**filters, 'report_type': 'Non Cash Benefits'}, user="Administrator").get('result')[:-1]
	deductions = run(report_name, {**filters, 'report_type': 'Deductions'}, user="Administrator").get('result')[:-1]
	return dict(relief=relief, taxable=taxable, non_cash=non_cash, deductions=deductions)

@frappe.write_only()
def write_to_db(sql):
	frappe.db.sql(sql)
	frappe.db.commit()
	
@frappe.whitelist()
def get_reports(payroll_entry):
	net_pay = get_net_pay_totals(payroll_entry)
	#core_banking.core_banking.report.company_totals.company_totals.get_reports
	args = get_run_reports(payroll_entry)
	taxable = args.get('taxable')
	non_cash = args.get('non_cash')
	relief = args.get('relief')
	
	doctype =  frappe.get_doc('Payroll Entry', payroll_entry)
	taxable_earnings = generate_html(taxable)
	non_cash_benefits = generate_html(non_cash)
	less_relief = generate_html(relief)
	deductions = args.get('deductions')
	deductions =  generate_html(deductions)
	net_pay = generate_html(net_pay)
	sql = f"UPDATE `tabPayroll Entry` set taxable_earnings='{taxable_earnings}',  non_cash_benefits='{non_cash_benefits}', less_relief='{less_relief}', deductions='{deductions}', net_pay='{net_pay}' where name='{payroll_entry}'"
	# frappe.db.set_value('Payroll Entry',doctype.name, {
	#     'taxable_earnings': generate_html(taxable),
	#     'non_cash_benefits': generate_html(non_cash),
	#     'less_relief': generate_html(relief),
	#     'deductions': generate_html(deductions),
	#     'net_pay': generate_html(net_pay)
	# })
	
	print(sql)
	write_to_db(sql)
	return args
@frappe.whitelist()
def payroll_gl_accrual(payroll_entry):
	net_pay = get_net_pay_totals(payroll_entry)
	args = get_run_reports(payroll_entry)
	deductions = args.get('deductions')
	return args
def generate():
	sql = f"SELECT DISTINCT `payroll_entry` from `tabSalary Slip` where docstatus=0"
	unsubmitted_slips = frappe.db.sql(sql, as_dict=True)
	# print(unsubmitted_slips)
	# get_reports('May 2022 - MTRH Security Services Payroll')
	for item in unsubmitted_slips:
		payroll = item.get('payroll_entry')
		get_reports(payroll)
	
@frappe.whitelist()
def generate_2():
	get_reports("March 2022 Payroll")

