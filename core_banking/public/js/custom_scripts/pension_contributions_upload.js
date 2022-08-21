// Copyright (c) 2022, mtrh_devs@gmail.com and contributors
// For license information, please see license.txt

frappe.ui.form.on('Pension Contributions Upload', {
	refresh: function (frm) {
		frm.set_df_property("excel_upload", "read_only", frm.doc.status=="Initiated" || frm.is_new() ? 0 : 1);
		frm.set_df_property("sponsor", "read_only", frm.is_new() ? 0 : 1);
		frm.set_df_property("document_reference", "read_only", frm.is_new() ? 0 : 1);

		if (frm.doc.status == "Initiated") {
			frm.add_custom_button(__("Validate and Process Document"), function () {
				processDocument(frm)
			})
		}
	},
	download_template(frm) {
		frappe.require('/assets/js/data_import_tools.min.js', () => {
			frm.data_exporter = new frappe.data_import.DataExporter(
				"Pension Contributions Upload Template",
				"Insert New Records",
				// "5 Records"
			);
		});
	},
});
function processDocument(frm) {
	frappe.prompt([
		{ 'fieldtype': 'HTML', 'fieldname': 'info', 'options': `<h4>Please be careful when selecting a salary component as this action is IRREVERSIBLE</h4><p><strong>Remarks Provided</strong> ${frm.doc.remarks}</p>` },
		{ 'fieldname': 'salary_component', 'options': 'Salary Component', 'fieldtype': 'Link', 'label': 'Salary Component', 'reqd': 1 },

	],
		function (values) {
			console.log(values);
			frm.call({
				'method': 'validate_and_process',
				args: {
					docname: frm.doc.name,
					salary_component: values.salary_component
				}
			}).then(res => {
				console.log(res)
				frm.reload_doc()
			})
		},
		'Salary Component Selection',
		'Validate and Incorpotate Into Payroll'
	)
}
