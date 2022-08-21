frappe.ui.form.on('Payment Entry', {
    refresh(frm){
        frm.dashboard.add_section(dash(frm));
        frm.dashboard.show()
    },
   
})

const dash =(frm)=>{
    const accountsPayable = frm.doc.paid_to;
    const cashBankAccount = frm.doc.paid_from;
    accountDetails = `<h5 style="margin-top: 0px;color:green">Accounts Affected:</h5><p>Bank/Cash: ${cashBankAccount}</p><p>Liability/Payable Account: ${accountsPayable}</p>`
    return `<h5 style="margin-top: 0px;color:green"> ${ __("Payment Narration:") }</a></h5>${frm.doc.remarks}${accountDetails}`;
}