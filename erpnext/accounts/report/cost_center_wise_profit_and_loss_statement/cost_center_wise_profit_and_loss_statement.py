# Copyright (c) 2013, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt
from erpnext.accounts.report.financial_statements import (
    get_period_list, get_accounts, filter_accounts, get_appropriate_currency, get_additional_conditions, convert_to_presentation_currency, filter_out_zero_value_rows, get_currency)
from six import itervalues
from datetime import datetime
from pprint import pprint
from pprint import pformat


def execute(filters=None):
    cost_centers = frappe.get_list("Cost Center", fields=["name"], filters={
                                   "company": filters.company})

    income = get_data(filters.company, "Income", "Credit", cost_centers, filters=filters,
                      accumulated_values=0, ignore_closing_entries=True, ignore_accumulated_values_for_fy=True)
                      
    expense = get_data(filters.company, "Expense", "Debit", cost_centers, filters=filters,
                       accumulated_values=0, ignore_closing_entries=True, ignore_accumulated_values_for_fy=True)

    net_profit_loss = get_net_profit_loss(
        income, expense, cost_centers, filters.company, filters.presentation_currency, filters)

    data = []
    data.extend(income or [])
    data.extend(expense or [])
    if net_profit_loss:
        data.append(net_profit_loss)

    columns = get_columns("None", cost_centers, 0, filters.company)

    chart = get_chart_data(filters, columns, income,
                           expense, net_profit_loss)

    default_currency = frappe.get_cached_value(
        'Company', filters.company, "default_currency")
    report_summary = get_report_summary(
        cost_centers, filters.company, income, expense, net_profit_loss, default_currency)

    return columns, data, None, chart, report_summary


def get_report_summary(cost_centers, periodicity, income, expense, net_profit_loss, default_currency, consolidated=False):
    net_income, net_expense, net_profit = 0.0, 0.0, 0.0

    for cost_center in cost_centers:
        key = cost_center if consolidated else cost_center.name
        if income:
            net_income += income[-2].get(key)
        if expense:
            net_expense += expense[-2].get(key)
        if net_profit_loss:
            net_profit += net_profit_loss.get(key)

    if (len(cost_centers) == 1 and periodicity == 'Yearly'):
        profit_label = _("Profit This Year")
        income_label = _("Total Income This Year")
        expense_label = _("Total Expense This Year")
    else:
        profit_label = _("Net Profit")
        income_label = _("Total Income")
        expense_label = _("Total Expense")

    return [
        {
            "value": net_profit,
            "indicator": "Green" if net_profit > 0 else "Red",
            "label": profit_label,
            "datatype": "Currency",
            "currency": net_profit_loss.get("currency") if net_profit_loss else default_currency
        },
        {
            "value": net_income,
            "label": income_label,
            "datatype": "Currency",
            "currency": income[-1].get('currency') if income else default_currency
        },
        {
            "value": net_expense,
            "label": expense_label,
            "datatype": "Currency",
            "currency": expense[-1].get('currency') if expense else default_currency
        }
    ]


def get_columns(periodicity, cost_centers, accumulated_values=0, company=None):
    columns = [{
        "fieldname": "account",
        "label": _("Account"),
        "fieldtype": "Link",
        "options": "Account",
        "width": 300
    }]

    if company:
        columns.append({
            "fieldname": "currency",
            "label": _("Currency"),
            "fieldtype": "Link",
            "options": "Currency",
            "hidden": 1
        })
    for cost_center in cost_centers:
        columns.append({
            "fieldname": cost_center.name,
            "label": cost_center.name,
            "fieldtype": "Currency",
            "options": "currency",
            "width": 150
        })
    if periodicity != "Yearly":
        if not accumulated_values:
            columns.append({
                "fieldname": "total",
                "label": _("Total"),
                "fieldtype": "Currency",
                "width": 150
            })

    return columns


def get_data(
        company, root_type, balance_must_be, cost_centers, filters=None,
        accumulated_values=1, only_current_fiscal_year=True, ignore_closing_entries=False,
        ignore_accumulated_values_for_fy=False, total=True):

    accounts = get_accounts(company, root_type)
    if not accounts:
        return None

    accounts, accounts_by_name, parent_children_map = filter_accounts(accounts)

    company_currency = get_appropriate_currency(company, filters)

    gl_entries_by_account = {}
    for root in frappe.db.sql("""select lft, rgt from tabAccount where root_type=%s and ifnull(parent_account, '') = ''""", root_type, as_dict=1):

        set_gl_entries_by_account(
            company,
            filters.from_date if only_current_fiscal_year else None,
            filters.to_date,
            root.lft, root.rgt, filters,
            gl_entries_by_account, ignore_closing_entries=ignore_closing_entries
        )

    calculate_values(accounts_by_name, gl_entries_by_account, cost_centers,
                     accumulated_values, ignore_accumulated_values_for_fy, filters)
    accumulate_values_into_parents(accounts, accounts_by_name, cost_centers)

    out = prepare_data(accounts, balance_must_be,
                       cost_centers, company_currency, filters)
    out = filter_out_zero_value_rows(out, parent_children_map)

    if out and total:
        add_total_row(out, root_type, balance_must_be,
                      cost_centers, company_currency)

    return out


def set_gl_entries_by_account(company, from_date, to_date, root_lft, root_rgt, filters, gl_entries_by_account, ignore_closing_entries=False):
    """Returns a dict like { "account": [gl entries], ... }"""

    additional_conditions = get_additional_conditions(
        from_date, ignore_closing_entries, filters)

    accounts = frappe.db.sql_list("""select name from `tabAccount`
		where lft >= %s and rgt <= %s""", (root_lft, root_rgt))
    additional_conditions += " and account in ({})"\
        .format(", ".join([frappe.db.escape(d) for d in accounts]))

    gl_entries = frappe.db.sql("""select posting_date, account, debit, credit, is_opening, fiscal_year, debit_in_account_currency, credit_in_account_currency, account_currency, cost_center from `tabGL Entry`
        where company=%(company)s
        {additional_conditions}
        and posting_date <= %(to_date)s
        order by account, posting_date""".format(additional_conditions=additional_conditions),
        {
            "company": company,
            "from_date": from_date,
            "to_date": to_date,
            "cost_center": filters.cost_center,
            "project": filters.project,
            "finance_book": filters.get("finance_book"),
            "company_fb": frappe.db.get_value("Company", company, 'default_finance_book')
        }
    ,as_dict=True)

    if filters and filters.get('presentation_currency'):
        convert_to_presentation_currency(gl_entries, get_currency(filters))

    for entry in gl_entries:
        gl_entries_by_account.setdefault(entry.account, []).append(entry)

    return gl_entries_by_account


def calculate_values(
        accounts_by_name, gl_entries_by_account, cost_centers, accumulated_values, ignore_accumulated_values_for_fy, filters=None):
    for entries in itervalues(gl_entries_by_account):
        for entry in entries:
            d = accounts_by_name.get(entry.account)
            if not d:
                frappe.msgprint(
                    _("Could not retrieve information for {0}.").format(entry.account), title="Error",
                    raise_exception=1
                )
            for cost_center in cost_centers:
                # check if posting date is within the period

                if entry.posting_date <= datetime.strptime(filters.to_date, '%Y-%m-%d').date() and entry.cost_center == cost_center.name:
                    if (accumulated_values or entry.posting_date >= datetime.strptime(filters.from_date, '%Y-%m-%d').date()) and (not ignore_accumulated_values_for_fy or entry.posting_date <= datetime.strptime(filters.to_date, '%Y-%m-%d').date()):
                        d[cost_center.name] = d.get(
                            cost_center.name, 0.0) + flt(entry.debit) - flt(entry.credit)

            if entry.posting_date < datetime.strptime(filters.from_date, '%Y-%m-%d').date():
                d["opening_balance"] = d.get(
                    "opening_balance", 0.0) + flt(entry.debit) - flt(entry.credit)


def accumulate_values_into_parents(accounts, accounts_by_name, cost_centers):
    """accumulate children's values in parent accounts"""
    for d in reversed(accounts):
        if d.parent_account:
            for cost_center in cost_centers:
                accounts_by_name[d.parent_account][cost_center.name] = \
                    accounts_by_name[d.parent_account].get(
                        cost_center.name, 0.0) + d.get(cost_center.name, 0.0)

            accounts_by_name[d.parent_account]["opening_balance"] = \
                accounts_by_name[d.parent_account].get(
                    "opening_balance", 0.0) + d.get("opening_balance", 0.0)


def prepare_data(accounts, balance_must_be, cost_centers, company_currency, filters=None):
    data = []
    year_start_date = filters.from_date
    year_end_date = filters.to_date

    for d in accounts:
        # add to output
        has_value = False
        total = 0
        row = frappe._dict({
            "account": _(d.name),
            "parent_account": _(d.parent_account) if d.parent_account else '',
            "indent": flt(d.indent),
            "year_start_date": year_start_date,
            "year_end_date": year_end_date,
            "currency": company_currency,
            "include_in_gross": d.include_in_gross,
            "account_type": d.account_type,
            "is_group": d.is_group,
            "opening_balance": d.get("opening_balance", 0.0) * (1 if balance_must_be == "Debit" else -1),
            "account_name": ('%s - %s' % (_(d.account_number), _(d.account_name))
                             if d.account_number else _(d.account_name))
        })

        for cost_center in cost_centers:
            if d.get(cost_center.name) and balance_must_be == "Credit":
                # change sign based on Debit or Credit, since calculation is done using (debit - credit)
                d[cost_center.name] *= -1

            row[cost_center.name] = flt(d.get(cost_center.name, 0.0), 3)

            if abs(row[cost_center.name]) >= 0.005:
                # ignore zero values
                has_value = True
                total += flt(row[cost_center.name])

        row["has_value"] = has_value
        row["total"] = total
        data.append(row)

    return data


def add_total_row(out, root_type, balance_must_be, cost_centers, company_currency, filters=None):
    total_row = {
        "account_name": "'" + _("Total {0} ({1})").format(_(root_type), _(balance_must_be)) + "'",
        "account": "'" + _("Total {0} ({1})").format(_(root_type), _(balance_must_be)) + "'",
        "currency": company_currency
    }

    for row in out:
        if not row.get("parent_account"):
            for cost_center in cost_centers:
                total_row.setdefault(cost_center.name, 0.0)
                total_row[cost_center.name] += row.get(
                    cost_center.name, 0.0)
                row[cost_center.name] = row.get(cost_center.name, 0.0)

            total_row.setdefault("total", 0.0)
            total_row["total"] += flt(row["total"])
            row["total"] = ""

    if "total" in total_row:
        out.append(total_row)

        # blank row after Total
        out.append({})


def get_net_profit_loss(income, expense, cost_centers, company, currency=None, consolidated=False, filters=None):
    total = 0
    net_profit_loss = {
        "account_name": "'" + _("Profit for the year") + "'",
        "account": "'" + _("Profit for the year") + "'",
        "warn_if_negative": True,
        "currency": currency or frappe.get_cached_value('Company',  company,  "default_currency")
    }

    has_value = False

    for cost_center in cost_centers:
        key = cost_center.name if consolidated else cost_center.name
        total_income = flt(income[-2][key], 3) if income else 0
        total_expense = flt(expense[-2][key], 3) if expense else 0

        net_profit_loss[key] = total_income - total_expense

        if net_profit_loss[key]:
            has_value = True

        total += flt(net_profit_loss[key])
        net_profit_loss["total"] = total

    if has_value:
        return net_profit_loss


def get_chart_data(filters, columns, income, expense, net_profit_loss):
    labels = [d.get("label") for d in columns[2:]]

    income_data, expense_data, net_profit = [], [], []

    for p in columns[2:]:
        if income:
            income_data.append(income[-2].get(p.get("fieldname")))
        if expense:
            expense_data.append(expense[-2].get(p.get("fieldname")))
        if net_profit_loss:
            net_profit.append(net_profit_loss.get(p.get("fieldname")))

    datasets = []
    if income_data:
        datasets.append({'name': 'Income', 'values': income_data})
    if expense_data:
        datasets.append({'name': 'Expense', 'values': expense_data})
    if net_profit:
        datasets.append({'name': 'Net Profit/Loss', 'values': net_profit})

    chart = {
        "data": {
            'labels': labels,
            'datasets': datasets
        }
    }

    if not filters.accumulated_values:
        chart["type"] = "bar"
    else:
        chart["type"] = "line"

    chart["fieldtype"] = "Currency"

    return chart
