# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from pprint import pprint
import datetime, json
from datetime import timedelta
from erpnext.hr.doctype.shift_assignment.shift_assignment import get_employee_shift_timings, get_shift_details
from frappe.utils import flt, cint

class AttendanceApproval(Document):
	def get_employees_attendance(self):
		out = []
		attendance_data = frappe._dict()
		date_attendance = frappe._dict()
		employees = frappe.get_list("Employee", fields=["name", "employee_name"], filters={"branch": self.branch}, order_by="employee_name")
		for emp in employees:
			emp_attendance = []
			for days_count in range(frappe.utils.date_diff(self.to_date, self.from_date) + 1):
				current_date = frappe.utils.add_days(self.from_date, days_count)
				day_data = frappe._dict()
				on_leave = frappe.get_list("Attendance", fields=['leave_type'], filters=[{"employee": emp.name}, {"status": "On Leave"}, {"attendance_date": current_date}])
				assigned_shift = frappe.get_list("Shift Assignment", fields=['shift_type'], filters=[{"employee": emp.name}, {"date": current_date}])
				att_date_display = frappe.utils.get_datetime(current_date).strftime("%e %b %y")
				has_chechkins_outside_duty = False
				curr_date = current_date

				attendance_status = late_entry_time = early_exit_time = in_time = out_time = ""
				working_hours = late_entry = early_exit = 0

				max_overtime_working_hours = 8
				overtime_100 = 1
				overtime_125 = 1.25
				overtime_125_from_hour = frappe.utils.datetime.timedelta(hours=7)
				overtime_125_to_hour = frappe.utils.datetime.timedelta(hours=19)
				overtime_150 = 1.5
				overtime_150_from_hour = frappe.utils.datetime.timedelta(hours=19)
				overtime_150_to_hour = frappe.utils.datetime.timedelta(hours=7)
				overtime_holiday = 1.5
				overtime_100_hours = 0.0
				overtime_125_hours = 0.0
				overtime_150_hours = 0.0
				overtime_holiday_hours = 0.0

				if on_leave:
					outside_duty_checkins = frappe.db.sql("""SELECT *, (@row_number:=@row_number + 1) AS idx
						FROM `tabEmployee Checkin`, (SELECT @row_number:=0) AS temp
						WHERE employee = %(employee)s
						AND DATE(`time`) = %(current_date)s
						ORDER BY `time`
					""", {"employee":emp.name, "current_date":current_date}, as_dict=1)

					if outside_duty_checkins:
						if len(emp_attendance) and emp_attendance[len(emp_attendance)-1]['checkins']:
							unique_checkins = []
							for checkin in outside_duty_checkins:
								exist = False
								for log in emp_attendance[len(emp_attendance)-1]['checkins']:
									if log.time == checkin.time:
										exist = True
								if not exist:
									unique_checkins.append(checkin)

							outside_duty_checkins = unique_checkins

						if outside_duty_checkins:
							has_chechkins_outside_duty = True
					
					overtime = [
						{
							'percentage': '100%',
							'hours': overtime_100_hours
						},
						{
							'percentage': '125%',
							'hours': overtime_125_hours
						},
						{
							'percentage': '150%',
							'hours': overtime_150_hours
						},
						{
							'percentage': 'Holiday',
							'hours': overtime_holiday_hours
						},
					]

					emp_attendance.append({
						"emp_name": emp.employee_name,
						"attendance_date": curr_date,
						"att_date_display": att_date_display,
						"attendance_status": "On Leave",
						"record_status": ('Unresolved' if has_chechkins_outside_duty else ''),
						"leave_type": on_leave[0].leave_type,
						"has_checkins_outside_duty": has_chechkins_outside_duty,
						"checkins": outside_duty_checkins,
						"overtime": overtime,
						"late_entry": late_entry,
						"early_exit": late_entry,
						"working_hours": working_hours,
						"shift_assignment": "",
						"change_log": []
					})

				elif assigned_shift:
					shift_type_doc = frappe.get_doc("Shift Type", assigned_shift[0].shift_type)
					end_date = ""
					outside_duty_date = current_date
					if shift_type_doc.get("in_two_days") and shift_type_doc.calculate_attendance_date_as_per == "Check-in":
						end_date = frappe.utils.add_days(current_date, 1)
					elif shift_type_doc.get("in_two_days") and shift_type_doc.calculate_attendance_date_as_per == "Check-out":
						end_date = current_date
						current_date = frappe.utils.add_days(current_date, -1)
						outside_duty_date = end_date
					else:
						end_date = current_date

					#curr_date = current_date

					current_date = frappe.utils.get_datetime(current_date + ' ' + str(shift_type_doc.start_time))
					current_date = (frappe.utils.add_to_date(current_date, minutes=(shift_type_doc.begin_check_in_before_shift_start_time * -1)))
					
					end_date = frappe.utils.get_datetime(end_date + ' ' + str(shift_type_doc.end_time))
					end_date = (frappe.utils.add_to_date(end_date, minutes=(shift_type_doc.allow_check_out_after_shift_end_time)))

					checkin_list = frappe.db.sql("""SELECT *, (@row_number:=@row_number + 1) AS idx
						FROM `tabEmployee Checkin`, (SELECT @row_number:=0) AS temp
						WHERE employee = %(employee)s
						AND `time` BETWEEN %(from_date)s AND %(to_date)s
						ORDER BY `time`
					""", {"employee":emp.name, "from_date":frappe.utils.get_datetime_str(current_date), "to_date":frappe.utils.get_datetime_str(end_date)}, as_dict=1)
					
					if len(checkin_list) > 1:
						attendance_status, working_hours, late_entry, late_entry_time, early_exit, early_exit_time, in_time, out_time = shift_type_doc.get_attendance(checkin_list)
					
					# Check Outside Shift Checkins
					shift_details = get_shift_details(shift_type_doc.name, frappe.utils.get_datetime(outside_duty_date))
					prev_shift, curr_shift, next_shift = get_employee_shift_timings(emp.name, shift_details.start_datetime, True)

					cond = ""
					if prev_shift:
						cond += """ AND (`time` NOT BETWEEN '{start}' AND '{end}') """.format(start=prev_shift.actual_start, end=prev_shift.actual_end)

					if curr_shift:
						cond += """ AND (`time` NOT BETWEEN '{start}' AND '{end}') """.format(start=curr_shift.actual_start, end=curr_shift.actual_end)
						overtime_end = frappe.utils.add_to_date(curr_shift.actual_end, hours=max_overtime_working_hours) if not next_shift else next_shift.actual_start
						cond += """ AND (`time` NOT BETWEEN '{start}' AND '{end}') """.format(start=curr_shift.actual_end, end=overtime_end)

					if next_shift:
						cond += """ AND (`time` NOT BETWEEN '{start}' AND '{end}') """.format(start=next_shift.actual_start, end=next_shift.actual_end)
						if shift_type_doc.get("in_two_days") and shift_type_doc.calculate_attendance_date_as_per == "Check-out":
							shift_details2 = get_shift_details(shift_type_doc.name, frappe.utils.get_datetime(frappe.utils.add_days(outside_duty_date, 1)))
							if shift_details2:
								cond += """ AND (`time` NOT BETWEEN '{start}' AND '{end}') """.format(start=shift_details2.actual_start, end=shift_details2.actual_end)

					outside_duty_checkins = frappe.db.sql("""SELECT *, (@row_number:=@row_number + 1) AS idx
						FROM `tabEmployee Checkin`, (SELECT @row_number:=0) AS temp
						WHERE employee = %(employee)s
						AND DATE(`time`) = %(current_date)s
						{conditions}
						ORDER BY `time`
					""".format(conditions=cond), {
						"employee":emp.name,
						"current_date":outside_duty_date
					}, as_dict=1)
					
					all_checkins = None

					if checkin_list:
						all_checkins = checkin_list.copy()

					if outside_duty_checkins:
						if len(emp_attendance) and emp_attendance[len(emp_attendance)-1]['checkins']:
							unique_checkins = []
							for checkin in outside_duty_checkins:
								exist = False
								for log in emp_attendance[len(emp_attendance)-1]['checkins']:
									if log.time == checkin.time:
										exist = True
								if not exist:
									unique_checkins.append(checkin)

							outside_duty_checkins = unique_checkins

						if outside_duty_checkins:
							has_chechkins_outside_duty = True
							if all_checkins:
								all_checkins = all_checkins.copy() + outside_duty_checkins.copy()
							else:
								all_checkins = outside_duty_checkins.copy()

					if all_checkins:
						all_checkins = sorted(all_checkins, key=lambda k: k['time'])

					# Overtime
					if curr_shift:
						overtime_end = frappe.utils.add_to_date(curr_shift.actual_end, hours=max_overtime_working_hours) if not next_shift else next_shift.actual_start
						overtime_cond = """ AND (`time` BETWEEN '{start}' AND '{end}') """.format(start=curr_shift.actual_end, end=overtime_end)
						if next_shift:
							overtime_cond += """ AND (`time` NOT BETWEEN '{start}' AND '{end}') """.format(start=next_shift.actual_start, end=next_shift.actual_end)
							if shift_type_doc.get("in_two_days") and shift_type_doc.calculate_attendance_date_as_per == "Check-out":
								shift_details2 = get_shift_details(shift_type_doc.name, frappe.utils.get_datetime(frappe.utils.add_days(outside_duty_date, 1)))
								if shift_details2:
									overtime_cond += """ AND (`time` NOT BETWEEN '{start}' AND '{end}') """.format(start=shift_details2.actual_start, end=shift_details2.actual_end)

						overtime_checkin = frappe.db.sql("""SELECT *, (@row_number:=@row_number + {idx}) AS idx
							FROM `tabEmployee Checkin`, (SELECT @row_number:=0) AS temp
							WHERE employee = %(employee)s
							{conditions}
							ORDER BY `time` DESC
							LIMIT 1
						""".format(idx=((len(all_checkins)+1) or 1), conditions=overtime_cond), {
							"employee":emp.name
						}, as_dict=1)

						if overtime_checkin:
							has_overtime = False
							old_out_time = out_time
							old_working_hours = working_hours
							if (attendance_status == 'Absent' or not attendance_status) and all_checkins:
								attendance_status = 'Present'
								in_time = all_checkins[0].time
								out_time = overtime_checkin[0].time
								working_hours = frappe.utils.time_diff_in_hours(out_time, in_time)
								if cint(shift_type_doc.enable_entry_grace_period) and in_time and in_time > curr_shift.start_datetime + timedelta(minutes=cint(shift_type_doc.late_entry_grace_period)):
									late_entry = True
									late_entry_time = in_time - curr_shift.start_datetime
								all_checkins = all_checkins.copy() + overtime_checkin.copy()
								has_overtime = True
							elif attendance_status == 'Present' and all_checkins:
								all_checkins = all_checkins.copy() + overtime_checkin.copy()
								out_time = overtime_checkin[0].time
								working_hours = working_hours + abs(frappe.utils.time_diff_in_hours(out_time, curr_shift.end_datetime))
								has_overtime = True
							else:
								all_checkins = overtime_checkin.copy()

							if has_overtime:
								overtime_hours = abs(frappe.utils.time_diff_in_hours(out_time, curr_shift.end_datetime))
								if overtime_hours <= max_overtime_working_hours:
									remaining_hours = overtime_hours
									overtime_time = in_time

									overtime_125_from = in_time.replace(hour=(overtime_125_from_hour.seconds//3600), minute=((overtime_125_from_hour.seconds % 3600) // 60), second=(overtime_125_from_hour.seconds % 60))
									overtime_125_to = in_time.replace(hour=(overtime_125_to_hour.seconds//3600), minute=((overtime_125_to_hour.seconds % 3600) // 60), second=(overtime_125_to_hour.seconds % 60))
									overtime_125_to = frappe.utils.add_to_date(overtime_125_to, days=1) if frappe.utils.time_diff_in_hours(overtime_125_to_hour, overtime_125_from_hour) < 0 else overtime_125_to

									overtime_150_from = in_time.replace(hour=(overtime_150_from_hour.seconds//3600), minute=((overtime_150_from_hour.seconds % 3600) // 60), second=(overtime_150_from_hour.seconds % 60))
									overtime_150_to = in_time.replace(hour=(overtime_150_to_hour.seconds//3600), minute=((overtime_150_to_hour.seconds % 3600) // 60), second=(overtime_150_to_hour.seconds % 60))
									overtime_150_to = frappe.utils.add_to_date(overtime_150_to, days=1) if frappe.utils.time_diff_in_hours(overtime_150_to_hour, overtime_150_from_hour) < 0 else overtime_150_to
									while(remaining_hours > 0.0):
										if overtime_time >= overtime_125_from and overtime_time < overtime_125_to:
											hours_diff = abs(frappe.utils.time_diff_in_hours(overtime_125_to, overtime_time)) if abs(frappe.utils.time_diff_in_hours(overtime_125_to, overtime_time)) < remaining_hours else remaining_hours
											overtime_125_hours += hours_diff
											remaining_hours -= hours_diff
											overtime_time = frappe.utils.add_to_date(overtime_time, hours=hours_diff)
										elif overtime_time >= overtime_150_from and overtime_time < overtime_150_to:
											hours_diff = abs(frappe.utils.time_diff_in_hours(overtime_150_to, overtime_time)) if abs(frappe.utils.time_diff_in_hours(overtime_150_to, overtime_time)) < remaining_hours else remaining_hours
											overtime_150_hours += hours_diff
											remaining_hours -= hours_diff
											overtime_time = frappe.utils.add_to_date(overtime_time, hours=hours_diff)
										else:
											reminaing_hours = 0
								else:
									out_time = old_out_time
									working_hours = old_working_hours
					
					overtime = [
						{
							'percentage': '100%',
							'hours': overtime_100_hours
						},
						{
							'percentage': '125%',
							'hours': overtime_125_hours
						},
						{
							'percentage': '150%',
							'hours': overtime_150_hours
						},
						{
							'percentage': 'Holiday',
							'hours': overtime_holiday_hours
						},
					]

					if late_entry_time:
						if len(str(late_entry_time)) < 8:
							late_entry_time = '0'+str(late_entry_time)
					
					if early_exit_time:
						if len(str(early_exit_time)) < 8:
							early_exit_time = '0'+str(early_exit_time)

					# Set Attendance status
					if attendance_status:
						emp_attendance.append({
							"emp_name": emp.employee_name,
							"attendance_date": curr_date,
							"att_date_display": att_date_display,
							"attendance_status": attendance_status,
							"record_status": ('Unresolved' if has_chechkins_outside_duty else ''),
							"shift_assignment": shift_type_doc.name,
							"shift_abbreviation": shift_type_doc.shift_abbreviation,
							"working_hours": working_hours,
							"late_entry": late_entry,
							"late_entry_time": late_entry_time,
							"early_exit": early_exit,
							"early_exit_time": early_exit_time,
							"in_time": frappe.utils.get_datetime(in_time).strftime("%H:%M"),
							"in_time_field": in_time,
							"out_time": frappe.utils.get_datetime(out_time).strftime("%H:%M"),
							"out_time_field": out_time,
							"has_checkins_outside_duty": has_chechkins_outside_duty,
							"checkins": all_checkins,
							"overtime": overtime,
							"change_log": []
						})
					else:
						attendance_status = "Absent"
						emp_attendance.append({
							"emp_name": emp.employee_name,
							"attendance_date": curr_date,
							"att_date_display": att_date_display,
							"attendance_status": attendance_status,
							"record_status": ('Unresolved' if has_chechkins_outside_duty else ''),
							"shift_assignment": shift_type_doc.name,
							"shift_abbreviation": shift_type_doc.shift_abbreviation,
							"has_checkins_outside_duty": has_chechkins_outside_duty,
							"checkins": all_checkins,
							"overtime": overtime,
							"late_entry": late_entry,
							"early_exit": late_entry,
							"working_hours": working_hours,
							"change_log": []
						})
				else:
					outside_duty_date = current_date
					current_date = frappe.utils.add_days(current_date, 1)
					assigned_shift = frappe.get_list("Shift Assignment", fields=['shift_type'], filters=[{"employee": emp.name}, {"date": current_date}])
					shift_type_doc = None
					if assigned_shift:
						shift_type_doc = frappe.get_doc("Shift Type", assigned_shift[0].shift_type)
					end_date = ""
					if shift_type_doc and shift_type_doc.get("in_two_days") and shift_type_doc.calculate_attendance_date_as_per == "Check-in":
						end_date = frappe.utils.add_days(current_date, 1)
					elif shift_type_doc and shift_type_doc.get("in_two_days") and shift_type_doc.calculate_attendance_date_as_per == "Check-out":
						end_date = current_date
						current_date = frappe.utils.add_days(current_date, -1)
					else:
						end_date = current_date

					#curr_date = current_date
					if shift_type_doc:
						current_date = frappe.utils.get_datetime(current_date + ' ' + str(shift_type_doc.start_time))
						current_date = (frappe.utils.add_to_date(current_date, minutes=(shift_type_doc.begin_check_in_before_shift_start_time * -1)))

						end_date = frappe.utils.get_datetime(end_date + ' ' + str(shift_type_doc.end_time))
						end_date = (frappe.utils.add_to_date(end_date, minutes=(shift_type_doc.allow_check_out_after_shift_end_time)))
					else:
						current_date = frappe.utils.get_datetime(current_date + ' 00:00:00')
						end_date = frappe.utils.get_datetime(end_date + ' 23:59:59')

					outside_duty_checkins = frappe.db.sql("""SELECT *, (@row_number:=@row_number + 1) AS idx
						FROM `tabEmployee Checkin`, (SELECT @row_number:=0) AS temp
						WHERE employee = %(employee)s
						AND DATE(`time`) = %(current_date)s
						AND `time` NOT BETWEEN %(from_date)s AND %(to_date)s
						ORDER BY `time`
					""", {"employee":emp.name, "current_date":outside_duty_date, "from_date":frappe.utils.get_datetime_str(current_date), "to_date":frappe.utils.get_datetime_str(end_date)}, as_dict=1)

					if outside_duty_checkins:
						if len(emp_attendance) and emp_attendance[len(emp_attendance)-1]['checkins']:
							unique_checkins = []
							for checkin in outside_duty_checkins:
								exist = False
								for log in emp_attendance[len(emp_attendance)-1]['checkins']:
									if log.time == checkin.time:
										exist = True
								if not exist:
									unique_checkins.append(checkin)

							outside_duty_checkins = unique_checkins

						if outside_duty_checkins:
							has_chechkins_outside_duty = True

					overtime = [
						{
							'percentage': '100%',
							'hours': overtime_100_hours
						},
						{
							'percentage': '125%',
							'hours': overtime_125_hours
						},
						{
							'percentage': '150%',
							'hours': overtime_150_hours
						},
						{
							'percentage': 'Holiday',
							'hours': overtime_holiday_hours
						},
					]

					emp_attendance.append({
						"emp_name": emp.employee_name,
						"attendance_date": curr_date,
						"att_date_display": att_date_display,
						"attendance_status": "Off",
						"record_status": ('Unresolved' if has_chechkins_outside_duty else ''),
						"has_checkins_outside_duty": has_chechkins_outside_duty,
						"checkins": outside_duty_checkins,
						"overtime": overtime,
						"late_entry": late_entry,
						"early_exit": late_entry,
						"working_hours": working_hours,
						"shift_assignment": "",
						"change_log": []
					})
			
			out.append({"attendance": emp_attendance})
			att_out = frappe._dict()
			for att in emp_attendance:
				att_out.setdefault(att["attendance_date"], att)
			attendance_data.setdefault(emp.name, att_out)

		self.attendance_data = json.dumps(attendance_data, default=str)
		return {"attendance_data": attendance_data}
