// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('VAT Return Settings', {
	onload: function (frm) {

		frm.set_query('debtors_accounts', function (doc) {
			return {
				filters: {
					"account_type": ["in", ["Receivable", "Payable"]]
				}
			};
		});

		frm.set_query('export_accounts', function (doc) {
			return {
				filters: {
					"account_type": "Receivable"
				}
			};
		});

		frm.set_query('creditors_accounts', function (doc) {
			return {
				filters: {
					"account_type": ["in", ["Receivable", "Payable"]]
				}
			};
		});

		frm.set_query('import_accounts', function (doc) {
			return {
				filters: {
					"account_type": "Tax"
				}
			};
		});
	},
	// refresh: function(frm) {

	// }
	/*income_parent_account: function (frm) {
		if (frm.doc.income_parent_account) {
			frm.set_query('income_accounts', function (doc) {
				return {
					filters: {
						root_type: "Income",
						name: ['not in', [frm.doc.income_parent_account]]
					}
				};
			});
			
			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Account",
					order_by: "name",
					fields: ["name"],
					filters: [
						["Account", "root_type", "=", "Income"],
						["Account", "name", "!=", frm.doc.income_parent_account]
					]
				},
				callback: function (r) {
					var data = r.message;
					var accounts = [];
					for (var i = 0; i < data.length; i++) {
						accounts.push({
							account: data[i].name,
							docstatus: frm.doc.docstatus,
							doctype: "Account Item",
							idx: (i+1),
							name: frm.doc.name,
							owner: frm.doc.owner,
							parent: "VAT Return Settings",
							parentfield: "income_accounts",
							parenttype: "VAT Return Settings",
							__islocal: frm.doc.__islocal,
							__unsaved: frm.doc.__unsaved
						});
					}

					frm.set_value('income_accounts', accounts);
				}
			});
		}
	},
	expense_parent_account: function (frm) {
		if (frm.doc.expense_parent_account) {
			frm.set_query('expense_accounts', function (doc) {
				return {
					filters: {
						root_type: "Expense",
						name: ['not in', [frm.doc.expense_parent_account]]
					}
				};
			});

			frappe.call({
				method: "frappe.client.get_list",
				args: {
					doctype: "Account",
					order_by: "name",
					fields: ["name"],
					filters: [
						["Account", "root_type", "=", "Expense"],
						["Account", "name", "!=", frm.doc.expense_parent_account]
					]
				},
				callback: function (r) {
					var data = r.message;
					var accounts = [];
					for (var i = 0; i < data.length; i++) {
						accounts.push({
							account: data[i].name,
							docstatus: frm.doc.docstatus,
							doctype: "Account Item",
							idx: (i+1),
							name: frm.doc.name,
							owner: frm.doc.owner,
							parent: "VAT Return Settings",
							parentfield: "expense_accounts",
							parenttype: "VAT Return Settings",
							__islocal: frm.doc.__islocal,
							__unsaved: frm.doc.__unsaved
						});
					}

					frm.set_value('expense_accounts', accounts);
				}
			});
		}
	}*/
});
