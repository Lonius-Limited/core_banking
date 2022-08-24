frappe.ui.form.on('Additional Salary', {
	refresh(frm) {
		if (frm.doc.docstatus ==1){
    		frm.add_custom_button(__("Stop Deduction / Earning"), function(){
                showStopDialog(frm)
            });
            frm.add_custom_button(__("Update Deduction / Earning Terms"), function(){
                 showUpdateSalaryComponentTerms(frm)
            })
	    }}
})

function showMakeAdditionalSalary(frm){
    var d = new frappe.ui.Dialog({
    'fields': [
        {'fieldname': 'ht', 'fieldtype': 'HTML'},
        {'fieldname': 'start_date', 'fieldtype': 'From Date', 'reqd':1, 'default':frm.doc.payroll_date},
        {'fieldname': 'end_date', 'fieldtype': 'End Date', 'reqd':1}
    ],
    primary_action: function(){
        let values = d.get_values()
        d.hide();
        show_alert();
    }
});
d.fields_dict.ht.$wrapper.html('Hello World');
d.show();
}

function showUpdateSalaryComponentTerms(frm){
    // if (!frm.doc.is_recurring){
    //     frappe.throw("Sorry, this transaction is applicable for recurring Additional Salary Documents")
    // }
    frappe.prompt([
        {
            //label: 'First Name',
            fieldname: 'text_html',
            fieldtype: 'HTML',
            options: `<p style='color:red'> WARNING!! You are about to UPDATE <strong>${frm.doc.salary_component} (${formattedAmount(parseFloat(frm.doc.amount))})</strong> for <strong>${frm.doc.employee_name}-${frm.doc.employee}. Please cross-check before submit to MAKE SURE of the details you provide.</strong></p>`
        },
        
        {
            label: 'Update Amount',
            fieldname: 'update_amount',
            fieldtype: 'Check',
            description: 'If ticked the monthly charges will be updated.',
            reqd: 1, 
            default : true
        },
            {
            label: 'Amount On',
            fieldname: 'amount',
            fieldtype: 'Currency',
            description: 'New Monthly Charges.',
            reqd: 1
        },
        {
            label: 'Update Balance',
            fieldname: 'update_balance',
            fieldtype: 'Check',
            description: 'If ticked the balance will be updated.',
            reqd: 1, 
            default : false
        },
         {
            label: 'Balance',
            fieldname: 'amount_payable',
            fieldtype: 'Currency',
            description: 'Account balance as at the effective date.',
            reqd: 1,
            default: frm.doc.amount_payable
             
         },
        
      {
            label: 'Attachment',
            fieldname: 'attachment_evidence',
            fieldtype: 'Attach',
            description: 'Attachment as evidence of this transaction.',
            reqd: 0
        },
         {
            label: 'Confirmation',
            fieldname: 'confirmation',
            fieldtype: 'Data',
            description: 'Please enter the Staff PF Number to Confirm transaction.',
            reqd: 1
        }
             
         
        
    ], (values) => {
    console.log(values);
    if (values.confirmation !== frm.doc.employee){
        frappe.throw("Invalid PF Number, Please enter the correct PF Number")
        
        
    }
        let payload = values;
        // if payload[]
        payload["name"] = frm.doc.name
        frappe.call({
            method: "core_banking.api.additional_salary.update_additional_salary",
            args: {
                "payload":payload
            }
        }).then(r=>{
            console.log(r)
            frm.reload_doc()
        })
    
})
}
function showStopDialog(frm){
    frappe.prompt([
        {
            //label: 'First Name',
            fieldname: 'text_html',
            fieldtype: 'HTML',
            options: `<p style='color:red'>You are about to STOP <strong>${frm.doc.salary_component} (${formattedAmount(parseFloat(frm.doc.amount))})</strong> for <strong>${frm.doc.employee_name}. Please cross-check before submit to MAKE SURE of the details you provide.</strong></p>`
        },
            {
            label: 'Stop Date',
            fieldname: 'stop_date',
            fieldtype: 'Date',
            description: 'Please set the to date this Additional Component should be stopped.',
            reqd: 1
        }
    ], (values) => {
    if (values.stop_date < frm.doc.from_date){
        // frappe.throw("To Date cannot be before From Date")
    }
    stopAdditionalSalary(frm, values.stop_date)
    console.log(values.stop_date);
})
}
function stopAdditionalSalary(frm, date){
    let dateToUpdate = date.toString()
    console.log("Converted String ", dateToUpdate)
    
    frappe.call({
        method: "core_banking.api.additional_salary.stop_additional_salary",
        args:{
            "docname": frm.doc.name,
            "stop_date": dateToUpdate
        }
    }).then(r=>{
        console.log(r)
        frm.reload_doc()
        // frm.doc.refresh()
        
    })
}
const formattedAmount = (amount) => { return amount.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,') }