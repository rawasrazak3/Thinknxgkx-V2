// Copyright (c) 2025, Thinknxg and contributors
// For license information, please see license.txt

// frappe.ui.form.on("Karexpert Settings", {
//     refresh: function(frm) {
//         frm.add_custom_button(__('My Button'), function() {
//             frappe.msgprint(__('Custom button clicked!'));
//         }, __('Actions')); // Optional: group under "Actions"
//     }
// });
frappe.ui.form.on("Karexpert  Table", {
	execute: function(frm, cdt, cdn) {
		console.log("Button clicked");
		let row = locals[cdt][cdn];

		let method_map = {
			"OP BILLING": {
				method: "thinknxg_kx.thinknxg_kx.custom_script.create_sales_invoice.main",
				message: "OP Sales Invoice Created"
			},
			"IPD BILLING": {
				method: "thinknxg_kx.thinknxg_kx.custom_script.create_si_ip.main",
				message: "IP Sales Invoice Created"
			},
			"DUE SETTLEMENT": {
				method:"thinknxg_kx.thinknxg_kx.custom_script.due_settlement.main",
				message: "Due settlement Created"
			},
			"ADVANCE DEPOSIT": {
				method: "thinknxg_kx.thinknxg_kx.custom_script.advance_deposit.main",
				message: "Advance Deposit Created"
			},
			"ADVANCE DEPOSIT REFUND": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.advance_deposit_refund.main",
				message: "Advance Deposit Refund Created"
			},
			"OP PHARMACY BILLING": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.pharmacy_bill.main",
				message: "OP pharmacy Sales Invoice Created"
			},
			"GRN CREATION SUMMARY": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.grn_creation.main",
				message: "GRN Created"
			},
			"OP BILLING REFUND": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.op_refund.main",
				message: "OP sales return  Invoice Created"
			},
			"PHARMACY BILLING REFUND": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.pharmacy_refund.main",
				message: "Pharmacy sales return Created"
			},
			"GRN RETURN DETAIL": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.grn_return.main",
				message: "GRN return Created"
			},
			"IPD ADDENDUM BILLING": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.ipd_addendum.main",
				message: "IPD Addendum Invoice Created"
			},
			"AR BILL SETTLEMENT": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.ar_bill_settlement.main",
				message: "AR Settlement Bill Created"
			},
			"DOCTOR PAYOUT": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.doctor_payout.main",
				message: "Doctor Payout Created"
			},
			"IF STOCK TRANSFER DETAIL": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.stock_transfer.main",
				message: "Stock Transfer Created"
			},
			"SUPPLIER CREATION": {
				method: "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.supplier_creation.main",
				message: "Suppliers Created"
			}
		};

		let billing_info = method_map[row.billing_type];

		if (!billing_info) {
            frappe.msgprint("Unsupported billing type selected.");
            return;
        }

        frappe.confirm(
            "Are you sure you want to execute this action?",
            function() {
                // YES clicked
                frappe.call({
                    method: billing_info.method,
                    args: { row_data: row },
                    callback: function(r) {
                        if (!r.exc) {
                            frappe.msgprint(billing_info.message);
                        } else {
                            frappe.msgprint("An error occurred while creating the document.");
                        }
                    }
                });
            },
            function() {
                // NO clicked
                frappe.msgprint("Execution cancelled.");
            }
        );
    }
});