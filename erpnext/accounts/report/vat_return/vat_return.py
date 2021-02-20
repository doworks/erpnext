# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt
from frappe import msgprint, _
from frappe.model.meta import get_field_precision
from erpnext import get_default_company
from erpnext.controllers.taxes_and_totals import get_itemised_tax
from pprint import pprint

def execute(filters):
	if not filters: filters = frappe._dict({})
	filters.setdefault('company', get_default_company())
	sales_template = frappe.get_doc('Sales Taxes and Charges Template', frappe.db.get_single_value('VAT Return Settings', 'sales_taxes_and_charges_template'))
	purchase_template = frappe.get_doc('Purchase Taxes and Charges Template', frappe.db.get_single_value('VAT Return Settings', 'purchase_taxes_and_charges_template'))

	columns = []
	data = []
	report_summary = []
	skip_total_row = 0

	if filters.report_type == 'Summary' and sales_template:
		skip_total_row = 1
		columns, data, report_summary = get_summary(filters, sales_template, purchase_template)
	elif filters.report_type == '1 Standard Rated Sales' and sales_template:
		columns, data, total_net_amount, total_vat_amount = get_standard_rated_sales(filters, sales_template)
	elif filters.report_type == '4 Zero Rated Domestic Sales' and sales_template:
		columns, data, total_net_amount, total_vat_amount = get_zero_rated_domestic_sales(filters, sales_template)
	elif filters.report_type == '5 Exports' and sales_template:
		columns, data, total_net_amount, total_vat_amount = get_exports_sales(filters, sales_template)
	elif filters.report_type == '8 Standard Rated Domestic Purchases' and purchase_template:
		columns, data, total_net_amount, total_vat_amount = get_standard_rated_purchases(filters, purchase_template)
	elif filters.report_type == '9 Imports' and purchase_template:
		columns, data, total_net_amount, total_vat_amount = get_imports_purchases(filters, purchase_template)
	elif filters.report_type == '12 Zero Rated Domesitc Purchases' and purchase_template:
		columns, data, total_net_amount, total_vat_amount = get_zero_rated_domestic_purchases(filters, purchase_template)
	
	return columns, data, [], [], report_summary, skip_total_row

def get_summary(filters, sales_template, purchase_template):
	columns = get_summary_columns()
	data = []
	report_summary = []
	total_sales_amount = 0
	total_sales_vat = 0
	total_purchase_amount = 0
	total_purchase_vat = 0

	if sales_template:
		column, result, total_net_amount, total_vat_amount = get_standard_rated_sales(filters, sales_template)
		total_sales_amount += total_net_amount
		total_sales_vat += total_vat_amount
		data.append({
			'no': '1',
			'description': 'Standard Rates Sales',
			'amount': total_net_amount,
			'vat_amount': total_vat_amount
		})
		data.append({
			'no': '2',
			'description': 'Sales to registered VAT payers in other GCC States',
			'amount': 0,
			'vat_amount': 0
		})
		data.append({
			'no': '3',
			'description': 'Sales subject to domestic reverse charge mechanism',
			'amount': 0,
			'vat_amount': 0
		})

		column, result, total_net_amount, total_vat_amount = get_zero_rated_domestic_sales(filters, sales_template)
		total_sales_amount += total_net_amount
		total_sales_vat += total_vat_amount
		data.append({
			'no': '4',
			'description': 'Zero Rated Domestic Sales',
			'amount': total_net_amount,
			'vat_amount': total_vat_amount
		})

		column, result, total_net_amount, total_vat_amount = get_exports_sales(filters, sales_template)
		total_sales_amount += total_net_amount
		total_sales_vat += total_vat_amount
		data.append({
			'no': '5',
			'description': 'Exports',
			'amount': total_net_amount,
			'vat_amount': total_vat_amount
		})
		data.append({
			'no': '6',
			'description': 'Exempt sales',
			'amount': 0,
			'vat_amount': 0
		})
		data.append({
			'no': '7',
			'description': 'Total Sales',
			'amount': total_sales_amount,
			'vat_amount': total_sales_vat
		})
	
	if purchase_template:
		column, result, total_net_amount, total_vat_amount = get_standard_rated_purchases(filters, purchase_template)
		total_purchase_amount += total_net_amount
		total_purchase_vat += total_vat_amount
		data.append({
			'no': '8',
			'description': 'Standard Rated Domestic Purchases',
			'amount': total_net_amount,
			'vat_amount': total_vat_amount
		})

		column, result, total_net_amount, total_vat_amount = get_imports_purchases(filters, purchase_template)
		total_purchase_amount += total_net_amount
		total_purchase_vat += total_vat_amount
		data.append({
			'no': '9',
			'description': 'Imports subject to VAT either paid at customs or deferred',
			'amount': total_net_amount,
			'vat_amount': total_vat_amount
		})
		data.append({
			'no': '10',
			'description': 'Imports subject to VAT accounted for through reverse charge mechanism',
			'amount': 0,
			'vat_amount': 0
		})
		data.append({
			'no': '11',
			'description': 'Purchases subject to domestic reverse charge mechanism',
			'amount': 0,
			'vat_amount': 0
		})

		column, result, total_net_amount, total_vat_amount = get_zero_rated_domestic_purchases(filters, purchase_template)
		total_purchase_amount += total_net_amount
		total_purchase_vat += total_vat_amount
		data.append({
			'no': '12',
			'description': 'Purchases from non-registered suppliers, zero-rated / exempt purchases',
			'amount': total_net_amount,
			'vat_amount': total_vat_amount
		})

		data.append({
			'no': '13',
			'description': 'Total Purchases',
			'amount': total_purchase_amount,
			'vat_amount': total_purchase_vat
		})

	data.append({
		'no': '14',
		'description': 'Total VAT due for current period',
		'amount': 0,
		'vat_amount': flt(total_sales_vat - total_purchase_vat)
	})

	data.append({
		'no': '15',
		'description': 'Corrections from previous period (between BHD +/- 5,000)',
		'amount': 0,
		'vat_amount': 0
	})

	data.append({
		'no': '16',
		'description': 'VAT credit  carried forward from previous period(s)',
		'amount': 0,
		'vat_amount': 0
	})

	data.append({
		'no': '17',
		'description': 'Net VAT due (or reclaimed)',
		'amount': 0,
		'vat_amount': flt(total_sales_vat - total_purchase_vat)
	})


	return columns, data, report_summary

def get_standard_rated_sales(filters, sales_template):
	columns = get_1_columns()

	vat_payable_account = sales_template.taxes[0].account_head
	vat_rate = sales_template.taxes[0].rate

	filters.setdefault('vat_account', vat_payable_account)

	data = []
	select_fields = """, gle.debit, gle.credit, gle.debit_in_account_currency,
		gle.credit_in_account_currency as vat_amount, (gle.credit_in_account_currency * {}) as net_total, 
		'{}' as vat, (gle.credit_in_account_currency + (gle.credit_in_account_currency * {})) as total_amount_incl_vat """.format((100/flt(vat_rate)), vat_rate, (100/flt(vat_rate)))

	conditions = []
	conditions.append("(gle.posting_date >=%(from_date)s and gle.posting_date <=%(to_date)s)")
	conditions.append("gle.is_cancelled = 0")
	conditions.append("gle.credit_in_account_currency > 0")
	conditions.append("customer.territory in ('All Territories', 'Bahrain')")
	conditions.append("gle.account = %(vat_account)s")
	conditions_str = "and {}".format(" and ".join(conditions)) if conditions else ""

	order_by_statement = "order by gle.posting_date, gle.account, gle.creation"

	gl_entries = frappe.db.sql(
		"""SELECT
			gle.name as gl_entry, gle.posting_date, gle.account, gle.party_type, customer.customer_name as customer_name, customer.tax_id,
			gle.voucher_type, gle.voucher_no, gle.cost_center, gle.project,
			gle.against_voucher_type, gle.against_voucher, gle.account_currency,
			gle.remarks, gle.against, gle.is_opening, gle.creation, customer.territory,
			CASE
				WHEN gle.voucher_type != 'Sales Invoice' THEN je.user_remark
				ELSE ""
			END as items
			{select_fields}
		FROM `tabGL Entry` gle
		LEFT JOIN `tabCustomer` `customer` ON `customer`.`name` = gle.`against`
		LEFT JOIN `tabJournal Entry` je ON gle.voucher_type = 'Journal Entry' and gle.voucher_no = je.name
		WHERE gle.company=%(company)s {conditions}
		{order_by_statement}
		""".format(
			select_fields=select_fields, conditions=conditions_str, order_by_statement=order_by_statement
		),
		filters, as_dict=1)

	total_net_amount = 0
	total_vat_amount = 0

	for gle in gl_entries:
		total_net_amount += flt(gle.net_total)
		total_vat_amount += flt(gle.vat_amount)

		if gle.voucher_type == "Sales Invoice":
			invoice = frappe.get_doc("Sales Invoice", gle.voucher_no)
			itemised_tax = get_itemised_tax(invoice.taxes, True)
			items = []

			for item_code, taxes in itemised_tax.items():
				for tax_head, tax_item in taxes.items():
					if tax_item.tax_amount > 0 and tax_item.tax_account == vat_payable_account and item_code not in items:
						items.append(item_code)

			gle.items = ", ".join(items)

	return columns, gl_entries, total_net_amount, total_vat_amount

def get_zero_rated_domestic_sales(filters, sales_template):
	columns = get_1_columns()

	vat_payable_account = sales_template.taxes[0].account_head
	vat_rate = sales_template.taxes[0].rate
	debtors_accounts = frappe.get_list('Account Item', fields='account', filters=[{'parentfield': 'debtors_accounts'}])

	filters.setdefault('vat_account', vat_payable_account)
	debtors_accounts_str =  ", ".join(frappe.db.escape(account.account) for account in debtors_accounts)

	data = []
	select_fields = """, gle.debit, gle.credit, gle.debit_in_account_currency,
		SUM(gle.debit_in_account_currency - gle.credit_in_account_currency) as balance, '0' as vat """

	conditions = []
	conditions.append("(gle.posting_date >=%(from_date)s and gle.posting_date <=%(to_date)s)")
	conditions.append("gle.is_cancelled = 0")
	conditions.append("gle.debit_in_account_currency > 0")
	conditions.append("customer.territory in ('All Territories', 'Bahrain')")
	conditions.append("gle.account in ({})".format(debtors_accounts_str))
	conditions_str = "and {}".format(" and ".join(conditions)) if conditions else ""

	order_by_statement = "order by gle.posting_date, gle.account, gle.creation"

	gl_entries = frappe.db.sql(
		"""SELECT
			gle.name as gl_entry, gle.posting_date, gle.account, gle.party_type, customer.customer_name as customer_name, customer.tax_id,
			gle.voucher_type, gle.voucher_no, gle.cost_center, gle.project,
			gle.against_voucher_type, gle.against_voucher, gle.account_currency,
			gle.remarks, gle.against, gle.is_opening, gle.creation, customer.territory,
			CASE
				WHEN gle.voucher_type != 'Sales Invoice' THEN je.user_remark
				ELSE ""
			END as items
			{select_fields}
		FROM `tabGL Entry` gle
		LEFT JOIN `tabCustomer` `customer` ON `customer`.`name` = gle.`party`
		LEFT JOIN `tabJournal Entry` je ON gle.voucher_type = 'Journal Entry' and gle.voucher_no = je.name
		WHERE gle.company=%(company)s {conditions}
		GROUP BY gle.voucher_no
		{order_by_statement}
		""".format(
			select_fields=select_fields, conditions=conditions_str, order_by_statement=order_by_statement
		),
		filters, as_dict=1)

	entries = []
	total_net_amount = 0
	total_vat_amount = 0
	for gle in gl_entries:
		vat_entries = frappe.get_list("GL Entry", fields=['(credit_in_account_currency) as amount', 'account'], 
			filters=[{'voucher_no': gle.voucher_no}, {'account': vat_payable_account}, {'credit_in_account_currency': ('>', '0')}])
		total_vat = sum(((vat_entry.amount * (100 / vat_rate)) + flt(vat_entry.amount)) for vat_entry in vat_entries)

		non_vat_amount = flt(gle.balance) - (flt(total_vat))

		if non_vat_amount > 0:
			if gle.voucher_type == "Sales Invoice":
				invoice = frappe.get_doc("Sales Invoice", gle.voucher_no)
				itemised_tax = get_itemised_tax(invoice.taxes, True)
				items = []

				for item_code, taxes in itemised_tax.items():
					for tax_head, tax_item in taxes.items():
						if tax_item.tax_amount == 0 and tax_item.tax_account == vat_payable_account and item_code not in items:
							items.append(item_code)

				gle.items = ", ".join(items)

			total_net_amount += flt(non_vat_amount)
			gle.setdefault('net_total', non_vat_amount)
			gle.setdefault('total_amount_incl_vat', non_vat_amount)
			gle.setdefault('vat_amount', 0)
			entries.append(gle)

	return columns, entries, total_net_amount, total_vat_amount

def get_exports_sales(filters, sales_template):
	columns = get_1_columns()

	vat_payable_account = sales_template.taxes[0].account_head
	vat_rate = sales_template.taxes[0].rate
	debtors_accounts = frappe.get_list('Account Item', fields='account', filters=[{'parentfield': 'export_accounts'}])

	if not debtors_accounts:
		return columns, [], 0, 0

	filters.setdefault('vat_account', vat_payable_account)
	debtors_accounts_str =  ", ".join(frappe.db.escape(account.account) for account in debtors_accounts)

	data = []
	select_fields = """, gle.debit, gle.credit, gle.debit_in_account_currency,
		SUM(gle.debit_in_account_currency - gle.credit_in_account_currency) as balance, '0' as vat """

	conditions = []
	conditions.append("(gle.posting_date >=%(from_date)s and gle.posting_date <=%(to_date)s)")
	conditions.append("gle.is_cancelled = 0")
	conditions.append("gle.debit_in_account_currency > 0")
	conditions.append("customer.territory not in ('All Territories', 'Bahrain')")
	conditions.append("gle.account in ({})".format(debtors_accounts_str))
	conditions_str = "and {}".format(" and ".join(conditions)) if conditions else ""

	order_by_statement = "order by gle.posting_date, gle.account, gle.creation"

	gl_entries = frappe.db.sql(
		"""SELECT
			gle.name as gl_entry, gle.posting_date, gle.account, gle.party_type, customer.customer_name as customer_name, customer.tax_id,
			gle.voucher_type, gle.voucher_no, gle.cost_center, gle.project,
			gle.against_voucher_type, gle.against_voucher, gle.account_currency,
			gle.remarks, gle.against, gle.is_opening, gle.creation, customer.territory,
			CASE
				WHEN gle.voucher_type != 'Sales Invoice' THEN je.user_remark
				ELSE ""
			END as items
			{select_fields}
		FROM `tabGL Entry` gle
		LEFT JOIN `tabCustomer` `customer` ON `customer`.`name` = gle.`party`
		LEFT JOIN `tabJournal Entry` je ON gle.voucher_type = 'Journal Entry' and gle.voucher_no = je.name
		WHERE gle.company=%(company)s {conditions}
		GROUP BY gle.voucher_no
		{order_by_statement}
		""".format(
			select_fields=select_fields, conditions=conditions_str, order_by_statement=order_by_statement
		),
		filters, as_dict=1)

	entries = []
	total_net_amount = 0
	total_vat_amount = 0
	for gle in gl_entries:
		vat_entries = frappe.get_list("GL Entry", fields=['(credit_in_account_currency) as amount', 'account'], 
			filters=[{'voucher_no': gle.voucher_no}, {'account': vat_payable_account}, {'credit_in_account_currency': ('>', '0')}])
		total_vat = sum(((vat_entry.amount * (100 / vat_rate)) + flt(vat_entry.amount)) for vat_entry in vat_entries)

		non_vat_amount = flt(gle.balance) - flt(total_vat)

		if non_vat_amount > 0:
			if gle.voucher_type == "Sales Invoice":
				invoice = frappe.get_doc("Sales Invoice", gle.voucher_no)
				itemised_tax = get_itemised_tax(invoice.taxes, True)
				items = []

				for item_code, taxes in itemised_tax.items():
					for tax_head, tax_item in taxes.items():
						if tax_item.tax_amount == 0 and tax_item.tax_account == vat_payable_account and item_code not in items:
							items.append(item_code)

				gle.items = ", ".join(items)

			total_net_amount += flt(non_vat_amount)
			gle.setdefault('net_total', non_vat_amount)
			gle.setdefault('total_amount_incl_vat', non_vat_amount)
			gle.setdefault('vat_amount', 0)
			entries.append(gle)

	return columns, entries, total_net_amount, total_vat_amount

def get_standard_rated_purchases(filters, purchase_template):
	columns = get_2_columns()
	
	vat_receivable_account = purchase_template.taxes[0].account_head
	vat_rate = purchase_template.taxes[0].rate

	filters.setdefault('vat_account', vat_receivable_account)

	data = []
	select_fields = """, gle.debit, gle.credit, gle.debit_in_account_currency,
		gle.debit_in_account_currency as vat_amount, (gle.debit_in_account_currency * {}) as net_total, 
		'{}' as vat, (gle.debit_in_account_currency + (gle.debit_in_account_currency * {})) as total_amount_incl_vat """.format((100/flt(vat_rate)), vat_rate, (100/flt(vat_rate)))

	conditions = []
	conditions.append("(gle.posting_date >=%(from_date)s and gle.posting_date <=%(to_date)s)")
	conditions.append("gle.is_cancelled = 0")
	conditions.append("gle.debit_in_account_currency > 0")
	conditions.append("(supplier.country = 'Bahrain' OR gle.`against` = '' OR supplier.name IS NULL)")
	conditions.append("gle.account = {}".format(frappe.db.escape(vat_receivable_account)))
	conditions_str = "and {}".format(" and ".join(conditions)) if conditions else ""

	order_by_statement = "order by gle.posting_date, gle.account, gle.creation"

	gl_entries = frappe.db.sql(
		"""SELECT
			gle.name as gl_entry, gle.posting_date, gle.account, gle.party_type, supplier.supplier_name as supplier_name, supplier.tax_id,
			gle.voucher_type, gle.voucher_no, gle.cost_center, gle.project,
			gle.against_voucher_type, gle.against_voucher, gle.account_currency,
			gle.remarks, gle.against, gle.is_opening, gle.creation, supplier.country,
			CASE
				WHEN gle.voucher_type != 'Purchase Invoice' THEN je.user_remark
				ELSE ""
			END as items
			{select_fields}
		FROM `tabGL Entry` gle
		LEFT JOIN `tabJournal Entry` je ON gle.voucher_type = 'Journal Entry' and gle.voucher_no = je.name
		LEFT JOIN `tabSupplier` `supplier` ON `supplier`.`name` = gle.`against` or `supplier`.`name` = je.`pay_to_recd_from`
		WHERE gle.company=%(company)s {conditions}
		{order_by_statement}
		""".format(
			select_fields=select_fields, conditions=conditions_str, order_by_statement=order_by_statement
		),
		filters, as_dict=1)

	total_net_amount = 0
	total_vat_amount = 0
	for gle in gl_entries:
		total_net_amount += flt(gle.net_total)
		total_vat_amount += flt(gle.vat_amount)
		if gle.voucher_type == "Purchase Invoice":
			invoice = frappe.get_doc("Purchase Invoice", gle.voucher_no)
			itemised_tax = get_itemised_tax(invoice.taxes, True)
			items = []

			for item_code, taxes in itemised_tax.items():
				for tax_head, tax_item in taxes.items():
					if tax_item.tax_amount > 0 and tax_item.tax_account == vat_receivable_account and item_code not in items:
						items.append(item_code)

			gle.items = ", ".join(items)

	return columns, gl_entries, total_net_amount, total_vat_amount

def get_imports_purchases(filters, purchase_template):
	columns = get_2_columns()

	vat_receivable_account = purchase_template.taxes[0].account_head
	vat_rate = purchase_template.taxes[0].rate
	import_accounts = frappe.get_list('Account Item', fields='account', filters=[{'parentfield': 'import_accounts'}])

	if not import_accounts:
		return columns, [], 0, 0

	filters.setdefault('vat_account', vat_receivable_account)
	import_accounts_str =  ", ".join(frappe.db.escape(account.account) for account in import_accounts)
	
	data = []
	select_fields = """, gle.debit, gle.credit, gle.debit_in_account_currency,
		gle.debit_in_account_currency as vat_amount, (gle.debit_in_account_currency * (100/account.tax_rate)) as net_total, 
		account.tax_rate as vat, (gle.debit_in_account_currency + (gle.debit_in_account_currency * (100/account.tax_rate))) as total_amount_incl_vat """

	conditions = []
	conditions.append("(gle.posting_date >=%(from_date)s and gle.posting_date <=%(to_date)s)")
	conditions.append("gle.is_cancelled = 0")
	conditions.append("gle.debit_in_account_currency > 0")
	conditions.append("gle.account in ({})".format(import_accounts_str))
	conditions_str = "and {}".format(" and ".join(conditions)) if conditions else ""

	order_by_statement = "order by gle.posting_date, gle.account, gle.creation"
	
	gl_entries = frappe.db.sql(
		"""SELECT
			gle.name as gl_entry, gle.posting_date, gle.account, gle.party_type, supplier.supplier_name as supplier_name, supplier.tax_id,
			gle.voucher_type, gle.voucher_no, gle.cost_center, gle.project,
			gle.against_voucher_type, gle.against_voucher, gle.account_currency,
			gle.remarks, gle.against, gle.is_opening, gle.creation, supplier.country,
			CASE
				WHEN gle.voucher_type != 'Purchase Invoice' THEN je.user_remark
				ELSE ""
			END as items
			{select_fields}
		FROM `tabGL Entry` gle
		LEFT JOIN `tabSupplier` `supplier` ON `supplier`.`name` = gle.`against`
		LEFT JOIN `tabJournal Entry` je ON gle.voucher_type = 'Journal Entry' and gle.voucher_no = je.name
		LEFT JOIN `tabAccount` account ON account.name = gle.account
		WHERE gle.company=%(company)s {conditions}
		{order_by_statement}
		""".format(
			select_fields=select_fields, conditions=conditions_str, order_by_statement=order_by_statement
		),
		filters, as_dict=1)

	total_net_amount = 0
	total_vat_amount = 0
	for gle in gl_entries:
		total_net_amount += flt(gle.net_total)
		total_vat_amount += flt(gle.vat_amount)
		if gle.voucher_type == "Purchase Invoice":
			invoice = frappe.get_doc("Purchase Invoice", gle.voucher_no)
			itemised_tax = get_itemised_tax(invoice.taxes, True)
			items = []

			for item_code, taxes in itemised_tax.items():
				for tax_head, tax_item in taxes.items():
					if tax_item.tax_amount > 0 and tax_item.tax_account == vat_receivable_account and item_code not in items:
						items.append(item_code)

			gle.items = ", ".join(items)

	return columns, gl_entries, total_net_amount, total_vat_amount

def get_zero_rated_domestic_purchases(filters, purchase_template):
	columns = get_2_columns()

	vat_receivable_account = purchase_template.taxes[0].account_head
	vat_rate = purchase_template.taxes[0].rate
	creditors_accounts = frappe.get_list('Account Item', fields='account', filters=[{'parentfield': 'creditors_accounts'}])

	filters.setdefault('vat_account', vat_receivable_account)
	creditors_accounts_str =  ", ".join(frappe.db.escape(account.account) for account in creditors_accounts)

	data = []
	select_fields = """, gle.debit, gle.credit, gle.debit_in_account_currency,
		SUM(gle.credit_in_account_currency - gle.debit_in_account_currency) as balance, '0' as vat """

	conditions = []
	conditions.append("(gle.posting_date >=%(from_date)s and gle.posting_date <=%(to_date)s)")
	conditions.append("gle.is_cancelled = 0")
	conditions.append("supplier.country = 'Bahrain'")
	conditions.append("gle.credit_in_account_currency > 0")
	conditions.append("gle.account in ({})".format(creditors_accounts_str))
	conditions_str = "and {}".format(" and ".join(conditions)) if conditions else ""

	order_by_statement = "order by gle.posting_date, gle.account, gle.creation"

	gl_entries = frappe.db.sql(
		"""SELECT
			gle.name as gl_entry, gle.posting_date, gle.account, gle.party_type, supplier.supplier_name as supplier_name, supplier.tax_id,
			gle.voucher_type, gle.voucher_no, gle.cost_center, gle.project,
			gle.against_voucher_type, gle.against_voucher, gle.account_currency,
			gle.remarks, gle.against, gle.is_opening, gle.creation, supplier.country,
			CASE
				WHEN gle.voucher_type != 'Purchase Invoice' THEN je.user_remark
				ELSE ""
			END as items
			{select_fields}
		FROM `tabGL Entry` gle
		LEFT JOIN `tabSupplier` `supplier` ON `supplier`.`name` = gle.`party`
		LEFT JOIN `tabJournal Entry` je ON gle.voucher_type = 'Journal Entry' and gle.voucher_no = je.name
		WHERE gle.company=%(company)s {conditions}
		GROUP BY gle.voucher_no
		{order_by_statement}
		""".format(
			select_fields=select_fields, conditions=conditions_str, order_by_statement=order_by_statement
		),
		filters, as_dict=1)

	entries = []
	total_net_amount = 0
	total_vat_amount = 0
	for gle in gl_entries:
		vat_entries = frappe.get_list("GL Entry", fields=['(debit_in_account_currency) as amount', 'account'], 
			filters=[{'voucher_no': gle.voucher_no}, {'account': vat_receivable_account}, {'debit_in_account_currency': ('>', '0')}])
		total_vat = sum(((vat_entry.amount * (100 / vat_rate)) + flt(vat_entry.amount)) for vat_entry in vat_entries)

		non_vat_amount = flt(gle.balance) - flt(total_vat)

		if non_vat_amount > 0:
			if gle.voucher_type == "Purchase Invoice":
				invoice = frappe.get_doc("Purchase Invoice", gle.voucher_no)
				itemised_tax = get_itemised_tax(invoice.taxes, True)
				items = []

				for item_code, taxes in itemised_tax.items():
					for tax_head, tax_item in taxes.items():
						if tax_item.tax_amount == 0 and tax_item.tax_account == vat_receivable_account and item_code not in items:
							items.append(item_code)

				gle.items = ", ".join(items)

			total_net_amount += flt(non_vat_amount)
			gle.setdefault('net_total', non_vat_amount)
			gle.setdefault('total_amount_incl_vat', non_vat_amount)
			gle.setdefault('vat_amount', 0)
			entries.append(gle)

	return columns, entries, total_net_amount, total_vat_amount

def get_1_columns():
	"""return columns based on filters"""
	return [
		{
			'label': _("Voucher No."),
			'fieldname': 'voucher_no',
			'fieldtype': 'Data',
			'width': 180
		},
		{
			'label': _("Posting Date"),
			'fieldname': 'posting_date',
			'fieldtype': 'Date',
			'width': 100
		},
		{
			'label': _("Customer Name"),
			'fieldname': 'customer_name',
			'fieldtype': 'Data',
			'width': 120
		},
		{
			'label': _("Territory"),
			'fieldname': 'territory',
			'fieldtype': 'Link',
			'options': 'Territory',
			'width': 80
		},
		{
			'label': _("Tax Id"),
			'fieldname': 'tax_id',
			'fieldtype': 'Data',
			'width': 120
		},
		{
			"label": _("Items"),
			"fieldname": "items",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Net Total"),
			"fieldname": "net_total",
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 120
		},
		{
			"label": _("VAT"),
			"fieldname": "vat",
			"fieldtype": "Percentage",
			"width": 120
		},
		{
			"label": _("VAT Amount"),
			"fieldname": "vat_amount",
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 120
		},
		{
			"label": _("Total Amount Incl VAT"),
			"fieldname": "total_amount_incl_vat",
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 160
		}
	]

def get_2_columns():
	"""return columns based on filters"""
	return [
		{
			'label': _("Voucher No."),
			'fieldname': 'voucher_no',
			'fieldtype': 'Data',
			'width': 180
		},
		{
			'label': _("Posting Date"),
			'fieldname': 'posting_date',
			'fieldtype': 'Date',
			'width': 100
		},
		{
			'label': _("Supplier Name"),
			'fieldname': 'supplier_name',
			'fieldtype': 'Data',
			'width': 120
		},
		{
			'label': _("Country"),
			'fieldname': 'country',
			'fieldtype': 'Link',
			'options': 'Country',
			'width': 80
		},
		{
			'label': _("Tax Id"),
			'fieldname': 'tax_id',
			'fieldtype': 'Data',
			'width': 120
		},
		{
			"label": _("Items"),
			"fieldname": "items",
			"fieldtype": "Data",
			"width": 120
		},
		{
			"label": _("Net Total"),
			"fieldname": "net_total",
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 120
		},
		{
			"label": _("VAT"),
			"fieldname": "vat",
			"fieldtype": "Percentage",
			"width": 120
		},
		{
			"label": _("VAT Amount"),
			"fieldname": "vat_amount",
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 120
		},
		{
			"label": _("Total Amount Incl VAT"),
			"fieldname": "total_amount_incl_vat",
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 160
		}
	]

def get_summary_columns():
	return [
		{
			'label': _("#"),
			'fieldname': 'no',
			'fieldtype': 'Int',
			'width': 20
		},
		{
			'label': _("Description"),
			'fieldname': 'description',
			'fieldtype': 'Data',
			'width': 400
		},
		{
			"label": _("Amount"),
			"fieldname": "amount",
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 120
		},
		{
			"label": _("VAT Amount"),
			"fieldname": "vat_amount",
			"fieldtype": "Currency",
			"options": 'currency',
			"width": 120
		}
	]