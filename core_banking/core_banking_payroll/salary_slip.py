import frappe

def computations(doc):
    the_context = doc.earnings

    amount = [x.get('amount') for x in the_context] or [0.00]

    consolidated = 0.0
    nonpayrollbenefits = 0.0
    # frappe.msgprint(f"{amount}")
    for r in the_context:
        component = r.salary_component
        if component == 'Taxable Income': continue
        is_relief = int(frappe.db.get_value('Salary Component', component, 'is_relief') or '0')
        if not is_relief:
            consolidated = consolidated + r.amount
        else:
            nonpayrollbenefits = nonpayrollbenefits + r.amount
        #------------------------------------------------
    total_deductions = 0.00
    deduction_context = doc.deductions
    for r in deduction_context:
        component = r.salary_component
        if component =='Taxable Income' or component =='Gross PAYE' or ('Relief' in component ) or ('Income Tax' in component): continue
        total_deductions = total_deductions + r.amount
    return consolidated, nonpayrollbenefits,total_deductions

def salary_slip_save(doc, state):
    # frappe.msgprint("Computing consolidated pay for: "+doc.name)
    
    consolidated, nonpayrollbenefits,total_deductions = computations(doc)
    
    doc.set('total_consolidated_pay', consolidated)
    doc.set('non_payroll_benefits', nonpayrollbenefits)

    #--------------------------------------------------------------------------------
   
    doc.set('total_deductions',total_deductions)
    net_pay = consolidated - total_deductions or 0.0
    doc.set('net_amount',net_pay)
    frappe.msgprint(f"{net_pay}", title="Summary")

    
