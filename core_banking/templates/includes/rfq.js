// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

window.doc={{ doc.as_json() }};

$(document).ready(function() {
	new rfq();
	doc.supplier = "{{ doc.supplier }}"
	doc.currency = "{{ doc.currency }}"
	doc.number_format = "{{ doc.number_format }}"
	doc.buying_price_list = "{{ doc.buying_price_list }}"

	doc.base_grand_total = 0.0
	doc.grand_total = 0.0
	doc.rounded_total = 0.0
	doc.in_words = ""
	doc.total = 0.0
	doc.base_total = 0.0
	doc.net_total = 0.0

	$.each(doc.items, function(idx, data){
		data.rate = 0.0;
		data.amount = 0.0;
	})
});

rfq = Class.extend({
	init: function(){
		this.onfocus_select_all();
		this.change_qty();
		this.change_rate();
		this.terms();
		this.submit_rfq();
		this.navigate_quotations();
		this.change_attachments();
	},

	onfocus_select_all: function(){
		$("input").click(function(){
			$(this).select();
		})
	},
	
	change_attachments: function(){
		var me = this;
		$('.rfq-items').on("change", ".rfq-attachments", function(){
			me.attachments = $(this).val();
			console.log("ATTACHED: " + me.attachments);
			
			$.each(doc.items, function(idx, data){
				if(data.idx == me.idx){
					data.attachments = me.attachments;
				}
			})
		})
	},

	change_qty: function(){
		var me = this;
		$('.rfq-items').on("change", ".rfq-qty", function(){
			me.idx = parseFloat($(this).attr('data-idx').replace(/,/g,''));
			me.qty = parseFloat($(this).val().replace(/,/g,'')) || 0;
			me.rate = parseFloat($(repl('.rfq-rate[data-idx=%(idx)s]',{'idx': me.idx})).val().replace(/,/g,''));
			me.update_qty_rate();
			$(this).val(format_number(me.qty, doc.number_format, 2));
			me.attachments = $(this).data("attachments");
		})
	},

	change_rate: function(){
		var me = this;
		$(".rfq-items").on("keyup", ".rfq-rate", function(){ 
			me.idx = parseFloat($(this).attr('data-idx').replace(/,/g,''));			
			me.rate = parseFloat($(this).val().replace(/,/g,'')) || 0;
			me.qty = parseFloat($(repl('.rfq-qty[data-idx=%(idx)s]',{'idx': me.idx})).val().replace(/,/g,''));
			//alert(me.qty)			
			me.update_qty_rate();
			//$(this).val(format_number(me.rate, doc.number_format, 2));
		})
		$(".rfq-items").on("change", ".rfq-rate", function(){
			me.update_qty_rate();
			$(this).val(format_number(me.rate, doc.number_format, 2));
		})
	},

	terms: function(){
		$(".terms").on("change", ".terms-feedback", function(){
			doc.terms = $(this).val();
		})
	},

	update_qty_rate: function(){
		var me = this;
		doc.grand_total = 0.0;
		$.each(doc.items, function(idx, data){
			if(data.idx == me.idx){
				console.log("Attachement: " + me.attachments);
				data.qty = me.qty;
				data.rate = me.rate;
				data.amount = (me.rate * me.qty) || 0.0;
				$(repl('.rfq-amount[data-idx=%(idx)s]',{'idx': me.idx})).text(format_number(data.amount, doc.number_format, 2));
				//data.attachments = me.attachments;
			}

			doc.grand_total += flt(data.amount);
			$('.tax-grand-total').text(format_number(doc.grand_total, doc.number_format, 2));
		})
	},

	submit_rfq: function(){
		$('.btn-sm').click(function(){
			//JSON.stringify(doc)
			var isconfirmed = confirm("Any previously submitted quotation for the associated RFQ [" + doc.name + "] will be overwritten and this will be regarded as the updated quotation. Are you sure?");
			if(isconfirmed){
				frappe.freeze();
				frappe.call({
					type: "POST",
					method: "mtrh_dev.mtrh_dev.utilities.create_supplier_quotation",
					args: {
						doc: doc
					},
					btn: this,
					callback: function(r){
						frappe.unfreeze();
						if(r.message){
							$('.btn-sm').hide()
							setTimeout(function(){
								window.location.href = "/supplier-quotations/" + encodeURIComponent(r.message);
								window.location.replace("/supplier-quotations/" + encodeURIComponent(r.message));
							}, 5000)
							frappe.msgprint({
								title: __('Successfully Submitted'),
								message:__("Your submission of Quotation: <b>" + r.message + "</b> was successful. You will be alerted once it is opened and evaluated"),
								indicator:'green'
							});
						}
					}
				})
			}
		})
	},

	navigate_quotations: function() {
		$('.quotations').click(function(){
			name = $(this).attr('idx')
			window.location.href = "/quotations/" + encodeURIComponent(name);
		})
	}
})
