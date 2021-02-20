from __future__ import unicode_literals, print_function
import frappe
import json
from pprint import pprint
from frappe.utils import flt

@frappe.whitelist()
def get_schedule_records(branch, date_range, start_hour):
    branch_employees = frappe.get_all('Employee', fields=['name', 'employee_name', 'holiday_list', 'designation'],filters={'branch': branch}, order_by='branch asc, designation asc, employee_name asc')
    date_range = json.loads(date_range)
    date_list = []
    out = []

    for count in range(frappe.utils.date_diff(date_range[1], date_range[0])+1):
        date_list.append(frappe.utils.add_days(date_range[0], count))

    emp_string = ""
    if branch_employees:
        emp_string = "'" + "', '".join([emp.name for emp in branch_employees]) + "'"
        
        records = frappe.db.sql("""SELECT emp.name as emp_doc_name, emp.employee_name as emp_name, emp.designation, shift.name as shift_name, shift.start_time, shift.end_time, shift.in_two_days, shift.split_shift, shift_ass.name as shift_assignment_name, shift_ass.date, 'exist' as `status`
            FROM `tabShift Assignment` shift_ass
            LEFT JOIN `tabEmployee` emp ON emp.name = shift_ass.employee
            LEFT JOIN `tabShift Type` shift ON shift.name = shift_ass.shift_type
            WHERE shift_ass.docstatus = 1
            AND emp.name in ({emp_string})
            AND shift_ass.date >= %(start_date)s
            AND shift_ass.date <= %(end_date)s
            ORDER BY emp.designation asc, emp.employee_name asc
        """.format(emp_string=emp_string), {'start_date': date_range[0], 'end_date': date_range[1]}, as_dict=1)

        for date in date_list:
            date_records = []
            start_date = frappe.utils.get_datetime(date)
            end_date = frappe.utils.add_to_date(start_date, hours=24)

            start_time = frappe.utils.add_to_date(start_date, hours=flt(start_hour))
            ##end_hour = flt(start_hour) + flt(24)
            end_hour = flt(24)
            end_time = frappe.utils.add_to_date(start_time, hours=end_hour)

            start_time = frappe.utils.datetime.timedelta(hours=start_time.hour, minutes=start_time.minute, seconds=start_time.second, microseconds=start_time.microsecond)
            end_time = frappe.utils.datetime.timedelta(hours=end_time.hour, minutes=end_time.minute, seconds=end_time.second, microseconds=end_time.microsecond)

            start_time = start_date.replace(hour=(start_time.seconds//3600), minute=((start_time.seconds % 3600) // 60), second=(start_time.seconds % 60))
            end_time = end_date.replace(hour=(end_time.seconds//3600), minute=((end_time.seconds % 3600) // 60), second=(end_time.seconds % 60))

            for emp in branch_employees:
                exist = False
                for record in records:
                    split_shifts = frappe._dict()
                    if record.split_shift == 1:
                        split_shifts = frappe.get_all('Split Shift Item', fields='*', filters={'parent': record.shift_name}, order_by='from_time asc')

                    record_start_date = frappe.utils.get_datetime(record.date)
                    record_end_date = frappe.utils.add_to_date(record_start_date, days=1) if record.in_two_days else record_start_date

                    record_start_time = record_start_date.replace(hour=(record.start_time.seconds//3600), minute=((record.start_time.seconds % 3600) // 60), second=(record.start_time.seconds % 60))
                    record_end_time = record_end_date.replace(hour=(record.end_time.seconds//3600), minute=((record.end_time.seconds % 3600) // 60), second=(record.end_time.seconds % 60))

                    if record.emp_doc_name == emp.name and ((record_start_time >= start_time and record_start_time <= end_time) or (record_end_time >= start_time and record_end_time <= end_time)) and not exist:
                        record_start_hour = int(record.start_time.seconds//3600)
                        record.setdefault('start_hour', record_start_hour)
                        start_minute = int((record.start_time.seconds % 3600) // 60)
                        record.setdefault('start_minute', start_minute)
                        record_end_hour = int(record.end_time.seconds//3600)
                        record.setdefault('end_hour', record_end_hour)
                        end_minute = int((record.end_time.seconds % 3600) // 60)
                        record.setdefault('end_minute', end_minute)
                        working_hours = abs(frappe.utils.time_diff_in_hours(record_end_time, record_start_time))
                        record.setdefault('working_hours', working_hours)
                        
                        filled_hours = []
                        filled_hours_list = []
                        shift_hours = abs(frappe.utils.time_diff_in_hours(end_time, record_start_time))
                        duration_hours = int(working_hours) if int(shift_hours) > int(working_hours) else int(shift_hours)
                        if not duration_hours:
                            duration_hours = int(working_hours)

                        current_time = record_start_time
                        
                        for i in range(duration_hours):
                            current_time = frappe.utils.add_to_date(record_start_time, hours=i)
                            current_hour = int(current_time.hour)
                            if split_shifts:
                                for split_shift in split_shifts:
                                    split_start_date = frappe.utils.get_datetime(record.date)
                                    split_end_date = frappe.utils.add_to_date(split_start_date, days=1) if record.in_two_days else split_start_date

                                    split_start_time = split_start_date.replace(hour=(split_shift.from_time.seconds//3600), minute=((split_shift.from_time.seconds % 3600) // 60), second=(split_shift.from_time.seconds % 60))
                                    split_end_time = split_end_date.replace(hour=(split_shift.to_time.seconds//3600), minute=((split_shift.to_time.seconds % 3600) // 60), second=(split_shift.to_time.seconds % 60))

                                    split_start_hour = int(split_shift.from_time.seconds//3600)
                                    split_start_minute = int((split_shift.from_time.seconds % 3600) // 60)
                                    split_end_hour = int(split_shift.to_time.seconds//3600)
                                    split_end_minute = int((split_shift.to_time.seconds % 3600) // 60)


                                    

                                    split_working_hours = abs(frappe.utils.time_diff_in_hours(split_end_time, split_start_time))

                                    if current_time >= split_start_time and current_time < split_end_time and split_shift.idx < len(split_shifts):
                                        hour = current_hour
                                        hour = abs(24 - hour) if hour >= 24 else hour
                                        filled_hours_list.append(hour)
                                        filled_hours.append({
                                            'hour': hour,
                                            'minute': split_start_minute if current_hour == split_start_hour else split_end_minute,
                                            'is_edge': True if current_hour == split_start_hour or current_hour == split_end_hour or (current_hour == split_end_hour - 1)  else False
                                        })
                                    elif current_time >= split_start_time and current_time <= split_end_time and split_shift.idx == len(split_shifts):
                                        hour = current_hour
                                        hour = abs(24 - hour) if hour >= 24 else hour
                                        filled_hours_list.append(hour)
                                        filled_hours.append({
                                            'hour': hour,
                                            'minute': split_start_minute if current_hour == split_start_hour else split_end_minute,
                                            'is_edge': True if current_hour == split_start_hour or current_hour == split_end_hour or (current_hour == split_end_hour - 1 and split_end_hour == record_end_hour)  else False
                                        })
                            else:
                                hour = record_start_hour + i
                                hour = abs(24 - hour) if hour >= 24 else hour
                                filled_hours_list.append(hour)
                                filled_hours.append({
                                    'hour': hour,
                                    'minute': start_minute if i == 0 else end_minute,
                                    'is_edge': True if i == 0 or i == (int(working_hours) - 1) else False
                                })

                        record.setdefault('filled_hours', filled_hours)
                        record.setdefault('filled_hours_list', filled_hours_list)

                        date_records.append(record)
                        exist = True
            
                if not exist:
                    on_leave = frappe.get_list("Attendance", fields=['leave_type'], filters=[{"employee": emp.name}, {"status": "On Leave"}, {"attendance_date": date}])

                    if on_leave:
                        date_records.append({
                            'emp_doc_name': emp.name,
                            'emp_name': emp.employee_name,
                            'designation': emp.designation,
                            'status': 'on_leave',
                            'leave_type': on_leave[0].leave_type,
                            'date': date
                        })
                    else:
                        holiday = frappe.get_list("Holiday", fields=['description'], filters=[{"parent": emp.holiday_list}, {"holiday_date": date}])
                        
                        if holiday:
                            date_records.append({
                                'emp_doc_name': emp.name,
                                'emp_name': emp.employee_name,
                                'designation': emp.designation,
                                'status': 'holiday',
                                'holiday_name': holiday[0].description,
                                'date': date
                            })
                        else:
                            date_records.append({
                                'emp_doc_name': emp.name,
                                'emp_name': emp.employee_name,
                                'designation': emp.designation,
                                'status': 'not_exist',
                                'date': date
                            })
            
            out.append({
                'date_display': frappe.utils.get_datetime(date).strftime('%A, %-d %B %Y'),
                'records':date_records
            })

    return out

@frappe.whitelist()
def reschedule(shift_assignment, shift_type):
    old_doc = frappe.get_doc("Shift Assignment", shift_assignment)
    old_doc.cancel()
    new_doc = frappe.copy_doc(frappe.get_doc("Shift Assignment", shift_assignment))
    new_doc.shift_type = shift_type
    new_doc.amended_from = old_doc.name
    new_doc.save()
    new_doc.submit()

    return "Shift Rescheduled Successfully"

@frappe.whitelist()
def schedule(date, employee, shift_type):
    new_doc = frappe.new_doc("Shift Assignment")
    new_doc.date = date
    new_doc.employee = employee
    new_doc.shift_type = shift_type
    new_doc.save()
    new_doc.submit()

    return "Shift Assigned Successfully"

@frappe.whitelist()
def cancel_shift_assignment(shift_assignment):
    old_doc = frappe.get_doc("Shift Assignment", shift_assignment)
    old_doc.cancel()

    return "Shift Cancelled Successfully"

@frappe.whitelist()
def clone_schedule(date_range, employee, shift_type):
    date_range = json.loads(date_range)
    date_list = []

    for count in range(frappe.utils.date_diff(date_range[1], date_range[0])+1):
        date_list.append(frappe.utils.add_days(date_range[0], count))

    for date in date_list:
        new_doc = frappe.new_doc('Shift Assignment')
        if frappe.db.exists("Shift Assignment", {"employee": employee, "date": date}):
            old_doc_name = frappe.get_all("Shift Assignment", fields='name', filters={"employee": employee, "date": date})
            old_doc = frappe.get_doc('Shift Assignment', old_doc_name[0].name)
            new_doc.amended_from = old_doc.name
            old_doc.cancel()

        new_doc.employee = employee
        new_doc.date = date
        new_doc.shift_type = shift_type
        
        new_doc.save()
        new_doc.submit()

    return "Shift Cloned Successfully"