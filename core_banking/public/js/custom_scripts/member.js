
frappe.ui.form.on('Member', {
	refresh(frm){
		if(frm.doc.pension_totals){
			frm.dashboard.add_section(frm.doc.pension_totals_html);
        	frm.dashboard.show();
		}
	},
	onload(frm) {
		// your code here
		if (frm.doc.date_of_birth) {
			let age =`<p style='color:green'>${get_age(frm.doc.date_of_birth)}</p>`
			$(frm.fields_dict['age'].wrapper).html(`${__('AGE')} : ${age}`);
		} else {
			$(frm.fields_dict['age'].wrapper).html('');
		}
		
	}, 
	onload_post_render(frm){
		getMemberContributionSummary(frm)
	}
})
let get_age = function (birth) {
	let ageMS = Date.parse(Date()) - Date.parse(birth);
	let age = new Date();
	age.setTime(ageMS);
	let years = age.getFullYear() - 1970;
	return years + ' Year(s) ' + age.getMonth() + ' Month(s) ' + age.getDate() + ' Day(s)';
};
//get_member_contributions
function getMemberContributionSummary(frm){
	frappe.call({
		method:"core_banking.api.member.get_member_contributions",
		freeze: true,
		freeze_message: `Please wait as we fetch the contributions for ${frm.doc.member_name}`,
		args:{
			'member':frm.doc.name
		}
	}).then(r=>{
		console.log(r)
		frm.dirty()
		frm.doc.pension_statement = r.message[1]
		// pension_totals_html
		$(frm.fields_dict['pension_totals_html'].wrapper).html(`${ r.message[0]}`);
		frm.save()
		// frm.dashboard.add_section(r.message);
        // frm.dashboard.show();
	})
}