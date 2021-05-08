from __future__ import unicode_literals, print_function
import frappe
import json
from pprint import pprint
from frappe.utils import flt
import math

@frappe.whitelist()
def get_schedule_records(branch, date_range, start_hour):
    date_range = json.loads(date_range)
    date_list = []
    out = []

    for count in range(frappe.utils.date_diff(date_range[1], date_range[0])+1):
        date_list.append(frappe.utils.add_days(date_range[0], count))

    previous_day = []
    for date in date_list:
        date_records = []
        employees = frappe.db.sql("""SELECT DISTINCT(emp.name), emp.employee_name, emp.holiday_list, emp.designation
            FROM `tabEmployee` emp
            LEFT JOIN `tabEmployee Internal Work History` iwh ON iwh.parent=emp.name
            WHERE iwh.branch = %(branch)s
            AND (%(date)s >= iwh.from_date AND (%(date)s <= iwh.to_date OR iwh.to_date IS NULL))
            ORDER BY designation asc, employee_name asc
        """, {'branch': branch, 'date': date}, as_dict=1)

        emp_string = "'" + "', '".join([emp.name for emp in employees]) + "'"

        hour = start_hour + ':00:00'

        start_date = frappe.utils.get_datetime(date)
        end_date = frappe.utils.add_to_date(start_date, hours=24)

        start_time = frappe.utils.add_to_date(start_date, hours=flt(start_hour))
        end_time = frappe.utils.add_to_date(start_time, hours=flt(24))

        start_time = frappe.utils.datetime.timedelta(hours=start_time.hour, minutes=start_time.minute, seconds=start_time.second, microseconds=start_time.microsecond)
        end_time = frappe.utils.datetime.timedelta(hours=end_time.hour, minutes=end_time.minute, seconds=end_time.second, microseconds=end_time.microsecond)

        start_time = start_date.replace(hour=(start_time.seconds//3600), minute=((start_time.seconds % 3600) // 60), second=(start_time.seconds % 60))
        end_time = end_date.replace(hour=(end_time.seconds//3600), minute=((end_time.seconds % 3600) // 60), second=(end_time.seconds % 60))
        
        records = frappe.db.sql("""SELECT emp.name as emp_doc_name, emp.employee_name as emp_name, emp.designation, shift.name as shift_name, shift.start_time, shift.end_time, shift.in_two_days, shift.split_shift, shift_ass.name as shift_assignment_name, shift_ass.start_date, 'exist' as `status`, shift_ass.notes
            FROM `tabShift Assignment` shift_ass
            LEFT JOIN `tabEmployee` emp ON emp.name = shift_ass.employee
            LEFT JOIN `tabShift Type` shift ON shift.name = shift_ass.shift_type
            WHERE shift_ass.docstatus = 1
            AND emp.name in ({emp_string})
            AND shift_ass.start_date = %(start_date)s
            AND CAST((CONCAT(CAST(shift_ass.start_date as DATE), ' ', CAST(shift.start_time as TIME))) as DATETIME) >= CAST(%(start_time)s as DATETIME)
            AND CAST((CONCAT(CAST(shift_ass.start_date as DATE), ' ', CAST(shift.start_time as TIME))) as DATETIME) <= CAST(%(end_time)s as DATETIME)
            ORDER BY emp.designation asc, emp.employee_name asc
        """.format(emp_string=emp_string), {'start_date': date, 'start_time': frappe.utils.get_datetime_str(start_time), 'end_time': frappe.utils.get_datetime_str(end_time)}, as_dict=1)

        exist = False
        assigned_employees = []
        for record in records:
            assigned_employees.append(record.emp_doc_name)
            split_shifts = frappe._dict()
            if record.split_shift == 1:
                split_shifts = frappe.get_all('Split Shift Item', fields='*', filters={'parent': record.shift_name}, order_by='from_time asc')

            record_start_date = frappe.utils.get_datetime(record.start_date)
            record_end_date = frappe.utils.add_to_date(record_start_date, days=1) if record.in_two_days else record_start_date

            record_start_time = record_start_date.replace(hour=(record.start_time.seconds//3600), minute=((record.start_time.seconds % 3600) // 60), second=(record.start_time.seconds % 60))
            record_end_time = record_end_date.replace(hour=(record.end_time.seconds//3600), minute=((record.end_time.seconds % 3600) // 60), second=(record.end_time.seconds % 60))

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

            next_filled_hours = []
            next_filled_hours_list = []

            for emp in previous_day:
                if emp.employee == record.emp_doc_name and emp.filled_hours:
                    filled_hours = emp.filled_hours
                    filled_hours_list
                previous_day.remove(emp)

            if split_shifts:
                for split_shift in split_shifts:
                    split_start_date = frappe.utils.get_datetime(record.start_date)
                    split_end_date = frappe.utils.add_to_date(split_start_date, days=1) if split_shift.from_time > split_shift.to_time else split_start_date

                    split_start_time = split_start_date.replace(hour=(split_shift.from_time.seconds//3600), minute=((split_shift.from_time.seconds % 3600) // 60), second=(split_shift.from_time.seconds % 60))
                    split_end_time = split_end_date.replace(hour=(split_shift.to_time.seconds//3600), minute=((split_shift.to_time.seconds % 3600) // 60), second=(split_shift.to_time.seconds % 60))

                    split_start_hour = int(split_shift.from_time.seconds//3600)
                    split_start_minute = int((split_shift.from_time.seconds % 3600) // 60)
                    split_end_hour = int(split_shift.to_time.seconds//3600)
                    split_end_minute = int((split_shift.to_time.seconds % 3600) // 60)

                    split_working_hours = abs(frappe.utils.time_diff_in_hours(split_end_time, split_start_time)) if split_end_time > split_start_time else (24 - abs(frappe.utils.time_diff_in_hours(split_end_time, split_start_time)))
                    split_working_hours = math.floor(split_working_hours)
                    
                    for i in range(split_working_hours):
                        current_time = frappe.utils.add_to_date(split_start_time, hours=i)
                        current_hour = int(current_time.hour)
                        current_time = frappe.utils.add_to_date(current_time, minutes=split_start_minute if current_hour == split_start_hour else split_end_minute)
                        current_minute = int(current_time.minute)

                        if current_time >= split_start_time and current_time < split_end_time:
                            if current_time < end_time:
                                hour = current_hour
                                filled_hours_list.append(hour)
                                filled_hours.append({
                                    'hour': hour,
                                    'minute': split_start_minute if current_hour == split_start_hour else split_end_minute,
                                    'is_edge': True if current_hour == split_start_hour or current_hour == split_end_hour or (current_hour == split_end_hour - 1)  else False,
                                    'color': 'lightgreen'
                                })
                            else:
                                hour = current_hour
                                next_filled_hours_list.append(hour)
                                next_filled_hours.append({
                                    'hour': hour,
                                    'minute': split_start_minute if current_hour == split_start_hour else split_end_minute,
                                    'is_edge': True if current_hour == split_start_hour or current_hour == split_end_hour or (current_hour == split_end_hour - 1)  else False,
                                    'color': '#eec490'
                                })
            else:
                shift_hours = abs(frappe.utils.time_diff_in_hours(record_end_time, record_start_time))
                duration_hours = int(shift_hours)#int(working_hours) if int(shift_hours) > int(working_hours) else int(shift_hours)
                if not duration_hours:
                    duration_hours = int(working_hours)

                for i in range(duration_hours):
                    current_time = frappe.utils.add_to_date(record_start_time, hours=i)
                    current_hour = int(current_time.hour)
                    current_time = frappe.utils.add_to_date(current_time, minutes=start_minute if current_hour == record_start_hour else end_minute)
                    current_minute = int(current_time.minute)

                    if current_time >= record_start_time and current_time < record_end_time:
                        if current_time < end_time:
                            hour = current_hour
                            filled_hours_list.append(hour)
                            filled_hours.append({
                                'hour': hour,
                                'minute': start_minute if i == 0 else end_minute,
                                'is_edge': True if i == 0 or i == (int(working_hours) - 1) else False,
                                'color': 'lightgreen'
                            })
                        else:
                            hour = current_hour
                            next_filled_hours_list.append(hour)
                            next_filled_hours.append({
                                'hour': hour,
                                'minute': start_minute if i == 0 else end_minute,
                                'is_edge': True if i == 0 or i == (int(working_hours) - 1) else False,
                                'color': '#eec490'
                            })

            record.setdefault('filled_hours', filled_hours)
            record.setdefault('filled_hours_list', filled_hours_list)

            if next_filled_hours:
                pday = frappe._dict({
                    'date': date,
                    'employee': record.emp_doc_name,
                    'record': record,
                    'filled_hours': next_filled_hours,
                    'filled_hours_list': next_filled_hours_list
                })
                previous_day.append(pday)

            date_records.append(record)
            exist = True

        for emp in employees:
            if emp.name not in assigned_employees:
                on_leave = frappe.get_list("Attendance", fields=['leave_type'], filters=[{"employee": emp.name}, {"status": "On Leave"}, {"attendance_date": date}])

                emp_record = frappe._dict({
                    'emp_doc_name': emp.name,
                    'emp_name': emp.employee_name,
                    'designation': emp.designation,
                    'date': date
                })

                if on_leave:
                    emp_record.setdefault('status', 'on_leave')
                    emp_record.setdefault('leave_type', on_leave[0].leave_type)
                else:
                    holiday = frappe.get_list("Holiday", fields=['description'], filters=[{"parent": emp.holiday_list}, {"holiday_date": date}])
                    
                    if holiday:
                        emp_record.setdefault('status', 'holiday')
                        emp_record.setdefault('holiday_name', holiday[0].description)
                    else:
                        emp_record.setdefault('status', 'not_exist')
                
                for p_emp in previous_day:
                    if p_emp.emp_doc_name == emp.name:
                        diff = frappe.utils.get_datetime(date) - frappe.utils.get_datetime(p_emp.date)
                        if diff.days == 1:
                            emp_record.setdefault('filled_hours', p_emp.filled_hours)
                            emp_record.setdefault('filled_hours_list', p_emp.filled_hours_list)
                            previous_day.remove(p_emp)
                            break

                date_records.append(emp_record)
        
        out.append({
            'date_display': frappe.utils.get_datetime(date).strftime('%A, %-d %B %Y'),
            'records':date_records
        })

    return out

@frappe.whitelist()
def get_schedule_records_1(branch, date_range, start_hour):
    branch_employees = frappe.get_all('Employee', fields=['name', 'employee_name', 'holiday_list', 'designation'],filters={'branch': branch}, order_by='branch asc, designation asc, employee_name asc')
    date_range = json.loads(date_range)
    date_list = []
    out = []

    for count in range(frappe.utils.date_diff(date_range[1], date_range[0])+1):
        date_list.append(frappe.utils.add_days(date_range[0], count))

    emp_string = ""
    if branch_employees:
        emp_string = "'" + "', '".join([emp.name for emp in branch_employees]) + "'"
        
        records = frappe.db.sql("""SELECT emp.name as emp_doc_name, emp.employee_name as emp_name, emp.designation, shift.name as shift_name, shift.start_time, shift.end_time, shift.in_two_days, shift.split_shift, shift_ass.name as shift_assignment_name, shift_ass.start_date, 'exist' as `status`, shift_ass.notes
            FROM `tabShift Assignment` shift_ass
            LEFT JOIN `tabEmployee` emp ON emp.name = shift_ass.employee
            LEFT JOIN `tabShift Type` shift ON shift.name = shift_ass.shift_type
            WHERE shift_ass.docstatus = 1
            AND emp.name in ({emp_string})
            AND shift_ass.start_date >= %(start_date)s
            AND shift_ass.start_date <= %(end_date)s
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

                    record_start_date = frappe.utils.get_datetime(record.start_date)
                    record_end_date = frappe.utils.add_to_date(record_start_date, days=1) if record.in_two_days else record_start_date

                    record_start_time = record_start_date.replace(hour=(record.start_time.seconds//3600), minute=((record.start_time.seconds % 3600) // 60), second=(record.start_time.seconds % 60))
                    record_end_time = record_end_date.replace(hour=(record.end_time.seconds//3600), minute=((record.end_time.seconds % 3600) // 60), second=(record.end_time.seconds % 60))

                    if record.emp_doc_name == emp.name and ((record_start_time >= start_time and record_start_time <= end_time) or (record_end_time >= start_time and record_end_time <= end_time)) and not exist and record_start_date == start_date:
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
                                    split_start_date = frappe.utils.get_datetime(record.start_date)
                                    split_end_date = frappe.utils.add_to_date(split_start_date, days=1) if split_shift.from_time > split_shift.to_time else split_start_date

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
def reschedule(shift_assignment, date, employee, shift_start, shift_end, split_shift, split_shift_start=None, split_shift_end=None, notes=None):
    shift_ass = frappe.get_doc("Shift Assignment", shift_assignment)
    exist_shift = get_exist_shift(shift_start, shift_end, split_shift, split_shift_start, split_shift_end)
    shift_type = ''
    if exist_shift:
        shift_type = exist_shift
    else:
        shift_type = create_new_shift(shift_start, shift_end, split_shift, split_shift_start, split_shift_end)

    shift_ass.shift_type = shift_type
    shift_ass.notes = notes

    shift_ass.save()

    return "Shift Rescheduled Successfully"

@frappe.whitelist()
def schedule(date, employee, shift_start, shift_end, split_shift, split_shift_start=None, split_shift_end=None, notes=None):
    exist_shift = get_exist_shift(shift_start, shift_end, split_shift, split_shift_start, split_shift_end)
    shift_type = ''
    if exist_shift:
        shift_type = exist_shift
    else:
        shift_type = create_new_shift(shift_start, shift_end, split_shift, split_shift_start, split_shift_end)

    new_doc = frappe.new_doc("Shift Assignment")
    new_doc.date = date
    new_doc.start_date = date
    new_doc.end_date = frappe.utils.add_to_date(date, days=1)
    new_doc.employee = employee
    new_doc.shift_type = shift_type
    new_doc.notes = notes
    new_doc.save()
    new_doc.submit()

    return "Shift Assigned Successfully"

def get_exist_shift(shift_start, shift_end, split_shift, split_shift_start=None, split_shift_end=None):
    if int(split_shift):
        shift_type = frappe.db.sql("""SELECT st.name
            FROM `tabShift Type` st
            WHERE
            CAST(start_time as TIME)  = CAST('{start_time}' as TIME)
            AND CAST(end_time as TIME)  = CAST('{end_time}' as TIME)
            AND split_shift = 1
        """.format(start_time=shift_start, end_time=split_shift_end), as_dict=1)
        for shift in shift_type:
            shift_doc = frappe.get_doc('Shift Type', shift.name)
            split_shifts = shift_doc.split_shifts
            sstart = frappe.utils.get_datetime(shift_start)
            send = frappe.utils.get_datetime(shift_end)
            ssstart = frappe.utils.get_datetime(split_shift_start)
            ssend = frappe.utils.get_datetime(split_shift_end)
            if shift_doc.split_shifts[0].from_time.seconds == ((sstart.hour * 3600) + (sstart.minute * 60)) and shift_doc.split_shifts[0].to_time.seconds == ((send.hour * 3600) + (send.minute * 60)) and shift_doc.split_shifts[1].from_time.seconds == ((ssstart.hour * 3600) + (ssstart.minute * 60)) and shift_doc.split_shifts[1].to_time.seconds == ((ssend.hour * 3600) + (ssend.minute * 60)):
                return shift.name
        return None
    else:
        shift_type = frappe.db.sql("""SELECT st.name
            FROM `tabShift Type` st
            WHERE CAST(start_time as TIME) = CAST('{start_time}' as TIME)
            AND CAST(end_time as TIME) = CAST('{end_time}' as TIME)
            AND split_shift = 0
        """.format(start_time=shift_start, end_time=shift_end), as_dict=1)
        return shift_type[0].name if shift_type else None

def create_new_shift(shift_start, shift_end, split_shift, split_shift_start=None, split_shift_end=None):
    new_st = frappe.new_doc('Shift Type')
    

    new_st.start_time = shift_start
    new_st.end_time = split_shift_end if int(split_shift) else shift_end
    
    new_name = ''
    if int(split_shift):
        values = shift_start.split(':')
        start_hours = int(values[0])
        start_minutes = int(values[1])
        values = shift_end.split(':')
        end_hours = int(values[0])
        end_minutes = int(values[1])
        values = split_shift_start.split(':')
        split_start_hours = int(values[0])
        split_start_minutes = int(values[1])
        values = split_shift_end.split(':')
        split_end_hours = int(values[0])
        split_end_minutes = int(values[1])
        new_name = str(start_hours+(round(start_minutes/60,2) if start_minutes else 0)) + '-' + str(end_hours+(round(end_minutes/60,2) if end_minutes else 0)) + ' ' + str(split_start_hours+(round(split_start_minutes/60,2) if split_start_minutes else 0)) + '-' + str(split_end_hours+(round(split_end_minutes/60,2) if split_end_minutes else 0))
    else:
        values = shift_start.split(':')
        start_hours = int(values[0])
        start_minutes = int(values[1])
        values = shift_end.split(':')
        end_hours = int(values[0])
        end_minutes = int(values[1])
        new_name = str(start_hours+(round(start_minutes/60,2) if start_minutes else 0)) + '-' + str(end_hours+(round(end_minutes/60,2) if end_minutes else 0))

    new_st.name = new_name
    new_st.shift_abbreviation = new_name

    new_st.split_shift = split_shift
    if int(split_shift):
        first = new_st.append('split_shifts')
        first.from_time = shift_start
        first.to_time = shift_end
        second = new_st.append('split_shifts')
        second.from_time = split_shift_start
        second.to_time = split_shift_end
    new_st.enable_auto_attendance = 1
    if new_st.end_time <= new_st.start_time:
        new_st.in_two_days = 1

    gss = frappe.get_single("General Shift Settings")
    new_st.holiday_list = gss.holiday_list
    new_st.determine_check_in_and_check_out = gss.determine_check_in_and_check_out
    new_st.working_hours_threshold_for_half_day = gss.working_hours_threshold_for_half_day
    new_st.working_hours_threshold_for_absent = gss.working_hours_threshold_for_absent
    new_st.working_hours_calculation_based_on = gss.working_hours_calculation_based_on
    new_st.begin_check_in_before_shift_start_time = gss.begin_check_in_before_shift_start_time
    new_st.allow_check_out_after_shift_end_time = gss.allow_check_out_after_shift_end_time
    new_st.enable_entry_grace_period = gss.enable_entry_grace_period
    new_st.late_entry_grace_period = gss.late_entry_grace_period
    new_st.enable_exit_grace_period = gss.enable_exit_grace_period
    new_st.early_exit_grace_period = gss.early_exit_grace_period
    new_st.late_component = gss.late_component
    new_st.late_calculation_formula = gss.late_calculation_formula
    new_st.overtime_125_component = gss.overtime_125_component
    new_st.overtime_125_formula = gss.overtime_125_formula
    new_st.overtime_150_component = gss.overtime_150_component
    new_st.overtime_150_formula = gss.overtime_150_formula
    new_st.overtime_200_component = gss.overtime_200_component
    new_st.overtime_200_formula = gss.overtime_200_formula
    new_st.has_shift_allowance = gss.has_shift_allowance
    new_st.shift_allowance_component = gss.shift_allowance_component
    new_st.shift_allowance_formula = gss.shift_allowance_formula

    new_st.save()
    return new_st.name

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
        new_doc.start_date = date
        new_doc.end_date = frappe.utils.add_to_date(date, days=1)
        new_doc.shift_type = shift_type
        
        new_doc.save()
        new_doc.submit()

    return "Shift Cloned Successfully"