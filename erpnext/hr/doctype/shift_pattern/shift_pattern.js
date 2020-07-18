// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Shift Pattern', {
	refresh: function (frm) {
		
	},

	unit_of_cycle: function (frm) {
		setup_shift_pattern_days(frm.doc.unit_of_cycle, frm.doc.no_of_cycles);
	},

	no_of_cycles: function (frm) {
		setup_shift_pattern_days(frm.doc.unit_of_cycle, frm.doc.no_of_cycles);
	}
});

var setup_shift_pattern_days = function (unit_of_cycle, cycles_no) {
	var week_days = ["Sunday", "Munday", "Tuesday", "Wednesday", "Thirsday", "Friday", "Saturday"];
	cur_frm.clear_table("shift_pattern");

	for (var i = 1; i <= cycles_no; i++) {
		if (unit_of_cycle == "Day") {
			var row = cur_frm.add_child("shift_pattern");
			row.day = "Day " + i;
		} else if (unit_of_cycle == "Week") {
			for (var x = 0; x < 7; x++) {
				var row = cur_frm.add_child("shift_pattern");
				row.day = "Week " + i + ": " + week_days[x];
			}
		}
	}

	refresh_field("shift_pattern");
}