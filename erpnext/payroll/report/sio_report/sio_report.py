# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import _

def execute(filters=None):
	if not filters: filters = {}
	salary_slips = get_salary_slips(filters)
	if not salary_slips: return [], []

	columns, earning_types, ded_types = get_columns(salary_slips)
	ss_earning_map = get_ss_earning_map(salary_slips)
	ss_ded_map = get_ss_ded_map(salary_slips)
	doj_map = get_employee_doj_map()

	data = []
	for ss in salary_slips:
		row = [ss.employee_name, doj_map.get(ss.employee), ss.branch, ss.department, ss.designation]

		if not ss.branch == None:columns[3] = columns[3].replace('-1','120')
		if not ss.department  == None: columns[4] = columns[4].replace('-1','120')
		if not ss.designation  == None: columns[5] = columns[5].replace('-1','120')

		total_earnings = 0
		total_deductions = 0
		row += [ss.net_pay]

		for e in earning_types:
			row.append(ss_earning_map.get(ss.name, {}).get(e))
			total_earnings += flt(ss_earning_map.get(ss.name, {}).get(e))

		for d in ded_types:
			row.append(ss_ded_map.get(ss.name, {}).get(d))
			total_deductions += flt(ss_ded_map.get(ss.name, {}).get(d))

		row += [(total_earnings + total_deductions)]

		data.append(row)

	return columns, data

def get_columns(salary_slips):
	"""
	columns = [
		_("Salary Slip ID") + ":Link/Salary Slip:150",_("Employee") + ":Link/Employee:120", _("Employee Name") + "::140",
		_("Date of Joining") + "::80", _("Branch") + ":Link/Branch:120", _("Department") + ":Link/Department:120",
		_("Designation") + ":Link/Designation:120", _("Company") + ":Link/Company:120", _("Start Date") + "::80",
		_("End Date") + "::80", _("Leave Without Pay") + ":Float:130", _("Payment Days") + ":Float:120"
	]
	"""
	columns = [
		_("Employee Name") + "::140", _("Date of Joining") + "::80", _("Branch") + ":Link/Branch:-1", 
		_("Department") + ":Link/Department:-1", _("Designation") + ":Link/Designation:120"
	]

	salary_components = {_("Earning"): [], _("Deduction"): []}

	for component in frappe.db.sql("""select distinct sd.salary_component, sc.type
		from `tabSalary Detail` sd, `tabSalary Component` sc
		where sc.name=sd.salary_component and
		sd.amount != 0 and sd.parent in (%s) and sc.name in ('Social Insurance - Company Contribution +', 'Social Insurance SIO', 'Unemployment SIO', 'Social Insurance - Company Contribution -')""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1):
		salary_components[_(component.type)].append(component.salary_component)

	columns = columns + [_("Insured Salary") + ":Currency:120"] + [(e + ":Currency:120") for e in salary_components[_("Earning")]] + \
		[(d + ":Currency:120") for d in salary_components[_("Deduction")]] + [_("Total") + ":Currency:120"]

	return columns, salary_components[_("Earning")], salary_components[_("Deduction")]

def get_salary_slips(filters):
	filters.update({"from_date": filters.get("from_date"), "to_date":filters.get("to_date")})
	conditions, filters = get_conditions(filters)
	salary_slips = frappe.db.sql("""select * from `tabSalary Slip` where %s
		order by employee""" % conditions, filters, as_dict=1)

	return salary_slips or []

def get_conditions(filters):

	conditions = "docstatus = 1"

	if filters.get("from_date"): conditions += " and start_date >= %(from_date)s"
	if filters.get("to_date"): conditions += " and end_date <= %(to_date)s"
	if filters.get("branch"): conditions += " and branch = %(branch)s"
	if filters.get("department"): conditions += " and department = %(department)s"
	if filters.get("designation"): conditions += " and designation = %(designation)s"
	if filters.get("company"): conditions += " and company = %(company)s"
	if filters.get("employee"): conditions += " and employee = %(employee)s"

	return conditions, filters

def get_employee_doj_map():
	return	frappe._dict(frappe.db.sql("""
				SELECT
					employee,
					date_of_joining
				FROM `tabEmployee`
				"""))

def get_ss_earning_map(salary_slips):
	ss_earnings = frappe.db.sql("""select parent, salary_component, amount
		from `tabSalary Detail` where parent in (%s) and salary_component in ('Social Insurance - Company Contribution +', 'Social Insurance SIO', 'Unemployment SIO', 'Social Insurance - Company Contribution -')""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

	ss_earning_map = {}
	for d in ss_earnings:
		ss_earning_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
		ss_earning_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_earning_map

def get_ss_ded_map(salary_slips):
	ss_deductions = frappe.db.sql("""select parent, salary_component, amount
		from `tabSalary Detail` where parent in (%s) and salary_component in ('Social Insurance - Company Contribution +', 'Social Insurance SIO', 'Unemployment SIO', 'Social Insurance - Company Contribution -')""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

	ss_ded_map = {}
	for d in ss_deductions:
		ss_ded_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
		ss_ded_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_ded_map
