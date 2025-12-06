

frappe.ui.form.on("Payment Entry Reference", {
    form_render: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];

        if (row.reference_doctype === "Journal Entry" ) {
            frappe.db.get_doc("Journal Entry", row.reference_name).then(doc => {
                frappe.model.set_value(cdt, cdn, "custom_bill_number", doc.custom_bill_number);
                frappe.model.set_value(cdt, cdn, "custom_grn_number", doc.custom_grn_number);
                frappe.model.set_value(cdt, cdn, "posting_date", doc.posting_date);
            });
        }
    }
});

