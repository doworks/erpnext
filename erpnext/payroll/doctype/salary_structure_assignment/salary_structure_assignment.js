// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/*
frappe.ui.form.on('Salary Structure Assignment', {
	onload: function(frm) {
		frm.set_query("employee", function() {
			return {
				query: "erpnext.controllers.queries.employee_query",
			}
		});
		frm.set_query("salary_structure", function() {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					is_active: "Yes"
				}
			}
		});

		frm.set_query("income_tax_slab", function() {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					disabled: 0,
					currency: frm.doc.currency
				}
			};
		});

		frm.set_query("payroll_payable_account", function() {
			var company_currency = erpnext.get_currency(frm.doc.company);
			return {
				filters: {
					"company": frm.doc.company,
					"root_type": "Liability",
					"is_group": 0,
					"account_currency": ["in", [frm.doc.currency, company_currency]],
				}
			}
		});

		frm.set_query("salary_component", "earnings", function() {
			return {
				filters: {
					type: "earning"
				}
			}
		});
		frm.set_query("salary_component", "deductions", function() {
			return {
				filters: {
					type: "deduction"
				}
			}
		});
		frm.set_query("payment_account", function () {
			var account_types = ["Bank", "Cash"];
			return {
				filters: {
					"account_type": ["in", account_types],
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		});
	},

	refresh: function(frm) {
		frm.fields_dict['earnings'].grid.set_column_disp("default_amount", false);
		frm.fields_dict['deductions'].grid.set_column_disp("default_amount", false);

		let fields_read_only = ["is_tax_applicable", "is_flexible_benefit", "variable_based_on_taxable_salary"];
		fields_read_only.forEach(function(field) {
			frappe.meta.get_docfield("Salary Detail", field, frm.doc.name).read_only = 1;
		});
	},

	employee: function(frm) {
		if(frm.doc.employee){
			frappe.call({
				method: "frappe.client.get_value",
				args:{
					doctype: "Employee",
					fieldname: "company",
					filters:{
						name: frm.doc.employee
					}
				},
				callback: function(data) {
					if(data.message){
						frm.set_value("company", data.message.company);
					}
				}
			});
		}
		else{
			frm.set_value("company", null);
		}
	},

	company: function(frm) {
		if (frm.doc.company) {
			frappe.db.get_value("Company", frm.doc.company, "default_payroll_payable_account", (r) => {
				frm.set_value("payroll_payable_account", r.default_payroll_payable_account);
			});
		}
	},

	salary_structure: function(frm) {
		frm.call({
			doc: frm.doc,
			method: "get_salary_structure_details",
			callback: function(r) {}
		});
	},
	base: function(frm) {
        if(frm.doc.salary_structure){
            calculate_totals(frm);
        } else {
            frappe.msgprint("Please set Salary Structure First!");
        }
	}
});

frappe.ui.form.on('Salary Detail', {
	amount: function(frm) {
		calculate_totals(frm);
	},

	formula: function(frm) {
		calculate_totals(frm);
	},

	condition: function(frm) {
		calculate_totals(frm);
	},

	earnings_remove: function(frm) {
		calculate_totals(frm);
	},

	deductions_remove: function(frm) {
		calculate_totals(frm);
	},

	statistical_component: function(frm) {
		calculate_totals(frm);
	},

	do_not_include_in_total: function(frm) {
		calculate_totals(frm);
	},

	salary_component: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if(child.salary_component){
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Salary Component",
					name: child.salary_component
				},
				callback: function(data) {
					if(data.message){
						var result = data.message;
						frappe.model.set_value(cdt, cdn, 'condition', result.condition);
						frappe.model.set_value(cdt, cdn, 'amount_based_on_formula', result.amount_based_on_formula);
						if(result.amount_based_on_formula == 1){
							frappe.model.set_value(cdt, cdn, 'formula', result.formula);
						}
						else{
							frappe.model.set_value(cdt, cdn, 'amount', result.amount);
						}
						frappe.model.set_value(cdt, cdn, 'statistical_component', result.statistical_component);
						frappe.model.set_value(cdt, cdn, 'depends_on_payment_days', result.depends_on_payment_days);
						frappe.model.set_value(cdt, cdn, 'do_not_include_in_total', result.do_not_include_in_total);
						frappe.model.set_value(cdt, cdn, 'variable_based_on_taxable_salary', result.variable_based_on_taxable_salary);
						frappe.model.set_value(cdt, cdn, 'is_tax_applicable', result.is_tax_applicable);
						frappe.model.set_value(cdt, cdn, 'is_flexible_benefit', result.is_flexible_benefit);
						refresh_field("earnings");
						refresh_field("deductions");
					}
				}
			});
		}
	}
})

var calculate_totals = function (frm) {
	frm.call({
        method: 'calculate_totals',
        doc: frm.doc,
        callback: function(r) {}
    });
}
*/

frappe.ui.form.on('Salary Structure Assignment', {
	onload: function(frm) {
		frm.set_query("employee", function() {
			return {
				query: "erpnext.controllers.queries.employee_query",
				filters: {
					company: frm.doc.company
				}
			}
		});
		frm.set_query("salary_structure", function() {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					is_active: "Yes"
				}
			}
		});

		frm.set_query("income_tax_slab", function() {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					disabled: 0
				}
			}
		});

		frm.set_query("salary_component", "earnings", function() {
			return {
				filters: {
					type: "earning"
				}
			}
		});
		frm.set_query("salary_component", "deductions", function() {
			return {
				filters: {
					type: "deduction"
				}
			}
		});
		frm.set_query("payment_account", function () {
			var account_types = ["Bank", "Cash"];
			return {
				filters: {
					"account_type": ["in", account_types],
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		});
	},

	setup: function(frm) {
		frm.get_field("earnings").grid.cannot_add_rows = true;
		frm.get_field("earnings").grid.only_sortable();

		frm.get_field("deductions").grid.cannot_add_rows = true;
        frm.get_field("deductions").grid.only_sortable();
	},
	
	refresh: function(frm) {
		frm.fields_dict['earnings'].grid.set_column_disp("default_amount", false);
		frm.fields_dict['deductions'].grid.set_column_disp("default_amount", false);

		let fields_read_only = ["is_tax_applicable", "is_flexible_benefit", "variable_based_on_taxable_salary", "formula"];
		fields_read_only.forEach(function(field) {
			frappe.meta.get_docfield("Salary Detail", field, frm.doc.name).read_only = 1;
		});

		//Custom Script
		frappe.meta.get_docfield("Salary Detail","salary_component", cur_frm.doc.name).read_only = 1;
        frappe.meta.get_docfield("Salary Detail","statistical_component", cur_frm.doc.name).read_only = 1;
        frappe.meta.get_docfield("Salary Detail","do_not_include_in_total", cur_frm.doc.name).read_only = 1;
        frappe.meta.get_docfield("Salary Detail","condition", cur_frm.doc.name).depends_on = '';
        frappe.meta.get_docfield("Salary Detail","condition", cur_frm.doc.name).hidden = 0;
        frappe.meta.get_docfield("Salary Detail","condition", cur_frm.doc.name).read_only = 1;
        frappe.meta.get_docfield("Salary Detail","amount_based_on_formula", cur_frm.doc.name).depends_on = '';
        frappe.meta.get_docfield("Salary Detail","amount_based_on_formula", cur_frm.doc.name).hidden = 0;
        frappe.meta.get_docfield("Salary Detail","amount_based_on_formula", cur_frm.doc.name).read_only = 1;
	},
	
	salary_structure: function(frm) {
		if(frm.doc.salary_structure) {
			get_salary_structure_details(frm);
		}
	},
	base: function(frm) {
        if(frm.doc.salary_structure){
            get_salary_structure_details(frm);
        } else {
            frappe.msgprint("Please set Salary Structure First!");
        }
	}
});

frappe.ui.form.on('Salary Detail', {
	amount: function(frm) {
		calculate_totals(frm);
	}
});

function get_salary_structure_details(frm) {
    frappe.call({
		method: 'erpnext.payroll.doctype.salary_structure_assignment.salary_structure_assignment.get_salary_structure_details',
		freeze: true,
		freeze_message: "Getting Salary Structure",
        args: {
            'salary_structure': frm.doc.salary_structure
        },
        callback: function(r) {
            var result = r.message;

            frm.set_value('earnings', []);
            frm.set_value('deductions', []);

            var columns = [
                "salary_component", 
                "abbr", 
                "statistical_component", 
                "is_tax_applicable", 
                "is_flexible_benefit", 
                "variable_based_on_taxable_salary", 
                "depends_on_payment_days", 
                "deduct_full_tax_on_selected_payroll_date", 
                "condition", 
                "amount_based_on_formula", 
                "formula", 
                "amount", 
                "do_not_include_in_total", 
                "default_amount", 
                "additional_amount", 
                "tax_on_flexible_benefit", 
                "tax_on_additional_salary"
            ];

            Object.keys(result).forEach(function (key) {
                if(result[key]) {
                    for(var i=0; i<result[key].length; i++){
                        var row = frappe.model.add_child(frm.doc, "Salary Detail", key);
                        Object.keys(result[key][i]).forEach(function (k) {
                            if(columns.includes(k)) {
                                row[k] = result[key][i][k];
                            }
                        });
                    }
                }                            
            });

            calculate_totals(frm);
        }
    });
}
var calculate_totals = function (frm) {
	var me = this;
	frm.call({
        method: 'calculate_totals',
		doc: frm.doc,
		freeze: true,
		freeze_message: "Calculating Salary",
        callback: function(r) {
			me.frm.refresh_fields();
		}
    });
}
/*function calculate_salary(frm) {
	frappe.call({
        method: 'taha.api.calculate_salary',
        args: {
            'ssa_doc': frm.doc
        },
        callback: function(r) {
            var result = r.message;

            //frm.set_value('earnings', []);
            //frm.set_value('deductions', []);

            var columns = [
                "salary_component", 
                "abbr", 
                "statistical_component", 
                "is_tax_applicable", 
                "is_flexible_benefit", 
                "variable_based_on_taxable_salary", 
                "depends_on_payment_days", 
                "deduct_full_tax_on_selected_payroll_date", 
                "condition", 
                "amount_based_on_formula", 
                "formula", 
                "amount", 
                "do_not_include_in_total", 
                "default_amount", 
                "additional_amount", 
                "tax_on_flexible_benefit", 
                "tax_on_additional_salary"
            ];

            Object.keys(result).forEach(function (key) {
                if(key == 'earnings' || key == 'deductions') {
                    for(var i=0; i<result[key].length; i++){
                        //var row = frappe.model.add_child(frm.doc, "Salary Detail", "earnings");
                        for(var x=0; x<frm.doc[key].length; x++){
                            if(frm.doc[key][x]['salary_component'] == result[key][i]['salary_component']){
                                var child = locals[frm.doc[key][x]['doctype']][frm.doc[key][x]['name']];
                                child.amount = result[key][i]['amount'];
                            }
                        }
                    }
                }                            
            });

            frm.set_value('total_earning', result['total_earning']);
            frm.set_value('total_deduction', result['total_deduction']);
            frm.set_value('salary_total', result['salary_total']);

            cur_frm.refresh_fields()
        }
    });
}*/
// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/*
frappe.ui.form.on('Salary Structure Assignment', {
	onload: function(frm) {
		frm.set_query("employee", function() {
			return {
				query: "erpnext.controllers.queries.employee_query",
				filters: {
					company: frm.doc.company
				}
			}
		});
		frm.set_query("salary_structure", function() {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					is_active: "Yes"
				}
			}
		});

		frm.set_query("income_tax_slab", function() {
			return {
				filters: {
					company: frm.doc.company,
					docstatus: 1,
					disabled: 0
				}
			}
		});

		frm.set_query("salary_component", "earnings", function() {
			return {
				filters: {
					type: "earning"
				}
			}
		});
		frm.set_query("salary_component", "deductions", function() {
			return {
				filters: {
					type: "deduction"
				}
			}
		});
		frm.set_query("payment_account", function () {
			var account_types = ["Bank", "Cash"];
			return {
				filters: {
					"account_type": ["in", account_types],
					"is_group": 0,
					"company": frm.doc.company
				}
			};
		});
	},

	refresh: function(frm) {
		frm.fields_dict['earnings'].grid.set_column_disp("default_amount", false);
		frm.fields_dict['deductions'].grid.set_column_disp("default_amount", false);

		let fields_read_only = ["is_tax_applicable", "is_flexible_benefit", "variable_based_on_taxable_salary"];
		fields_read_only.forEach(function(field) {
			frappe.meta.get_docfield("Salary Detail", field, frm.doc.name).read_only = 1;
		});
	},
	employee: function(frm) {
		if(frm.doc.employee){
			frappe.call({
				method: "frappe.client.get_value",
				args:{
					doctype: "Employee",
					fieldname: "company",
					filters:{
						name: frm.doc.employee
					}
				},
				callback: function(data) {
					if(data.message){
						frm.set_value("company", data.message.company);
					}
				}
			});
		}
		else{
			frm.set_value("company", null);
		}
	},
	salary_structure: function(frm) {
		if(frm.doc.salary_structure){
			frm.call({
				doc: frm.doc,
				freeze: true,
				freeze_message: "Getting Salary Structure",
				method: "get_salary_structure_details",
				callback: function(r) {}
			});
		}
	},
	base: function(frm) {
        if(frm.doc.salary_structure){
            calculate_totals(frm);
        } else {
            frappe.msgprint("Please set Salary Structure First!");
        }
	}
});

frappe.ui.form.on('Salary Detail', {
	amount_based_on_formula: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if(child.amount_based_on_formula == 1){
			frappe.model.set_value(cdt, cdn, 'amount', null);
		}
		else{
			frappe.model.set_value(cdt, cdn, 'formula', null);
		}
	},

	amount: function(frm) {
		calculate_totals(frm);
	},

	formula: function(frm) {
		calculate_totals(frm);
	},

	condition: function(frm) {
		calculate_totals(frm);
	},

	earnings_remove: function(frm) {
		calculate_totals(frm);
	},

	deductions_remove: function(frm) {
		calculate_totals(frm);
	},

	statistical_component: function(frm) {
		calculate_totals(frm);
	},

	do_not_include_in_total: function(frm) {
		calculate_totals(frm);
	},

	salary_component: function(frm, cdt, cdn) {
		var child = locals[cdt][cdn];
		if(child.salary_component){
			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: "Salary Component",
					name: child.salary_component
				},
				callback: function(data) {
					if(data.message){
						var result = data.message;
						frappe.model.set_value(cdt, cdn, 'condition', result.condition);
						frappe.model.set_value(cdt, cdn, 'amount_based_on_formula', result.amount_based_on_formula);
						if(result.amount_based_on_formula == 1){
							frappe.model.set_value(cdt, cdn, 'formula', result.formula);
						}
						else{
							frappe.model.set_value(cdt, cdn, 'amount', result.amount);
						}
						frappe.model.set_value(cdt, cdn, 'statistical_component', result.statistical_component);
						frappe.model.set_value(cdt, cdn, 'depends_on_payment_days', result.depends_on_payment_days);
						frappe.model.set_value(cdt, cdn, 'do_not_include_in_total', result.do_not_include_in_total);
						frappe.model.set_value(cdt, cdn, 'variable_based_on_taxable_salary', result.variable_based_on_taxable_salary);
						frappe.model.set_value(cdt, cdn, 'is_tax_applicable', result.is_tax_applicable);
						frappe.model.set_value(cdt, cdn, 'is_flexible_benefit', result.is_flexible_benefit);
						refresh_field("earnings");
						refresh_field("deductions");
					}
				}
			});
		}
	}
})

var calculate_totals = function (frm) {
	frm.call({
        method: 'calculate_totals',
		doc: frm.doc,
		freeze: true,
		freeze_message: "Calculating Salary",
        callback: function(r) {
			frm.refresh_fields();
		}
    });
}
}*/
