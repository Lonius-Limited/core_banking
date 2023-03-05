// Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
// License: GNU General Public License v3. See license.txt

window.doc={{ doc.as_json() }};

$(document).ready(function() {
	new order();
	console.log("Purchase order {{doc.name}} ")
	window.doc_info = {
		//customer: '{{doc.customer}}',
		doctype: '{{ doc.doctype }}',
		doctype_name: '{{ doc.name }}',
		grand_total: '{{ doc.grand_total }}',
		currency: '{{ doc.currency }}'
	}
});

order = Class.extend({
	init: function(){
		this.onfocus_select_all();
		this.change_qty();
		this.load_qty_balance();
		this.change_rate();
		this.change_quantity_amount();
		this.terms();
		this.generatedeliverynote();
		this.generatepurchaseinvoice();
		this.navigate_quotations();
		this.change_attachments();
		this.Check_Balance_Remaining();
		this.change_attachments_two();
		
	},

	onfocus_select_all: function(){
		$("input").click(function(){
			$(this).select();
		})
	},

	load_qty_balance: function(){
		var me = this
		//me.qty="450"
		$(this).val(format_number(me.qty, doc.number_format, 2));
		//alert(me.qty)
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
	change_attachments_two: function(){
		var me = this;
		
		$('.order-items').on("change", ".invoice-attachments", function(){
			me.attachments = $(this).val();
			console.log("The documents atteched are: " + me.attachments);
			
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
			me.idx = parseFloat($(this).attr('data-idx'));
			me.qty = parseFloat($(this).val()) || 0;
			me.rate = parseFloat($(repl('.rfq-rate[data-idx=%(idx)s]',{'idx': me.idx})).val());
			me.update_qty_rate();
			$(this).val(format_number(me.qty, doc.number_format, 2));
			me.attachments = $(this).data("attachments");
		})
	},
	
	change_rate: function(){
		var me = this;
		$(".rfq-items").on("change", ".rfq-rate", function(){
			me.idx = parseFloat($(this).attr('data-idx'));
			me.rate = parseFloat($(this).val()) || 0;
			me.qty = parseFloat($(repl('.rfq-qty[data-idx=%(idx)s]',{'idx': me.idx})).val());
			me.update_qty_rate();
			$(this).val(format_number(me.rate, doc.number_format, 2));
		})
	},
	change_quantity_amount: function(){
		var me = this;		
		$(".order-items").on("change", ".order-supply", function(){			
			me.idx = parseFloat($(this).attr('data-idx'));	
			//alert(me.idx)		
			me.tosupply = parseFloat($(this).val()) || 0;
			//alert("3: " + me.tosupply);
			me.itemcode = parseFloat($(repl('.order-it[data-idx=%(idx)s]',{'idx': me.idx})).val());
			me.qty = parseFloat($(repl('.order-qty[data-idx=%(idx)s]',{'idx': me.idx})).val());
			me.rate = parseFloat($(repl('.orderrate[data-idx=%(idx)s]',{'idx': me.idx})).val());
			
			//me.dnote = parseFloat($(repl('.order-dnote[data-idx=%(idx)s]',{'idx': me.idx})).val());
			//me.rate = parseFloat($(this).val()) || 0;			
			//me.rate = "55"
			//parseFloat($(repl('.orderrate[data-idx=%(idx)s]',{'idx': me.idx})).val())		
			//alert(me.itemcode)
			//me.qty = parseFloat($(repl('.order-qty[data-idx=%(idx)s]',{'idx': me.idx})).val());	
			//alert(me.rate)
			me.Check_Balance_Remaining();					
			me.update_supply_amount();
			//$(this).val(format_number(me.rate, doc.number_format, 2));
		})
	
	},
/*
	dnote_check: function(){
		var me = this;		
		$(".order-items").on("change", ".order-dnote", function(){			
			me.idx = parseFloat($(this).attr('data-idx'));			
			me.dnote = parseFloat($(repl('.order-dnote[data-idx=%(idx)s]',{'idx': me.idx})).val());
			//me.rate = parseFloat($(this).val()) || 0;			
			//me.rate = "55"
			//parseFloat($(repl('.orderrate[data-idx=%(idx)s]',{'idx': me.idx})).val())		
			//alert(me.dnote)
			//me.qty = parseFloat($(repl('.order-qty[data-idx=%(idx)s]',{'idx': me.idx})).val());	
			//alert(me.rate)
								
			me.update_supply_amount();
			//$(this).val(format_number(me.rate, doc.number_format, 2));
		})
	
	},
	*/

	terms: function(){
		$(".terms").on("change", ".terms-feedback", function(){
			doc.terms = $(this).val();
		})
	},

	update_supply_amount: function(){
		var me = this;
		doc.grand_total = 0.0;
		 		
		$.each(doc.items, function(idx, data){
			if(data.idx == me.idx){				
				data.qty = me.qty;
				data.tosupply=me.tosupply;
				//alert("2: " + data.tosupply);
				data.rate = me.rate;
				//data.dnote= me.dnote;
				//alert(data.rate)
				data.amount = (me.rate * me.tosupply) || 0.0;
				//alert(data.amount )
				$(repl('.order-amount[data-idx=%(idx)s]',{'idx': me.idx})).text(format_number(data.amount, doc.number_format, 2));
				//data.attachments = me.attachments;
						}
			doc.grand_total += flt(data.amount);
			$('.tax-grand-total').text(format_number(doc.grand_total, doc.number_format, 2));
			
		})
	},


	
	update_qty_rate: function(){
		var me = this;
		doc.grand_total = 0.0;
		$.each(doc.items, function(idx, data){
			if(data.idx == me.idx){				
				data.qty = me.qty;
				data.tosupply=me.tosupply;
				data.rate = me.rate;				
				//alert("1: " + data.tosupply);
				data.amount = (me.rate * me.tosupply) || 0.0;
				//alert(data.amount)
				$(repl('.order-amount[data-idx=%(idx)s]',{'idx': me.idx})).text(format_number(data.amount, doc.number_format, 2));
				//data.attachments = me.attachments;
						}

			doc.grand_total += flt(data.amount);
			$('.tax-grand-total').text(format_number(doc.grand_total, doc.number_format, 2));
			
		})
	},

	generatedeliverynote: function(){
		
		$('.btn-gen').click(function(){	
					
			var isconfirmed = confirm("Ensure you have entered all field required Are you sure?");
			var deliverynumber =document.getElementById("deliverynumber").value;
			if(deliverynumber.length==0)
			{
				frappe.throw("Delivery Number Field Empty!!")
			}
			
			
			if(isconfirmed){
				//frappe.freeze();
				frappe.call({
					type: "POST",
					method: "mtrh_dev.mtrh_dev.tqe_evaluation.Generate_Purchase_Receipt_Draft",
					args: {						
						doc:doc,
						deliverynumber:deliverynumber	
					},
					btn: this,
					callback: function(r){
						//alert("Submitted Successfully");
						//location.reload(true);
						//frappe.unfreeze();
						//if(r.message){
							//$('.btn-sm').hide()
						//	window.location.href = "/deliverynumber/"// + encodeURIComponent(r.message);
							//window.location.replace("/Supplier-Delivery-Note/Supplier-Delivery-Note/"// + encodeURIComponent(r.message));
							//frappe.show_alert("Your submission has been successfull", 10)
						//}
					}
				})
			}
		})
	},

	//






	///

	generatepurchaseinvoice: function(){
		
		$('.btn-invoice').click(function(){					
			var isconfirmed = confirm("Are you sure you want to generate purchase invoice?");								
			if(isconfirmed){
				//frappe.freeze();
				frappe.call({
					type: "POST",
					method: "mtrh_dev.mtrh_dev.tqe_evaluation.make_purchase_invoice_from_portal",
					args: {						
						purchase_order_name:doc.name,
						doc:doc
											
					},
					btn: this,
					callback: function(r){
						//alert(r.totalqty);
						//location.reload(true);
						//frappe.unfreeze();
						//if(r.message){
							//$('.btn-sm').hide()
							//window.location.href = "/purchase-invoices/"+ encodeURIComponent(doc.name);
							//window.location.replace("/Supplier-Delivery-Note/Supplier-Delivery-Note/"// + encodeURIComponent(r.message));
							//frappe.show_alert("Your submission has been successfull", 10)
						//}
						
					}
				})
			}
		})
	},

	Check_Balance_Remaining: function(){	
		var me=this;
		var itemcode =document.getElementById("itemcode").value;
		//alert(itemcode)
/*
		$.each(doc.items, function(idx, data){
			if(data.idx == me.idx){				
				data.qty = me.qty;
				data.itemcode = me.itemcode
				//alert(data.itemcode)
		*/		
				frappe.call({
					type: "POST",
					method: "mtrh_dev.mtrh_dev.tqe_evaluation.getquantitybalance",
					args: {						
						purchase_order_name:doc.name,
						itemcode:itemcode

					},
					callback: function(r){	
						console.log(r.message)
						//alert(r.message)
						if(r.message<=0)
						{
							//frappe.throw("You have submitted more than required")

						}
						//$(repl('.order-qty[data-idx=%(idx)s]',{'idx': me.idx})).text(r.message);
						//$('.order-qty').text(r.message);				
						
					}
				})
			//}
		//})
			//}
		//})
	},

	navigate_quotations: function() {
		$('.quotations').click(function(){
			name = $(this).attr('idx')
			window.location.href = "/quotations/" + encodeURIComponent(name);
		})
	}
})
