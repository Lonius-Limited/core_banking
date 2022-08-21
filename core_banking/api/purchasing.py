import frappe

@frappe.whitelist()
def material_requests(page_length=0):
    requests =  frappe.get_all("Material Request", fields=["*"],order_by='creation desc',page_length=page_length or 20)
    def _update_items(doc):
        items = frappe.get_all("Material Request Item", filters=dict(parent=doc.get("name")),fields=["*"])
        doc.update(dict(items=items))

    list(map(lambda doc: _update_items(doc),requests))
    return requests