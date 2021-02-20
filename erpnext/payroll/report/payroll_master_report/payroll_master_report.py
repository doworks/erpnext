# copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import datetime
from frappe.utils import flt
from erpnext.payroll.doctype.payroll_entry.payroll_entry import get_start_end_dates
from frappe.utils import cint, flt, nowdate, add_days, getdate, fmt_money, add_to_date, DATE_FORMAT, date_diff
from dateutil.relativedelta import relativedelta
from erpnext.accounts.utils import get_fiscal_year
from erpnext.hr.doctype.employee.employee import get_holiday_list_for_employee
from frappe import _
from pprint import pprint
from frappe.model.mapper import get_mapped_doc
from erpnext.hr.doctype.leave_application.leave_application import get_leave_balance_on
from frappe.utils.background_jobs import enqueue

def execute(filters=None):
	if not filters: filters = {}
	globals()['filters'] = filters
	employees = get_employees(filters)
	if not employees: return [], []
	
	columns, earning_types, ded_types = get_columns(employees)
	ss_earning_map = get_ss_earning_map(employees)
	ss_ded_map = get_ss_ded_map(employees)


	data = []
	for emp in employees:
		row = [
			emp.employee_name, 
			emp.cpr, 
			emp.date_of_joining,
			emp.employee_category,
			emp.branch,
			emp.department,
			emp.designation
		]

		#if not emp.branch == None:columns[3] = columns[3].replace('-1','120')
		#if not emp.department  == None: columns[4] = columns[4].replace('-1','120')
		#if not emp.designation  == None: columns[5] = columns[5].replace('-1','120')
		
		gross_pay = 0
		leave_accrual = 0
		accrual_total = 0
		for e in earning_types:
			row.append(ss_earning_map.get(emp.name, {}).get(e))
			gross_pay += flt(ss_earning_map.get(emp.name, {}).get(e))
			if frappe.get_value("Salary Component", {"name":e}, "is_accrual"):
				accrual_total += flt(ss_earning_map.get(emp.name, {}).get(e))

		row += [gross_pay]

		total_deduction = 0
		for d in ded_types:
			row.append(ss_ded_map.get(emp.name, {}).get(d))
			total_deduction += flt(ss_ded_map.get(emp.name, {}).get(d))

		net_pay = flt(gross_pay) - flt(total_deduction)

		row += [total_deduction, net_pay]

		data.append(row)

	#pprint(columns)
	#pprint(data)

	return columns, data

def get_columns(employees):
	"""
	columns = [
		_("Salary Slip ID") + ":Link/Salary Slip:150",_("Employee") + ":Link/Employee:120", _("Employee Name") + "::140", _("Branch") + ":Link/Branch:120",
		_("Department") + ":Link/Department:120", _("Designation") + ":Link/Designation:120",
		_("Company") + ":Link/Company:120", _("Start Date") + "::80", _("End Date") + "::80", _("Leave Without Pay") + ":Float:130",
		_("Payment Days") + ":Float:120"
	]
	"""
	columns = [
		_("Employee") + "::120", 
		_("CPR") + "::80",
		_("Joining Date") + "::80",
		_("Category") + "::80",
		_("Branch") + ":Link/Branch:-1",
		_("Department") + ":Link/Department:-1", 
		_("Designation") + ":Link/Designation:-1"
	]

	structure_components = {_("Earning"): [], _("Deduction"): []}

	for component in frappe.db.sql("""
			select distinct sc.salary_component, sc.type
			from `tabSalary Component` sc
		""", (), as_dict=1):
		structure_components[_(component.type)].append(component.salary_component)

	columns = columns + [(e + ":Currency:120") for e in structure_components[_("Earning")]] + \
		[_("Gross Pay") + ":Currency:120"] + [(d + ":Currency:120") for d in structure_components[_("Deduction")]] + \
		[_("Total Deduction") + ":Currency:120", _("Net Pay") + ":Currency:120"]

	return columns, structure_components[_("Earning")], structure_components[_("Deduction")]

def get_employees(filters):
	filters.update({"to_date": filters.get("to_date"), "employee":filters.get("employee")})
	conditions, filters = get_conditions(filters)

	employees = frappe.db.sql("""select * from `tabEmployee` where %s and `status` = 'Active' order by name""" % conditions, filters, as_dict=1)
	
	return employees or []

def get_conditions(filters):
	conditions = ""

	if filters.get("to_date"): conditions += " date_of_joining <= %(to_date)s"
	if filters.get("employee"): conditions += " and name = %(employee)s"
	if filters.get("branch"): conditions += " and branch = %(branch)s"
	if filters.get("department"): conditions += " and department = %(department)s"
	if filters.get("designation"): conditions += " and designation = %(designation)s"
	if filters.get("company"): conditions += " and company = %(company)s"

	return conditions, filters

def get_ss_earning_map(employees):
	ss_earning_map = {}
	for employee in employees:
		'''First time, load all the components from salary structure'''
		if employee.name:
			emp = get_employee(employee)
			
			if emp:
				if emp[0]:
					if emp[0][2]:
						ssa_doc = frappe.get_doc("Salary Structure Assignment", emp[0][3])

						if ssa_doc.earnings:
							data = get_data_for_eval(employee.name, emp[0][2])
							data.setdefault("end_date", ssa_doc.from_date)

							for key in ('earnings', 'deductions'):
								for struct_row in ssa_doc.get(key):
									amount = eval_condition_and_formula(struct_row, data)
									ss_earning_map.setdefault(employee.name, frappe._dict()).setdefault(struct_row.salary_component, [])
									ss_earning_map[employee.name][struct_row.salary_component] = flt(amount)
						else:
							_salary_structure_doc = frappe.get_doc('Salary Structure', emp[0][2])
							#frappe.msgprint(_salary_structure_doc.name)

							data = get_data_for_eval(employee.name, _salary_structure_doc.name)
							data.setdefault("end_date", ssa_doc.from_date)
							#frappe.msgprint(str(_salary_structure_doc.get('earnings')))

							for key in ('earnings', 'deductions'):
								for struct_row in _salary_structure_doc.get(key):
									amount = eval_condition_and_formula(struct_row, data)
									ss_earning_map.setdefault(employee.name, frappe._dict()).setdefault(struct_row.salary_component, [])
									ss_earning_map[employee.name][struct_row.salary_component] = flt(amount)

	return ss_earning_map

def get_ss_ded_map(employees):
	ss_ded_map = {}
	for employee in employees:
		'''First time, load all the components from salary structure'''
		if employee.name:
			emp = get_employee(employee)
			
			if emp:
				if emp[0]:
					if emp[0][2]:
						ssa_doc = frappe.get_doc("Salary Structure Assignment", emp[0][3])
						#frappe.msgprint()
						if ssa_doc.deductions:
							data = get_data_for_eval(employee.name, emp[0][2])
							data.setdefault("end_date", ssa_doc.from_date)

							for key in ('earnings', 'deductions'):
								for struct_row in ssa_doc.get(key):
									amount = eval_condition_and_formula(struct_row, data)
									ss_ded_map.setdefault(employee.name, frappe._dict()).setdefault(struct_row.salary_component, [])
									ss_ded_map[employee.name][struct_row.salary_component] = flt(amount)
						else:
							_salary_structure_doc = frappe.get_doc('Salary Structure', emp[0][2])
							#frappe.msgprint(_salary_structure_doc.name)

							data = get_data_for_eval(employee.name, _salary_structure_doc.name)
							data.setdefault("end_date", ssa_doc.from_date)
							#frappe.msgprint(str(_salary_structure_doc.get('earnings')))

							for key in ('earnings', 'deductions'):
								for struct_row in _salary_structure_doc.get(key):
									amount = eval_condition_and_formula(struct_row, data)
									ss_ded_map.setdefault(employee.name, frappe._dict()).setdefault(struct_row.salary_component, [])
									ss_ded_map[employee.name][struct_row.salary_component] = flt(amount)

	return ss_ded_map

def eval_condition_and_formula(d, data):
	whitelisted_globals = {
		"int": int,
		"float": float,
		"long": int,
		"round": round,
		"date": datetime.date,
		"getdate": getdate,
		"date_diff": date_diff,
		"str": str
	}

	try:
		condition = d.condition.strip() if d.condition else None
		if hasattr(d, 'abbr'):
			abbr = d.abbr
		else:
			abbr = d.salary_component_abbr
		if condition:
			if not frappe.safe_eval(condition, whitelisted_globals, data):
				return None
		amount = d.amount
		if d.amount_based_on_formula:
			formula = d.formula.strip() if d.formula else None
			if formula:
				amount = frappe.safe_eval(formula, whitelisted_globals, data)
		if amount:
			data[abbr] = amount

		return amount

	except NameError as err:
		frappe.throw(_("Name error: {0}".format(err)))
	except SyntaxError as err:
		frappe.throw(_("Syntax error in formula or condition: {0}".format(err)))
	except Exception as e:
		frappe.throw(_("Error in formula or condition: {0}".format(e)))
		raise
		
def get_data_for_eval(employee, salary_structure):
	'''Returns data for evaluating formula'''
	data = frappe._dict()

	data.update(frappe.get_doc("Salary Structure Assignment",
		{"employee": employee, "salary_structure": salary_structure}).as_dict())

	data.update(frappe.get_doc("Employee", employee).as_dict())
	#data.update(as_dict())

	# set values for components
	salary_components = frappe.get_all("Salary Component")
	for sc in salary_components:
		salary_component = frappe.get_doc('Salary Component', sc.name)
		data.setdefault(salary_component.salary_component_abbr, 0)
		data[salary_component.salary_component_abbr] = salary_component.amount

	return data


def get_employee(employee):
	#Get Employee Structure
	cond = get_filter_condition()
	
	condition = ''

	condition = """and payroll_frequency = '%(payroll_frequency)s'"""% {"payroll_frequency": 'Monthly'}

	sal_struct = frappe.db.sql_list("""
			select
				name from `tabSalary Structure`
			where
				docstatus = 1 and
				is_active = 'Yes'
				and company = %(company)s and
				ifnull(salary_slip_based_on_timesheet,0) = %(salary_slip_based_on_timesheet)s
				{condition}""".format(condition=condition),
			{"company": globals()['filters'].get('company'), "salary_slip_based_on_timesheet": 0})

	if sal_struct:
		cond += "and t2.salary_structure IN %(sal_struct)s "
		cond += "and %(from_date)s >= t2.from_date "
		cond += "and t1.name = %(employee)s "

		emp_list = frappe.db.sql("""
			select 
				distinct t1.name as employee, t1.employee_name, t2.salary_structure as salary_structure_name, t2.name as salary_structure_assignment_name
			from 
				`tabEmployee` t1, `tabSalary Structure Assignment` t2 
			where 
				t1.name = t2.employee 
				and t2.docstatus = 1 
		%s order by t2.from_date desc""" % cond, {"sal_struct": tuple(sal_struct), "from_date": globals()['filters'].get('to_date'), "employee": employee.name})
		
		return emp_list

	return []

def get_filter_condition():
	check_mandatory()

	cond = ''
	for f in ['company']:
		if globals()['filters'].get(f):
			cond += " and t1." + f + " = '" + globals()['filters'].get(f).replace("'", "\'") + "'"

	return cond

def check_mandatory():
	for fieldname in ['company']:
		if not globals()['filters'].get(fieldname):
			frappe.throw(_("Please set {0}").format(fieldname))
