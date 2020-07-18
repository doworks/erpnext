// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shift Assignment Tool', {
	refresh: function (frm) {
		frm.disable_save();
		frm.page.set_primary_action(__('Assign Shifts'), () => {
			if (!frm.doc.employees) {
				frappe.throw("Select employee/s");
			}
			let btn_primary = frm.page.btn_primary.get(0);

			if (!cur_frm.doc.shift_pattern) {
				frappe.throw("Please select <b>Shift Pattern</b>");
			} else if (!cur_frm.doc.from_date) {
				frappe.throw("Please set <b>From Date</b>");
			} else if (!cur_frm.doc.to_date) {
				frappe.throw("Please set <b>To Date</b>");
			} else if (cur_frm.doc.from_date > cur_frm.doc.to_date) {
				frappe.throw("<b>To Date</b> Can't be less than <b>From Date</b>");
			} else {
				cur_frm.call({
					doc: cur_frm.doc,
					method: 'generate_shift_pattern_view',
					callback: function (r, rt) {
						return frm.call({
							doc: frm.doc,
							freeze: true,
							btn: $(btn_primary),
							method: "assign_shifts",
							freeze_message: __("Creating Shift Assignment"),
							callback: (r) => {
								if (!r.exc) {
									frappe.msgprint(__("Shift Assignments Created"));
									frm.reload_doc();
								}
							}
						});
					}
				});
			}
		});
	},

	generate_view: function (frm) {
		get_shift_pattern_dates();
	}
});

var get_shift_pattern_dates = function () {
	cur_frm.clear_table("shift_pattern_view");

	if (!cur_frm.doc.shift_pattern) {
		frappe.throw("Please select <b>Shift Pattern</b>");
	} else if (!cur_frm.doc.from_date) {
		frappe.throw("Please set <b>From Date</b>");
	} else if (!cur_frm.doc.to_date) {
		frappe.throw("Please set <b>To Date</b>");
	} else if (cur_frm.doc.from_date > cur_frm.doc.to_date) {
		frappe.throw("<b>To Date</b> Can't be less than <b>From Date</b>");
	} else {
		cur_frm.call({
			doc: cur_frm.doc,
			method: 'generate_shift_pattern_view',
			callback: function (r, rt) { }
		});
	}
}
