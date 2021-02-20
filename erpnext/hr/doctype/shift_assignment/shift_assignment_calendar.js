// Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.views.calendar["Shift Assignment"] = {
	field_map: {
		"start": "date",
		"end": "date",
		"id": "name",
		"title": "employee",
		"allDay": "allDay",
		"progress": "progress",
		"docstatus": 1
	},
	gantt: true,
	options: {
		header: {
			left: 'prev,next today',
			center: 'title',
			right: 'month'
		}
	},
	get_events_method: "erpnext.hr.doctype.shift_assignment.shift_assignment.get_events"
}