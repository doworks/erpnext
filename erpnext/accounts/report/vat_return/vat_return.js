// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["VAT Return"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname": "sales_taxes_and_charges_template",
			"label": __("Sales Taxes and Charges Template"),
			"fieldtype": "Link",
			"options": "Sales Taxes and Charges Template",
			"reqd": 1
		},
		{
			"fieldname": "purchase_taxes_and_charges_template",
			"label": __("Purchase Taxes and Charges Template"),
			"fieldtype": "Link",
			"options": "Purchase Taxes and Charges Template",
			"reqd": 1
		},
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -3),
			"reqd": 1,
			"width": "80"
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"reqd": 1,
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "report_type",
			"label": __("Report Type"),
			"reqd": 1,
			"fieldtype": "Select",
			"options": "Summary\n1 Standard Rated Sales\n4 Zero Rated Domestic Sales\n5 Exports\n8 Standard Rated Domestic Purchases\n9 Imports\n12 Zero Rated Domesitc Purchases",
			"default": "Summary"
		}
	],
	"formatter": function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (typeof data !== "undefined") {
			if ('description' in data) {
				if (data.description == 'Total Sales') {
					value = `<span style='color:green!important; font-weight:bold!important;'>${value}</span>`;
				}

				if (data.description == 'Total Purchases') {
					value = `<span style='color:red!important; font-weight:bold!important;'>${value}</span>`;
				}

				if (parseInt(data.no) > 13) {
					value = `<span style='font-weight:bold!important;'>${value}</span>`;
				}

				if (parseInt(data.no) == 17) {
					value = `<span style='font-weight:bold!important; background:#ccc!important'>${value}</span>`;
				}
			}
		}

		return value;
	}
};
