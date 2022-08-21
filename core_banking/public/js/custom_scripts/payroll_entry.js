// 172.23.95.166
frappe.ui.form.on('Payroll Entry', {
    onload(frm){
        const buttons = ["Make Bank Entry", "Submit Salary Slip"]
        buttons.forEach(button => frm.remove_custom_button(button));
    },
    onload_post_render(frm) {
        const buttons = ["Make Bank Entry", "Submit Salary Slip"]
        buttons.forEach(button => frm.remove_custom_button(button));
        frm.clear_custom_buttons()
        frm.add_custom_button(__("Run Company Totals"), function () {
            frappe.call({
                method: "core_banking.core_banking.report.company_totals.company_totals.get_reports",
                freeze: true,
                freeze_message: "Please wait as we run totals",
                async: false,
                args: {
                    payroll_entry: frm.doc.name
                }
            }).then(r => frm.reload_doc())

        });
        frm.trigger('post_payroll_accrual_transaction')

    },
    clear_dash(frm) {
        const buttons = ["Make Bank Entry", "Submit Salary Slip"]
        buttons.forEach(button => frm.remove_custom_button(button));
    },
    post_payroll_accrual_transaction(frm) {
        const submitted = frm.doc.salary_slips_submitted.toString();
        const docstatus = frm.doc.docstatus.toString();
        const journal_details = frm.doc.journal_details
        if (submitted === '0' && docstatus == '1') {
            // frm.add_custom_button(__("Close Payroll -"), function () {
            //     closePayroll(frm).then(
            //         console.log('Closed')
            //         //postAccrual(frm)
            //     )
            // });
           
        }
        if(!journal_details && submitted){
            // frm.add_custom_button(__("Post accounting entries"), function () {
            //     postAccrual(frm)
            // });
        }
    },
    refresh(frm) {
        //Refresh functions only
        const buttons = ["Make Bank Entry", "Submit Salary Slip"]
        buttons.forEach(button => frm.remove_custom_button(button));

        if(frm.doc.journal_details){
            frm.dashboard.add_section(`<h5 style="margin-top: 0px;"> ${ __("Payroll Journal") }</a></h5>${frm.doc.journal_details}`);
        }
    }
})
const closePayroll = async (frm) => {
    const payrollEntry = frm.doc.name;
    const closeArgs = {
        method: "core_banking.api.payroll_entry.close_payroll",
        args: {
            payroll_entry: payrollEntry
        },
        freeze: true,
        freeze_message: "Please wait as we submit payslips."
    }

    frappe.call(closeArgs).then(console.log('Slips submitted'))

}

const postAccrual = (frm) => {
  
    const payrollEntry = frm.doc.name;
    const postArgs = {
        method: "core_banking.api.payroll_entry.post_payroll_journal",
        args: {
            payroll_entry: payrollEntry
        },
        freeze: true,
        freeze_message: "Please wait as we post gl entries."
    }
    console.log(postArgs)
    frappe.call(postArgs).then(console.log('Entries posted'))

}