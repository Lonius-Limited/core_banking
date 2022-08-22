frappe.ui.form.on('Payment Entry', {
    refresh(frm) {
        frm.dashboard.add_section(dash(frm));
        frm.dashboard.show()
        if (frm.doc.payroll_entry) {
            if (frm.doc.payroll_summary) {
                console.log("No need for the query")
                frm.dashboard.add_section(frm.doc.payroll_summary);
                frm.dashboard.show()
            } else {
                fetchAccountPayrollComponents(frm).then(r => {
                    console.log(r)
                })
            }
        }
    },

})

const dash = (frm) => {
    const accountsPayable = frm.doc.paid_to;
    const cashBankAccount = frm.doc.paid_from;
    accountDetails = `<h5 style="margin-top: 0px;color:green">Accounts Affected:</h5><p>Bank/Cash: ${cashBankAccount}</p><p>Liability/Payable Account: ${accountsPayable}</p>`
    return `<h5 style="margin-top: 0px;color:green"> ${__("Payment Narration:")}</a></h5>${frm.doc.remarks}${accountDetails}`;
}

const fetchAccountPayrollComponents = async (frm) => {
    let account = frm.doc.paid_to
    let payroll_entry = frm.doc.payroll_entry
    let payment_entry = frm.doc.name
    const accountArgs = {
        account,
        payroll_entry,
        payment_entry
    }
    frappe.call({
        method: "core_banking.api.payroll_entry.account_components_in_payroll_entry",
        args: accountArgs,
        async: true,
    }).then(r => {

        const employees = r.message;
        console.log(employees)
        const heading = '<table class="table table-striped"><tr><td>Employee ID</td><td>Employee Name</td><td>Paid To</td><td>Amount</td></tr>'
        let total = 0.00
        const bodyTRList = employees.map(employee => {
            if (employee.amount) {
                total += parseFloat(employee.amount)
                return `<tr><td>${employee.employee}</td><td>${employee.employee_name}</td><td>${employee.salary_component}</td><td>${frm.doc.paid_to_account_currency} ${formatted(parseFloat(employee.amount))}</td></tr>`
            }
        })
        console.log(bodyTRList)
        const footer = `<tr><td colspan=3><b>Total</b></td> <td style='color:green'>${frm.doc.paid_to_account_currency} ${formatted(parseFloat(total))}</td></table>`

        frm.set_value('payroll_summary', `Summary: ${heading} ${bodyTRList.join("")} ${footer}`)
            .then(() => {
                if (frm.doc.docstatus == 1) {
                    frm.save('Update')
                } else {
                    frm.save()
                }
            })

        // frm.dashboard.add_section(`Summary: ${heading} ${bodyTRList.join("")} ${footer}`);
        // frm.dashboard.show()
        return r.message
    })
}
const formatted = (amount) => { return amount.toFixed(2).replace(/\d(?=(\d{3})+\.)/g, '$&,') }

