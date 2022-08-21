from braintree import Customer
import frappe
from frappe import _
from frappe.core.doctype.data_import.importer import Importer, ImportFile
from frappe.utils.xlsxutils import read_xlsx_file_from_attached_file
import math
from frappe.utils import add_to_date, getdate,get_link_to_form, getdate, nowdate
from csv import DictReader
import re
from datetime import datetime, date,timedelta
from frappe.desk.query_report import run

def make_member_customer(doc, state):
	if not doc.create_customer_account: return
	doc.make_customer_and_link()
def validate_percentages(doc,state):
	if doc.get('beneficiaries'):
		percent = sum([x.get('percentage_distribution') for x in doc.get('beneficiaries')])
		if percent > 100: frappe.throw('Total Percentage exceeds 100%')
		if percent < 100: frappe.throw('Total Percentage must add up to 100%')
@frappe.whitelist()
def get_member_net_contribution(member):
	customer = frappe.db.get_value('Member',member,'customer')
	sql = """SELECT DISTINCT sum(amount) AS contribution FROM `tabSales Invoice Item` WHERE parent IN (SELECT name FROM `tabSales Invoice` WHERE customer ='{}' AND docstatus=1);""".format(customer)

	transfers_out = frappe.db.get_all("Payment Entry",filters=dict(docstatus=1,party_type='Member', party=member,payment_type='Pay'), fields=['paid_amount']) or [dict(paid_amount=0.0)]

	amount_contr = frappe.db.sql(sql, as_dict=1) or [dict(contribution=0.0)]

	balance = (amount_contr[0].get("contribution") or 0.0 ) - (transfers_out[0].get("paid_amount"))

	return balance
@frappe.whitelist()
def get_member_contributions(member):
	member_doc = frappe.get_doc('Member', member)
	customer = member_doc.customer
	sql = """SELECT DISTINCT item_code AS item_name, sum(amount) AS contribution FROM `tabSales Invoice Item` WHERE parent IN (SELECT name FROM `tabSales Invoice` WHERE customer ='{}' AND docstatus=1) GROUP BY item_code;""".format(customer)
	contributions = frappe.db.sql(sql, as_dict=1)
	contributions = [x for x in contributions if x.get('item_name')]
	text ="<h4>Pension Contributions for <b style='color:green'>{}</b> </h4>".format(member_doc.get('member_name'))
	if not contributions:
		text += '<p>No records were found.</p>'
		return text
	
	text += "<div class='row'>"
	total = 0.00
	for contribution in contributions:
		total += float(contribution.get('contribution'))
		# if not contribution.get('item_name'): continue
		amount,contribution_type = contribution.get('contribution'), contribution.get('item_name')
		text += """<div class="card" style="width: 14rem;">
				<div class="card-body">
					<h5 class="card-title">{}</h5>
					<p class="card-text" style='color:blue' >{}</p>
					
				</div>
			</div>
			&nbsp""".format(contribution_type,frappe.format(amount, dict(fieldtype='Currency')))
	text += "</div>"
	#<a href="#" class="btn btn-primary"></a>
	text += "<br><br><h4>Total contribution: <em style='color:red'>{}</em></h4>".format(frappe.format(total,dict(fieldtype='Currency')))
	out = 0.00
	transfers_out = frappe.db.get_all("Payment Entry",filters=dict(docstatus=1,party_type='Member', party=member,payment_type='Pay'), fields=['paid_amount'])

	if transfers_out: out = sum([x.get('paid_amount') for x in transfers_out])

	balance= float(total) - float(out)

	text += "<br><br><h4>Transfers Out: <em style='color:blue'>{}</em></h4>".format(frappe.format(out,dict(fieldtype='Currency')))

	text += "<br><br><h4>Net Contribution: <em style='color:green'>{}</em></h4>".format(frappe.format(balance,dict(fieldtype='Currency')))
	return text, member_complete_statement_html(member)
@frappe.whitelist()
def populate_upload(doc, state):
	fileurl = doc.get('excel_upload')
	if not fileurl: frappe.throw("File URL not provided")
	# doc.set('pension_schedule',[])
	_file = frappe.get_doc("File", {"file_url": fileurl})
	filename = _file.get_full_path()
	payload = []
	with open(filename, 'r') as read_obj:
		# pass the file object to DictReader() to get the DictReader object
		dict_reader = DictReader(read_obj)
		# get a list of dictionaries from dct_reader
		list_of_dict = list(dict_reader)
		# print list of dict i.e. rows
		frappe.msgprint("Pension schedule will be validated and posted in the background on submit of this document")
@frappe.whitelist()
def get_pension_schedule(docid):
	doc = frappe.get_doc('Pension Contributions Upload', docid)
	fileurl = doc.get('excel_upload')
	if not fileurl: frappe.throw("File URL not provided")
	# doc.set('pension_schedule',[])
	_file = frappe.get_doc("File", {"file_url": fileurl})
	filename = _file.get_full_path()
	# payload = []
	with open(filename, 'r', encoding='utf-8-sig') as read_obj:
		# pass the file object to DictReader() to get the DictReader object
		dict_reader = DictReader(read_obj)
		# get a list of dictionaries from dct_reader
		list_of_dict = list(dict_reader)
		# print list of dict i.e. rows
		payload = list_of_dict
		# frappe.msgprint(f"{list_of_dict}")
		return payload
def reevaluate_doc():
	docid ='877a75414f'
	post_pension_schedule(docid)
def post_pension_schedule_hook(doc, state):
	post_pension_schedule(doc.get('name'))
def post_pension_schedule(docid):
	#member_pf_number
	schedule = get_pension_schedule(docid)
	schedule_doc = frappe.get_doc('Pension Contributions Upload',docid)
	'''
	[
		{
			"ID":"",
			"PF Number":"1",
			"Reference Document":"",
			"Employer Contribution":"100",
			"Employee Contribution":"100",
			"Additional Voluntary Contribution":"100",
			"Interest Earned":"100","Other Income":"100"
		}
	]
	'''
	for row in schedule:
		docname = frappe.get_value('Member',dict(member_pf_number=row.get('PF Number'), membership_type=schedule_doc.get('sponsor')),'name')
		if not docname: frappe.throw("Sorry, Member record for {} not found ".format(row.get('PF Number')))

		if frappe.get_value('Pension Contributions Upload Template', dict(pf_number=row.get('PF Number'), reference_document=docid),'name'): continue
		'''
		Make template document
		Check if items exist and create if not
		Create a dict of items
		Post to make_invoice_endpoint
		'''
		if 'ID' in list(row.keys()): row.pop('ID')
		to_upload ={}
		for b in list(row.keys()):
			to_upload[frappe.scrub(b)] = row.get(b)
		to_upload['reference_document'] = docid
		to_upload['doctype'] = 'Pension Contributions Upload Template'
		items = validate_items(row)
		#-----
		# if not frappe.get_value('Member',to_upload.get('pf_number')): continue
		member_doc = frappe.get_doc('Member',docname)
		customer = member_doc.get('customer')
		make_invoice_endpoint(customer=customer, items=items, posting_date=schedule_doc.get('effective_date'),narration=schedule_doc.get("remarks"),reference=docid)
		#Make Upload template
		# member_doc.make
		frappe.get_doc(to_upload).save(ignore_permissions=True)
def validate_items(row):
	items = ['Employer Contribution','Employee Contribution','Additional Voluntary Contribution','Interest Earned']
	invoice_items =[]
	# def _make_item(item_name):
	# 	args = dict(item_code=item_name, item_name=item_name,item_group='Services',stock_uom='Unit',disabled=0,is_stock_item=0, doctype='Item')
	# 	frappe.get_doc(args).insert()
	for item_name in items:
		if not frappe.get_value('Item',item_name):make_item(item_name)
		invoice_items.append(dict(item_code=item_name, qty=1, rate= row.get(item_name), amount= row.get(item_name)))
	return invoice_items
def make_invoice_endpoint(customer=None, items=[],posting_date=None, narration="No Remarks", reference=None):
	company = frappe.defaults.get_user_default("company")
	# if not invoice:
	clean = re.compile('<.*?>')
	invoice = frappe.get_doc({
		"doctype": "Sales Invoice",
		# "patient": patient,
		"status": "Draft",
		"company": company,
		'due_date': '2099-01-01',
		'posting_date': posting_date or datetime.today() ,
		"currency": "KES",
		"customer": customer,
		"remarks" : re.sub(clean, '', narration),
		"pension_upload_": reference
	})
	for item in items:
		invoice.append('items', item)
	invoice.run_method('set_missing_values')
	invoice.insert()
	invoice.submit()

	settings = frappe.get_doc("Non Profit Settings")
	make_payment_entry(reference or invoice.get('name'),settings,invoice)
	return invoice
def make_item(item_name):
	args = dict(item_code=item_name, item_name=item_name,item_group='Services',stock_uom='Unit',disabled=0,is_stock_item=0, doctype='Item')
	frappe.get_doc(args).insert()
def validate_transfers_in(doc,state):
	# transfer_in = doc.get('transfer_in')
	narration = '<p>Being posting of pension transfers for </p>'
	data =[]
	total = 0.00
	if not doc.get('transfers_in'): return
	for row in doc.get('transfers_in'):
		if row.posted: continue
		total += row.amount
		narration += "<b style='color:green'>{}</b>:  {}".format(row.get("sponsor"),frappe.format(row.get("amount"), dict(fieldtype='Currency')))
		row.posted = 1
	if total < 1.00 : return
	
	initial_transfer_in(doc.get('name'),amount=total,narration=narration)
	return
@frappe.whitelist()
def initial_transfer_in(member, amount=0.0, narration=''):
	member_doc = frappe.get_doc('Member', member)
	customer = member_doc.get('customer')
	item_name = 'Transfer In'
	if not frappe.get_value('Item',item_name): make_item(item_name)
	# already_entered = frappe.db.sql("SELECT item_name FROM `tabInvoice Item` WHERE item_code= '{}' parent IN (SELECT name FROM `tabSales Invoice` WHERE docstatus=1 and customer ='{}')".format(item, customer))
	invoice_item = [dict(item_code=item_name, qty=1, rate= amount, amount= amount)]
	inv = make_invoice_endpoint(customer=customer, items=invoice_item, narration=narration)
	inv.add_comment(text=narration)
	return inv
def set_date_of_retirement(doc,state):
	# return
	if doc.date_of_birth:
		bdate = doc.date_of_birth
		years_to_retirement = 60 
		if doc.persons_with_disability:
			years_to_retirement = 65 
		rt = add_to_date(bdate,years=years_to_retirement)
		# frappe.msgprint(rt)
		doc.date_of_retirement = rt #bdate.replace(year=bdate.year + years_to_retirement)
	return
def make_payment_entry(reference,settings, invoice):
		if not settings.membership_payment_account:
			frappe.throw(_("You need to set <b>Payment Account</b> for Membership in {0}").format(
				get_link_to_form("Non Profit Settings", "Non Profit Settings")))

		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry
		frappe.flags.ignore_account_permission = True
		pe = get_payment_entry(dt="Sales Invoice", dn=invoice.name, bank_amount=invoice.grand_total)
		frappe.flags.ignore_account_permission=False
		pe.paid_to = settings.membership_payment_account
		pe.reference_no = reference
		pe.reference_date = getdate()
		pe.flags.ignore_mandatory = True
		pe.save()
		pe.submit()
@frappe.whitelist()
def member_complete_statement_html(member):
	to_date = date.today()
	from_date=add_to_date(to_date,days=-9999)#27 years
	filters = dict(member=member,date_from=from_date, date_to=to_date)
	# frappe.msgprint("filters")
	report_name ='Member Statement'
	pl = run(report_name, filters, user="Administrator")
	res = pl.get('result')

	if not res : return "<em style='color:blue'>Sorry, no records were found</em>"
	data = [x for x in res if not isinstance(x,list)]

	header_fields = list(dict.fromkeys([x.get('contribution_type') for x in data]))

	text = "<table class='table table-responsive table-striped'><thead><tr><td><b>Posting Date</b></td> <td><b>Contribution Type</b></td> <td><b>Contribution</b></td> <td><b>Reference</b></td> <td><b>Narration</b></td></tr></thead>"

	text += "<tbody>"

	for row in data:
		text += "<tr><td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td> <td>{}</td></tr>".format(
			row.get("posting_date"),
			row.get("contribution_type"),
			frappe.format(row.get("contribution"),dict(fieldtype='Currency')),
			row.get("reference"),
			row.get("narration")
		)

	text += "</tbody><tfoot><tr><td colspan=5><h3 style='color:green'>Summary</h3></td></tr>"
	grand_total =0.0
	for ctype in header_fields:
		subtotal = sum([x.get("contribution") for x in data if x.get("contribution_type")==ctype])
		grand_total += subtotal
		formatted_s_total = frappe.format(subtotal,dict(fieldtype='Currency'))
		text += "<tr><td colspan=3><b>{}</b></td><td colspan=2>{}</td></tr>".format(ctype,formatted_s_total)
	formatted_grand_total =  frappe.format(grand_total, dict(fieldtype='Currency'))
	text += "<tr><td colspan=3><b style='color:blue'>Net Pension Amount: </b></td><td colspan=2>{}</td></tr>".format(formatted_grand_total)
	text += '</tfoot></table>'
	return text


	# for field in header_fields:
	# 	text += '<td>{}</td>'.format(field)
	# text += '</tr></thead><tbody>'
	# for row in data:
	# 	text += "<tr>"
	# 	for field in header_fields:
	# 		text += "<td>"






	

		



