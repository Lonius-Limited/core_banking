frappe.pages['purchase-request'].on_page_load = function (wrapper) {

	// loadPage(wrapper)
	new NewPage(wrapper)

}
class NewPage {
	constructor(wrapper) {
		this.page = frappe.ui.make_app_page({
			parent: wrapper,
			title: 'Purchase Request List',
			single_column: true
		});
		this.page.set_indicator('Active Requests', 'green')

		let $btn = this.page.set_primary_action(' + New Purchase Request', () => create_new(), 'octicon octicon-plus')
		let $btn2 = this.page.set_secondary_action('Refresh', () => this.refresh(), 'octicon octicon-sync')
		this.refresh()
	}
	make() { }
	async fetchRequests() {
		const res = await fetch('https://dummyjson.com/products');
		const json = await res.json();

		return json
	}
	refresh() {
		const title = `<div class="form-message blue"><div>This is a list of material requests</div></div><br>`
		fetchPurchaseRequests().then(fetchedRequests => {
			console.log(fetchedRequests)
			const itemsGrid = this.itemsTable(fetchedRequests)
			const template = `${title} ${itemsGrid}`
			this.$container = $('.page-body').empty().append(
				$(frappe.render_template(template, this.page)).appendTo(this.page.main)
			)
		})
	}

	itemsTable(fetchedRequests) {
		// const rq = fetchedRequests.products
		const rq = fetchedRequests
		const randomIDs = Array.from({ length: 20 }, () => Math.floor(Math.random() * 20));
		let context = rq
		const header = `<div class="list-row-container" tabindex="1">
		<table class="table table-striped custom-table">
			<thead><tr>
				<th scope="col">#</th>
				<th scope="col">Document ID</th>
				<th scope="col">Status</th>
				<th scope="col">Show Items</th>
				<th scope="col">Actions</th>
				</tr>
			</thead>
			<tbody>`
		const footer = `</tbody>
						</table>
					</div>`
		const body = context.map(row => {
			const workflowState = row.workflow_state
			return `
			<tr>
			  <th scope="row">${row.title}</th>
			  <td>${row.name}</td>
			  <td>${workflowState}</td>
			  <td><button class="btn btn-secondary">${workflowState == "Approved" ? "View" : "Edit"}</button></td> 
			  <td>${this.dropdown(row.name)}</td>  
			</tr>
		  
		  `

		})
		console.log(body)
		return `${header} ${body.join("")} ${footer}`
	}
	dropdown(id) {
		let actions =[];
		const doc = {
			doctype :"Material Request",
			name : id
		}
		const transitionArgs = {
			method:"frappe.model.workflow.get_transitions",
			args:{
				doc: doc
			},
			async:false,
		}
		frappe.call(transitionArgs).then(r=>{
			let transitions = r.message || []
			
			actions = transitions.map(transition=>{
				return `<a class="dropdown-item">${transition.action}</a>`
			})
			
		})
		return `<div class="dropdown">
		<button class="btn btn-secondary dropdown-toggle" type="button" id="dropdownMenuButton" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false">
		  Select Action
		</button>
		<div class="dropdown-menu" aria-labelledby="dropdownMenuButton">
		  ${actions.join("")}
		</div>
	  </div>`
	}
	actions(id) {

	}
	documentAction(document, action) {
		console.log(document, action)
	}
}

const fetchPurchaseRequests = async () => {
	let mRequests = []
	const mRequestArgs = {
		method: "core_banking.api.purchasing.material_requests",
		async: false,
		freeze: true,
		freeze_message: "Please wait as we fetch material requests"
	}
	frappe.call(mRequestArgs).then(r => {
		mRequests = r.message || []

	})
	return mRequests;
}