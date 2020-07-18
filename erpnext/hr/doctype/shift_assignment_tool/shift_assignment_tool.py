# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import date_diff, add_days

class ShiftAssignmentTool(Document):
	def generate_shift_pattern_view(self):
		self.set("shift_pattern_view", []);
		
		days = date_diff(self.to_date, self.from_date) + 1

		shift_pattern = frappe.get_doc("Shift Pattern", self.shift_pattern)
		
		current_shift = 0
		if shift_pattern.unit_of_cycle == "Day":
			current_shift = self.start_from_day or 1
			current_shift -= 1
		elif shift_pattern.unit_of_cycle == "Week":
			current_shift = int(frappe.utils.get_datetime(self.from_date).weekday())
			current_shift += 1
			current_shift = 0 if current_shift == 7 else current_shift

		pattern_days = list(shift_pattern.shift_pattern)

		for day in range(days):
			row = self.append("shift_pattern_view")
			row.date = add_days(self.from_date, day)
			row.shift_type = pattern_days[current_shift].shift_type
			current_shift += 1
			if current_shift == len(pattern_days):
				current_shift = 0
		
	def assign_shifts(self):
		for employee in self.employees:
			for row in self.shift_pattern_view:
				if row.shift_type:
					assignment_doc = frappe.new_doc("Shift Assignment")
					assignment_doc.company = self.company
					assignment_doc.shift_type = row.shift_type
					assignment_doc.employee = employee.employee
					assignment_doc.date = row.date
					assignment_doc.insert()
					assignment_doc.submit()