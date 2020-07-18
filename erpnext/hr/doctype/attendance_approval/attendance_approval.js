// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Approval', {
	branch: function(frm) {
		if (frm.doc.from_date && frm.doc.to_date && frm.doc.branch) {
			frm.trigger("get_employees_attendance");
		}
	},

	from_date: function(frm) {
		frm.trigger("branch");
	},

	to_date: function(frm) {
		frm.trigger("branch");
	},

	get_employees_attendance: function(frm) {
		var wrapper = $(frm.get_field('attendance_display').wrapper);
		wrapper.empty();

		frm.call({
			method: "get_employees_attendance",
			doc: frm.doc,
			callback: function(r) {
				console.log(r.message);
				var employees = r.message;
			}
		});
	}
});
