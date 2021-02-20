# -*- coding: utf-8 -*-
# Copyright (c) 2018, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import getdate, flt, cint, cstr, date_diff
from frappe.model.document import Document
import datetime
from frappe.model.mapper import get_mapped_doc

class DuplicateAssignment(frappe.ValidationError): pass

class SalaryStructureAssignment(Document):
	def validate(self):
		self.validate_dates()
		self.validate_income_tax_slab()
		self.set_payroll_payable_account()

	def validate_dates(self):
		joining_date, relieving_date = frappe.db.get_value("Employee", self.employee,
			["date_of_joining", "relieving_date"])

		if self.from_date:
			if frappe.db.exists("Salary Structure Assignment", {"employee": self.employee, "from_date": self.from_date, "docstatus": 1}):
				frappe.throw(_("Salary Structure Assignment for Employee already exists"), DuplicateAssignment)

			if joining_date and getdate(self.from_date) < joining_date:
				frappe.throw(_("From Date {0} cannot be before employee's joining Date {1}")
					.format(self.from_date, joining_date))

			# flag - old_employee is for migrating the old employees data via patch
			if relieving_date and getdate(self.from_date) > relieving_date and not self.flags.old_employee:
				frappe.throw(_("From Date {0} cannot be after employee's relieving Date {1}")
					.format(self.from_date, relieving_date))

	def get_salary_structure_details(self):
		salary_structure = frappe.get_doc("Salary Structure", self.salary_structure)

		earnings = []
		deductions = []

		self.earnings = salary_structure.earnings
		self.deductions = salary_structure.deductions
		self.calculate_totals()

	def calculate_totals(self):
		#Get Salary Structure
		_salary_structure_doc = frappe.get_doc('Salary Structure', self.salary_structure)

		#Get Data for Evaluation
		data = self.get_data_for_eval()
		data.setdefault("end_date", frappe.utils.nowdate())
		data.update(frappe.get_doc("Employee", self.employee).as_dict())

		#Define Totals
		total_earning = 0
		total_deduction = 0

		#Evaluate Components
		for component in self.earnings:
			amount = self.eval_condition_and_formula(component, data)
			component.amount = flt(amount)
			if not component.statistical_component:
				total_earning += flt(amount)

		for component in self.deductions:
			amount = self.eval_condition_and_formula(component, data)
			component.amount = flt(amount)
			if not component.statistical_component:
				total_deduction += flt(amount)

		net_pay = total_earning - total_deduction

		self.total_earning = total_earning
		self.total_deduction = total_deduction
		self.net_pay = net_pay
	
	def get_data_for_eval(self):
		'''Returns data for evaluating formula'''
		data = frappe._dict()
		data.update(self.as_dict())

		# set values for components
		for sc in self.earnings:
			if str(sc.formula).lower() == 'base':
				data.setdefault(sc.abbr, 0)
				data[sc.abbr] = self.base
			else:
				data.setdefault(sc.abbr, 0)
				data[sc.abbr] = sc.amount

		for sc in self.deductions:
			data.setdefault(sc.abbr, 0)
			data[sc.abbr] = sc.amount

		return data

	def eval_condition_and_formula(self, d, data):
		whitelisted_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"getdate": getdate,
			"date": datetime.date,
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
	def validate_income_tax_slab(self):
		if not self.income_tax_slab:
			return
		
		income_tax_slab_currency = frappe.db.get_value('Income Tax Slab', self.income_tax_slab, 'currency')
		if self.currency != income_tax_slab_currency:
			frappe.throw(_("Currency of selected Income Tax Slab should be {0} instead of {1}").format(self.currency, income_tax_slab_currency))

	def set_payroll_payable_account(self):
		if not self.payroll_payable_account:
			payroll_payable_account = frappe.db.get_value('Company', self.company, 'default_payroll_payable_account')
			if not payroll_payable_account:
				payroll_payable_account = frappe.db.get_value(
					"Account", {
						"account_name": _("Payroll Payable"), "company": self.company, "account_currency": frappe.db.get_value(
							"Company", self.company, "default_currency"), "is_group": 0})
			self.payroll_payable_account = payroll_payable_account

def get_assigned_salary_structure(employee, on_date):
	if not employee or not on_date:
		return None
	salary_structure = frappe.db.sql("""
		select salary_structure from `tabSalary Structure Assignment`
		where employee=%(employee)s
		and docstatus = 1
		and %(on_date)s >= from_date order by from_date desc limit 1""", {
			'employee': employee,
			'on_date': on_date,
		})
	return salary_structure[0][0] if salary_structure else None

@frappe.whitelist()
def make_salary_slip(source_name, target_doc = None, employee = None, as_print = False, print_format = None, for_preview=0, ignore_permissions=False):
	def postprocess(source, target):
		if employee:
			employee_details = frappe.db.get_value("Employee", employee,
				["employee_name", "branch", "designation", "department", "payroll_cost_center"], as_dict=1)
			target.employee = employee
			target.employee_name = employee_details.employee_name
			target.branch = employee_details.branch
			target.designation = employee_details.designation
			target.department = employee_details.department
			target.payroll_cost_center = employee_details.payroll_cost_center
			if not target.payroll_cost_center and target.department:
				target.payroll_cost_center = frappe.db.get_value("Department", target.department, "payroll_cost_center")

		target.run_method('process_salary_structure', for_preview=for_preview)

	doc = get_mapped_doc("Salary Structure Assignment", source_name, {
		"Salary Structure Assignment": {
			"doctype": "Salary Slip",
			"field_map": {
				"total_earning": "gross_pay",
				"name": "salary_structure_assignment"
			}
		}
	}, target_doc, postprocess, ignore_child_tables=True, ignore_permissions=ignore_permissions)

	if cint(as_print):
		doc.name = 'Preview for {0}'.format(employee)
		return frappe.get_print(doc.doctype, doc.name, doc = doc, print_format = print_format)
	else:
		return doc

@frappe.whitelist()
def get_salary_structure_details(salary_structure):
    ss_doc = frappe.get_doc("Salary Structure", salary_structure)

    earnings = []
    deductions = []

    for earning in ss_doc.earnings:
        earnings.append(earning)

    for deduction in ss_doc.deductions:
        deductions.append(deduction)

    return frappe._dict({"earnings": earnings, "deductions": deductions})
    return frappe._dict({"earnings": earnings, "deductions": deductions})
