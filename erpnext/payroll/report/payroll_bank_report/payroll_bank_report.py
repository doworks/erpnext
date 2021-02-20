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

	columns = get_columns(salary_slips)

	data = []
	for ss in salary_slips:
		row = [ss.employee, ss.employee_name, ss.bank, ss.iban, ss.account_no, ss.net_pay]

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
		_("Employee") + ":Link/Employee:120", _("Employee Name") + "::140",
		_("Bank") + "::80", _("IBAN") + "::120", _("Account No") + "::120",
		_("Net Salary") + ":Currency:120"
	]

	return columns

def get_salary_slips(filters):
	filters.update({"from_date": filters.get("from_date"), "to_date":filters.get("to_date")})
	conditions, filters = get_conditions(filters)
	salary_slips = frappe.db.sql("""select ss.*, emp.bank_name as bank, emp.iban as iban, emp.bank_ac_no as account_no 
		from `tabSalary Slip` ss
		LEFT JOIN `tabEmployee` emp ON emp.name = ss.employee
		where %s
		order by employee""" % conditions, filters, as_dict=1, debug=True)

	return salary_slips or []

def get_conditions(filters):
	conditions = ""

	conditions += "ss.docstatus = 1"

	if filters.get("from_date"): conditions += " and ss.start_date >= %(from_date)s"
	if filters.get("to_date"): conditions += " and ss.end_date <= %(to_date)s"
	if filters.get("branch"): conditions += " and emp.branch = %(branch)s"
	if filters.get("department"): conditions += " and emp.department = %(department)s"
	if filters.get("designation"): conditions += " and emp.designation = %(designation)s"
	if filters.get("company"): conditions += " and ss.company = %(company)s"
	if filters.get("employee"): conditions += " and ss.employee = %(employee)s"

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
		from `tabSalary Detail` where parent in (%s)""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

	ss_earning_map = {}
	for d in ss_earnings:
		ss_earning_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
		ss_earning_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_earning_map

def get_ss_ded_map(salary_slips):
	ss_deductions = frappe.db.sql("""select parent, salary_component, amount
		from `tabSalary Detail` where parent in (%s)""" %
		(', '.join(['%s']*len(salary_slips))), tuple([d.name for d in salary_slips]), as_dict=1)

	ss_ded_map = {}
	for d in ss_deductions:
		ss_ded_map.setdefault(d.parent, frappe._dict()).setdefault(d.salary_component, [])
		ss_ded_map[d.parent][d.salary_component] = flt(d.amount)

	return ss_ded_map
