# -*- coding: utf-8 -*-
# Copyright (c) 2020, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class AttendanceApproval(Document):
	def get_employees_attendance(self):
		out = frappe._dict()
		employees = frappe.get_list("Employee", fields=["name", "employee_name"], filters={"branch": self.branch})
		for emp in employees:
			attendance_list = frappe.get_list("Attendance", fields='*', filters=[{"employee": emp.name}, {"attendance_date": ('>=', self.from_date)}, {"attendance_date": ('<=', self.to_date)}])
			out.setdefault(emp.name, {"attendance": attendance_list, "employee": emp})


		return out
