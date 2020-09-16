// Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt

frappe.ui.form.on('Attendance Approval', {
	refresh: function (frm) {
		const assets = [
			"/assets/frappe/css/frappe-datatable.css",
			"/assets/frappe/js/lib/clusterize.min.js",
			"/assets/frappe/js/lib/Sortable.min.js",
			"/assets/frappe/js/lib/frappe-datatable.js"
		];

		frappe.require(assets, () => {
			if (frm.doc.attendance_data) {
				make_attendance_table(JSON.parse(frm.doc.attendance_data));
			}
		});

		if (frm.doc.docstatus === 0) {
			frm.add_custom_button(__('Get Attendance'), function () {
				if (frm.doc.attendance_data) {
					frappe.confirm(
						'The current attendance data will be erased',
						function () {
							var wrapper = $(frm.get_field('attendance_display').wrapper);
							wrapper.empty();

							frm.call({
								method: "get_employees_attendance",
								doc: frm.doc,
								freeze: true,
								freeze_message: __("Generating Attendance"),
								callback: function (r) {
									var attendance_data = r.message.attendance_data;
									make_attendance_table(attendance_data);
									frm.dirty();
								}
							});
						},
						function () { }
					);
				} else {
					var wrapper = $(frm.get_field('attendance_display').wrapper);
					wrapper.empty();

					frm.call({
						method: "get_employees_attendance",
						doc: frm.doc,
						freeze: true,
						freeze_message: __("Generating Attendance"),
						callback: function (r) {
							var attendance_data = r.message.attendance_data;
							make_attendance_table(attendance_data);
							frm.dirty();
						}
					});
				}
			});
		}
	},

	branch: function (frm) {
		//if (frm.doc.from_date && frm.doc.to_date && frm.doc.branch) {
		//	frm.trigger("get_employees_attendance");
		//}
	},

	from_date: function (frm) {
		//frm.trigger("branch");
	},

	to_date: function (frm) {
		//frm.trigger("branch");
	},

	get_employees_attendance: function (frm) {
		var wrapper = $(frm.get_field('attendance_display').wrapper);
		wrapper.empty();

		frm.call({
			method: "get_employees_attendance",
			doc: frm.doc,
			callback: function (r) {
				console.log(r.message);
				var employees = r.message;
			}
		});
	}
});

var make_attendance_table = function (attendance_data) {
	var columns = [{
		id: 'employee_name',
		name: 'Employee Name',
		content: 'Employee Name',
		editable: false,
		resizable: false,
		sortable: false,
		focusable: false,
		dropdown: false,
		align: 'center'
	}];

	for (const [emp, attendances] of Object.entries(attendance_data)) {
		for (const [date, attendance] of Object.entries(attendances)) {
			columns.push({
				id: frappe.utils.get_random(6),
				name: attendance.att_date_display,
				content: attendance.att_date_display,
				editable: false,
				resizable: false,
				sortable: false,
				//focusable: false,
				dropdown: false,
				align: 'center'
			});
		}
		break;
	}

	var rows = []
	for (const [emp, attendances] of Object.entries(attendance_data)) {
		var row_data = [];
		for (const [date, attendance] of Object.entries(attendances)) {
			row_data.push(
				{
					content: attendance.emp_name,
					editable: false,
					resizable: false,
					sortable: false,
					focusable: false,
					dropdown: false,
					format: (val) => {
						return val.bold();
					}
				}
			);
			break;
		}
		for (const [date, attendance] of Object.entries(attendances)) {
			row_data.push({
				content: format_data(attendance, emp),
				editable: false,
				resizable: false,
				sortable: false,
				focusable: false,
				dropdown: false
			});
		}
		rows.push(row_data);
	}

	const options = {
		columns: columns,
		data: rows,
		layout: columns.length < 10 ? 'fluid' : 'fixed',
		serialNoColumn: false,
		checkboxColumn: false,
		noDataMessage: __('No Data'),
		disableReorderColumn: true
	}
	//console.log(options);
	const datatable = new DataTable(cur_frm.fields_dict['attendance_display'].wrapper, options);

	var r_idx = 0;
	for (const [emp, attendances] of Object.entries(attendance_data)) {
		var c_idx = 0;
		for (const [date, attendance] of Object.entries(attendances)) {
			var color = '';
			var bg_color = '';
			if (attendance.attendance_status == 'On Leave') {
				color = 'rgba(0,0,0,.5)';
				bg_color = '#FFEB3B';
			} else if (attendance.attendance_status == 'Present') {
				color = '#ecf0f1';
				bg_color = '#4CAF50';
			} else if (attendance.attendance_status == 'Absent') {
				color = '#ecf0f1';
				bg_color = '#F44336';
			} else if (attendance.attendance_status == 'Off') {
				color = '#ecf0f1';
				bg_color = '#9E9E9E';
			}

			datatable.style.setStyle(`[data-row-index="${r_idx}"][data-col-index="${(c_idx + 2)}"]`, {
				'text-align': 'center',
				'background-color': bg_color,
				'color': color
			});
			c_idx++;
		}
		r_idx++;
	}

	$('.content.ellipsis').css('height', 'auto');
}

function format_data(att, employee_name) {
	var result = '';

	if (att.attendance_status == "On Leave") {
		result += `<div class="att-cell" data-emp="${employee_name}" data-date="${att.attendance_date}">${att.attendance_status} ${(att.has_checkins_outside_duty ? `<i style="color:#${(att.record_status == 'Unresolved' ? `920808` : `ffffff`)};" class="fa fa-exclamation-circle"></i>` : '')}<br>(${att.leave_type})`;
	} else if (att.attendance_status == "Off") {
		result += `<div class="att-cell" data-emp="${employee_name}" data-date="${att.attendance_date}">${att.attendance_status} ${(att.has_checkins_outside_duty ? `<i style="color:#${(att.record_status == 'Unresolved' ? `920808` : `ffffff`)};" class="fa fa-exclamation-circle"></i>` : '')}`;
	} else if (att.attendance_status == "Present") {
		result += `<div class="att-cell" data-emp="${employee_name}" data-date="${att.attendance_date}"><b>(${att.shift_abbreviation})</b> ${(att.has_checkins_outside_duty ? `<i style="color:#${(att.record_status == 'Unresolved' ? `920808` : `ffffff`)};" class="fa fa-exclamation-circle"></i>` : '')}<br>
			<b>${att.in_time}</b> - <b>${att.out_time}</b><br>
			<b>WH:</b> ${parseFloat(att.working_hours).toFixed(2)}`;

		var overtime = 0
		for (var i = 0; i < att.overtime.length; i++) {
			overtime += att.overtime[i].hours;
		}

		if (overtime) {
			result += ` - <span style="color:yellow"><b><u>OT:</u></b> ${parseFloat(overtime).toFixed(2)}</span>`;
		}

		if (att.late_entry_time) {
			result += `<br><b>LE:</b> ${att.late_entry_time}`;
		}

		if (att.early_exit_time) {
			result += `${(att.late_entry_time ? ' - ' : '<br>')}<b>EE:</b> ${att.early_exit_time}`;
		}
	} else if (att.attendance_status == "Absent") {
		result += `<div class="att-cell" data-emp="${employee_name}" data-date="${att.attendance_date}"><b>(${att.shift_abbreviation})</b> ${(att.has_checkins_outside_duty ? `<i style="color:#${(att.record_status == 'Unresolved' ? `920808` : `ffffff`)};" class="fa fa-exclamation-circle"></i>` : '')}`;
	}

	result += `</div>`

	return result;
}

$(document).on('dblclick', '.att-cell', function () {
	var col_index = $(this).parents('td').data('col-index');
	var row_index = $(this).parents('td').data('row-index');
	var date = $(`thead td[data-col-index="${col_index}"] .content`).html();
	var emp_name = $(`tbody td[data-col-index="1"][data-row-index="${row_index}"] .content`).html();
	var employee = $(this).data('emp');
	var att_date = $(this).data('date');
	var attendance_data = JSON.parse(cur_frm.doc.attendance_data);
	var selected_att = attendance_data[employee][att_date];
	var old_overtime = $.extend(true, {}, selected_att.overtime);;
	//console.log(selected_att);

	var d = new frappe.ui.Dialog({
		title: `${emp_name} | ${selected_att.att_date_display}`,
		fields: [
			{
				"fieldtype": "Link",
				"fieldname": "employee",
				"label": __("Employee"),
				"options": "Employee",
				"hidden": 1,
				"default": employee
			},
			{
				"fieldtype": "Date",
				"fieldname": "attendance_date",
				"label": __("Attendance Date"),
				"read_only": 1,
				"default": selected_att.attendance_date
			},
			{
				"fieldtype": "Select",
				"fieldname": "status",
				"options": `Present\nAbsent\nOn Leave\nOff`,
				"label": __("Status"),
				"default": selected_att.attendance_status
			},
			{
				"fieldtype": "Column Break",
				"fieldname": "column_break_1",
			},
			{
				"fieldtype": "Select",
				"fieldname": "record_status",
				"options": `\nResolved\nUnresolved`,
				"label": __("Record Status"),
				"default": selected_att.record_status
			},
			{
				"fieldtype": "Float",
				"fieldname": "working_hours",
				"label": __("Working Hours"),
				"precision": 3,
				"default": selected_att.working_hours
			},
			{
				"fieldtype": "Section Break",
				"fieldname": "details_section_break",
				"label": __("Details"),
			},
			{
				"fieldtype": "Link",
				"fieldname": "shift",
				"label": __("Shift"),
				"options": "Shift Type",
				"default": selected_att.shift_assignment
			},
			{
				"fieldtype": "Section Break",
				"fieldname": "section_break_2",
				"hide_border": 1
			},
			{
				"fieldtype": "Datetime",
				"fieldname": "in_time",
				"label": __("In Time"),
				"default": selected_att.in_time_field
			},
			{
				"fieldtype": "Check",
				"fieldname": "late_entry",
				"label": __("Late Entry"),
				"default": selected_att.late_entry
			},
			{
				"fieldtype": "Time",
				"fieldname": "late_entry_time",
				"label": __("Late Entry Time"),
				//"precision": 2,
				"depends_on": "eval:doc.late_entry===1",
				"default": selected_att.late_entry_time
			},
			{
				"fieldtype": "Column Break",
				"fieldname": "column_break_2",
			},
			{
				"fieldtype": "Datetime",
				"fieldname": "out_time",
				"label": __("Out Time"),
				"default": selected_att.out_time_field
			},
			{
				"fieldtype": "Check",
				"fieldname": "early_exit",
				"label": __("Early Exit"),
				"default": selected_att.early_exit
			},
			{
				"fieldtype": "Time",
				"fieldname": "early_exit_time",
				"label": __("Early Exit Time"),
				"precision": 2,
				"depends_on": "eval:doc.early_exit===1",
				"default": selected_att.early_exit_time
			},
			{
				"fieldtype": "Section Break",
				"fieldname": "logs_section_break"
			},
			{
				"fieldtype": "Table",
				"fieldname": "logs",
				"label": __("Logs"),
				cannot_add_rows: true,
				in_place_edit: true,
				"fields": [
					{
						"fieldtype": "Datetime",
						"fieldname": "time",
						"label": __("Time"),
						in_list_view: 1,
						read_only: 1
					},
					{
						"fieldtype": "Select",
						"fieldname": "log_type",
						"label": __("Log Type"),
						"options": "\nIN\nOUT",
						in_list_view: 1,
						read_only: 1
					}
				],
				data: (selected_att.checkins ? selected_att.checkins : []),
				get_data: () => {
					return (selected_att.checkins ? selected_att.checkins : []);
				}
			},
			{
				"fieldtype": "Section Break",
				"fieldname": "overtime_section_break"
			},
			{
				"fieldtype": "Table",
				"fieldname": "overtime",
				"label": __("Overtime"),
				cannot_add_rows: true,
				in_place_edit: true,
				"fields": [
					{
						"fieldtype": "Select",
						"fieldname": "percentage",
						"label": __("Percentage"),
						"options": "\n100%\n125%\n150%\nHoliday",
						in_list_view: 1,
						read_only: 1
					},
					{
						"fieldtype": "Float",
						"fieldname": "hours",
						"label": __("Hours"),
						in_list_view: 1
					}
				],
				data: (selected_att.overtime ? selected_att.overtime : []),
				get_data: () => {
					return (selected_att.overtime ? selected_att.overtime : []);
				},
			},
			{
				"fieldtype": "Section Break",
				"fieldname": "change_section_break"
			},
			{
				"fieldtype": "Table",
				"fieldname": "change_log",
				"label": __("Change Log"),
				cannot_add_rows: true,
				in_place_edit: true,
				"fields": [
					{
						"fieldtype": "Datetime",
						"fieldname": "time",
						"label": __("Time"),
						in_list_view: 1,
						read_only: 1
					},
					{
						"fieldtype": "Data",
						"fieldname": "user",
						"label": __("User"),
						in_list_view: 1,
						read_only: 1
					},
					{
						"fieldtype": "Data",
						"fieldname": "field",
						"label": __("Field"),
						in_list_view: 1,
						read_only: 1
					},
					{
						"fieldtype": "Data",
						"fieldname": "from",
						"label": __("From"),
						in_list_view: 1,
						read_only: 1
					},
					{
						"fieldtype": "Data",
						"fieldname": "to",
						"label": __("To"),
						in_list_view: 1,
						read_only: 1
					}
				],
				data: (selected_att.change_log ? selected_att.change_log : []),
				get_data: () => {
					return (selected_att.change_log ? selected_att.change_log : []);
				}
			}
		],
		primary_action: function () {
			var attendance_status = cur_dialog.get_value('status');
			var record_status = cur_dialog.get_value('record_status');
			var working_hours = cur_dialog.get_value('working_hours');
			var shift = cur_dialog.get_value('shift');
			var in_time = cur_dialog.get_value('in_time');
			var out_time = cur_dialog.get_value('out_time');
			var late_entry = cur_dialog.get_value('late_entry');
			var late_entry_time = cur_dialog.get_value('late_entry_time');
			var early_exit = cur_dialog.get_value('early_exit');
			var early_exit_time = cur_dialog.get_value('early_exit_time');
			var overtime = cur_dialog.get_value('overtime');
			var change_log = cur_dialog.get_value('change_log');
			var new_change_log = [];

			if (attendance_status != selected_att.attendance_status) {
				attendance_data[employee][att_date]['attendance_status'] = attendance_status;
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Status',
					'from': selected_att.attendance_status,
					'to': attendance_status
				});
			}

			if (record_status != selected_att.record_status) {
				attendance_data[employee][att_date]['record_status'] = record_status;
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Record Status',
					'from': selected_att.record_status,
					'to': record_status
				});
			}

			if (!working_hours)
				working_hours = 0;

			if (parseFloat(working_hours).toFixed(3) != parseFloat(selected_att.working_hours).toFixed(3)) {
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Working Hours',
					'from': selected_att.working_hours,
					'to': working_hours
				});
				attendance_data[employee][att_date]['working_hours'] = working_hours;
			}

			if (!shift || typeof shift == 'undefined')
				shift = "";

			if (shift != selected_att.shift_assignment) {
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Shift',
					'from': selected_att.shift_assignment,
					'to': shift
				});
				attendance_data[employee][att_date]['shift'] = shift;
			}

			if (in_time != selected_att.in_time_field) {
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'In Time',
					'from': selected_att.in_time_field,
					'to': in_time
				});
				attendance_data[employee][att_date]['in_time_field'] = in_time;
				attendance_data[employee][att_date]['in_time'] = new moment(in_time).format("HH:mm");
			}

			if (out_time != selected_att.out_time_field) {
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Out Time',
					'from': selected_att.out_time_field,
					'to': out_time
				});
				attendance_data[employee][att_date]['out_time_field'] = out_time;
				attendance_data[employee][att_date]['out_time'] = new moment(out_time).format("HH:mm");
			}

			if (late_entry != selected_att.late_entry) {
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Late Entry',
					'from': selected_att.late_entry,
					'to': late_entry
				});
				attendance_data[employee][att_date]['late_entry'] = late_entry;
			}

			if (late_entry_time != selected_att.late_entry_time && (late_entry_time || selected_att.late_entry_time)) {
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Late Entry Time',
					'from': selected_att.late_entry_time,
					'to': late_entry_time
				});
				attendance_data[employee][att_date]['late_entry_time'] = late_entry_time;
			}

			if (early_exit != selected_att.early_exit) {
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Early Exit',
					'from': selected_att.early_exit,
					'to': early_exit
				});
				attendance_data[employee][att_date]['early_exit'] = early_exit;
			}

			if (early_exit_time != selected_att.early_exit_time && (early_exit_time || selected_att.early_exit_time)) {
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Early Exit Time',
					'from': selected_att.early_exit_time,
					'to': early_exit_time
				});
				attendance_data[employee][att_date]['early_exit_time'] = early_exit_time;
			}

			if (early_exit != selected_att.early_exit) {
				new_change_log.push({
					'time': frappe.datetime.now_datetime(),
					'user': frappe.session.user,
					'field': 'Early Exit',
					'from': selected_att.early_exit,
					'to': early_exit
				});
				attendance_data[employee][att_date]['early_exit'] = early_exit;
			}

			for (var i = 0; i < overtime.length; i++) {
				if (overtime[i].hours != old_overtime[i].hours) {
					new_change_log.push({
						'time': frappe.datetime.now_datetime(),
						'user': frappe.session.user,
						'field': 'Overtime ' + overtime[i].percentage,
						'from': old_overtime[i].hours,
						'to': overtime[i].hours
					});
				}
			}

			if (new_change_log) {
				var concat_log = change_log.concat(new_change_log);
				attendance_data[employee][att_date]['change_log'] = concat_log;
				make_attendance_table(attendance_data);
				cur_frm.doc.attendance_data = JSON.stringify(attendance_data);
				cur_frm.dirty();
			}

			cur_dialog.hide();
			return false;
		},
		primary_action_label: __('Update')
	});

	d.get_field("logs").grid.cannot_add_rows = true;
	d.get_field("logs").grid.only_sortable();
	d.get_field("logs").refresh();

	//d.get_field("overtime").grid.cannot_add_rows = true;
	//d.get_field("overtime").grid.only_sortable();
	//d.get_field("overtime").refresh();


	d.show();
	$(d.$wrapper.find('.modal-dialog')).width('60%');
});