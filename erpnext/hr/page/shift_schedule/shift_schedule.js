frappe.pages['shift-schedule'].on_page_load = function (wrapper) {
	var me = this;
	var page = frappe.ui.make_app_page({
		parent: wrapper,
		title: 'Shift Schedule',
		single_column: true
	});

	frappe.breadcrumbs.add("HR");
	//page.main.html(frappe.render_template("shift_schedule", {}));

	this.branch = page.add_field({
		fieldname: "branch",
		label: __("Branch"),
		fieldtype: "Link",
		options: "Branch",
		reqd: 1,
		change: (e) => {
			//this.options.selected_branch = this.branch.get_value();
			//this.make_request();
		}
	});

	this.date_range = page.add_field({
		fieldtype: 'DateRange',
		fieldname: 'selected_date_range',
		label: __("Date Range"),
		placeholder: "Date Range",
		default: [frappe.datetime.month_start(), frappe.datetime.month_end()],
		input_class: 'input-sm',
		reqd: 1,
		change: (e) => {
			//this.options.selected_date_range = this.date_range.get_value();
			//this.make_request();
		}
	});

	this.start_hour = page.add_field({
		fieldname: "start_hour",
		label: __("Start Hour"),
		fieldtype: "Select",
		options: "00\n01\n02\n03\n04\n05\n06\n07\n08\n09\n10\n11\n12\n13\n14\n15\n16\n17\n18\n19\n20\n21\n22\n23",
		default: "07",
		reqd: 1,
		change: (e) => {
			//this.options.selected_start_hour = this.start_hour.get_value();
			//this.make_request();
		}
	});

	this.show_schedule = page.add_field({
		fieldname: "show_schedule",
		label: __("Show Schedule"),
		fieldtype: "Button",
		click: (e) => {
			var errors = [];
			if (!this.branch.value) {
				errors.push('- Branch');
			}

			if (!this.date_range.value) {
				errors.push('- Date Range');
			}

			if (!this.start_hour.value) {
				errors.push('- Start Hour');
			}

			if (errors.length > 0) {
				frappe.msgprint("Please enter:<br>" + errors.join("<br>"), "Error");
			} else {
				show_schedule(this.branch.value, this.date_range.value, this.start_hour.value);
			}

		}
	});

	//console.log(page);
}

var show_schedule = function (branch, date_range, start_hour) {
	frappe.call({
		"method": "erpnext.hr.page.shift_schedule.shift_schedule.get_schedule_records",
		args: {
			branch: branch,
			date_range: date_range,
			start_hour: start_hour
		},
		freeze: true,
		freeze_message: __("Getting Schedule..."),
		callback: function (r) {
			var data = r.message;
			var hours = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09', '10', '11', '12', '13', '14', '15', '16', '17', '18', '19', '20', '21', '22', '23']
			var sorted_hours = [];
			var sorted_int_hours = [];

			var i = parseInt(start_hour);
			var x = 0;
			while (x <= 23) {
				if (i > 23) {
					var z = Math.abs(24 - i);
					sorted_hours.push(hours[z]);
					sorted_int_hours.push(parseInt(hours[z]));
				} else {
					sorted_hours.push(hours[i]);
					sorted_int_hours.push(parseInt(hours[i]));
				}
				i++;
				x++;
			}

			var html = frappe.render_template('shift_schedule', {
				data: data,
				hours: sorted_hours,
				int_hours: sorted_int_hours
			});

			$('.layout-footer').removeClass('hide');
			$('.layout-footer').html(html);
		}
	});
};

$(document).on('click', '.btn-reschedule', function () {
	var shift_assignment = $(this).data('shift-assignment');
	frappe.call({
		method: "frappe.client.get",
		args: {
			doctype: "Shift Assignment",
			filters: { name: shift_assignment }
		},
		freeze: true,
		freeze_message: __("Getting Shift Assignment..."),
		callback: function (r) {
			if (r.message) {
				var shift = r.message;
				var d = new frappe.ui.Dialog({
					title: `${shift.employee_name} | ${shift.date}`,
					fields: [
						{
							"fieldtype": "Link",
							"fieldname": "shift_assignment",
							"label": __("Shift Assignment"),
							"options": "Shift Assignment",
							"hidden": 1,
							"default": shift.name
						},
						{
							"fieldtype": "Date",
							"fieldname": "date",
							"label": __("Date"),
							"read_only": 1,
							"default": shift.date
						},
						{
							"fieldtype": "Link",
							"fieldname": "employee",
							"label": __("Employee"),
							"options": "Employee",
							"hidden": 1,
							"default": shift.employee
						},
						{
							"fieldtype": "Data",
							"fieldname": "employee_name",
							"label": __("Employee Name"),
							"read_only": 1,
							"default": shift.employee_name
						},
						{
							"fieldtype": "Link",
							"fieldname": "shift_type",
							"options": `Shift Type`,
							"label": __("Shift Type"),
							"default": shift.shift_type
						},
						{
							"fieldtype": "Button",
							"fieldname": "cancel_shift_assignment",
							"label": __("Cancel Shift Assignment")
						}
					],
					primary_action: function () {
						var selected_shift_assignment = cur_dialog.get_value('shift_assignment');
						var selected_shift_type = cur_dialog.get_value('shift_type');
						frappe.call({
							"method": "erpnext.hr.page.shift_schedule.shift_schedule.reschedule",
							args: {
								shift_assignment: selected_shift_assignment,
								shift_type: selected_shift_type
							},
							freeze: true,
							freeze_message: __("Getting Schedule..."),
							callback: function (r) {
								cur_dialog.hide();
								if (r.message) {
									frappe.show_alert({message:__(r.message), indicator:'green'});
								}
								show_schedule(cur_page.page.branch.value, cur_page.page.date_range.value, cur_page.page.start_hour.value);
							}
						});

						//frappe.db.set_value("Shift Assignment", selected_shift_assignment, "shift_type", selected_shift_type);
						return false;
					},
					primary_action_label: __('Reschedule')
				});

				d.show();
				d.wrapper.find('button[data-fieldname="cancel_shift_assignment"]').addClass('btn-danger');
				d.wrapper.on('click', 'button[data-fieldname="cancel_shift_assignment"]', function () {
					frappe.call({
						"method": "erpnext.hr.page.shift_schedule.shift_schedule.cancel_shift_assignment",
						args: {
							shift_assignment: cur_dialog.get_value('shift_assignment')
						},
						freeze: true,
						freeze_message: __("Cancelling Shift Assignment..."),
						callback: function (r) {
							cur_dialog.hide();
							if (r.message) {
								frappe.show_alert({message:__(r.message), indicator:'green'});
							}
							show_schedule(cur_page.page.branch.value, cur_page.page.date_range.value, cur_page.page.start_hour.value);
						}
					});
				});
			}
		}
	});
});

$(document).on('click', '.btn-schedule', function () {
	var date = $(this).data('date');
	var emp_doc = $(this).data('emp');
	var emp_name = $(this).data('emp-name');

	var d = new frappe.ui.Dialog({
		title: `${emp_name} | ${date}`,
		fields: [
			{
				"fieldtype": "Date",
				"fieldname": "date",
				"label": __("Date"),
				"read_only": 1,
				"default": date
			},
			{
				"fieldtype": "Link",
				"fieldname": "employee",
				"label": __("Employee"),
				"options": "Employee",
				"hidden": 1,
				"default": emp_doc
			},
			{
				"fieldtype": "Data",
				"fieldname": "employee_name",
				"label": __("Employee Name"),
				"read_only": 1,
				"default": emp_name
			},
			{
				"fieldtype": "Link",
				"fieldname": "shift_type",
				"options": `Shift Type`,
				"label": __("Shift Type")
			}
		],
		primary_action: function () {
			var selected_date = d.get_value('date');
			var selected_emp = d.get_value('employee');
			var selected_shift_type = d.get_value('shift_type');
			frappe.call({
				"method": "erpnext.hr.page.shift_schedule.shift_schedule.schedule",
				args: {
					date: selected_date,
					employee: selected_emp,
					shift_type: selected_shift_type
				},
				freeze: true,
				freeze_message: __("Updating Shift Assignment..."),
				callback: function (r) {
					d.hide();
					if (r.message) {
						frappe.show_alert({message:__(r.message), indicator:'green'});
					}
					show_schedule(cur_page.page.branch.value, cur_page.page.date_range.value, cur_page.page.start_hour.value);
				}
			});

			//frappe.db.set_value("Shift Assignment", selected_shift_assignment, "shift_type", selected_shift_type);
			return false;
		},
		primary_action_label: __('Assign Shift')
	});

	d.show();
});

$(document).on('click', '.clone', function () {
	var date = $(this).data('date');
	var emp_doc = $(this).data('emp');
	var emp_name = $(this).data('emp-name');
	var shift = $(this).data('shift');

	var d = new frappe.ui.Dialog({
		title: `${emp_name} | ${date}`,
		fields: [
			{
				fieldtype: 'DateRange',
				fieldname: 'selected_date_range',
				label: __("Date Range"),
				placeholder: "Date Range",
				//input_class: 'input-sm'
			},
			{
				"fieldtype": "Link",
				"fieldname": "employee",
				"label": __("Employee"),
				"options": "Employee",
				"default": emp_doc,
				change: (e) => {
					frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Employee',
							filters: { name: d.get_value('employee') }
						},
						callback: function(r){
							d.set_value('employee_name', r.employee_name)
						}

					});
				}
			},
			{
				"fieldtype": "Data",
				"fieldname": "employee_name",
				"label": __("Employee Name"),
				"read_only": 1,
				"default": emp_name
			},
			{
				"fieldtype": "Link",
				"fieldname": "shift_type",
				"options": `Shift Type`,
				"label": __("Shift Type"),
				"default": shift
			}
		],
		primary_action: function () {
			var selected_date_range = d.get_value('selected_date_range');
			var selected_emp = d.get_value('employee');
			var selected_shift_type = d.get_value('shift_type');
			frappe.call({
				"method": "erpnext.hr.page.shift_schedule.shift_schedule.clone_schedule",
				args: {
					date_range: selected_date_range,
					employee: selected_emp,
					shift_type: selected_shift_type
				},
				freeze: true,
				freeze_message: __("Updating Shift Assignment..."),
				callback: function (r) {
					d.hide();
					if (r.message) {
						frappe.show_alert({message:__(r.message), indicator:'green'});
					}
					show_schedule(cur_page.page.branch.value, cur_page.page.date_range.value, cur_page.page.start_hour.value);
				}
			});

			//frappe.db.set_value("Shift Assignment", selected_shift_assignment, "shift_type", selected_shift_type);
			return false;
		},
		primary_action_label: __('Clone')
	});

	d.show();
});