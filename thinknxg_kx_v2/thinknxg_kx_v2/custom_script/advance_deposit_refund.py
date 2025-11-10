import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from datetime import datetime, timedelta,  timezone, time
from frappe.utils import getdate, add_days, cint
from thinknxg_kx_v2.thinknxg_kx_v2.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "ADVANCE DEPOSIT REFUND"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")

# Fetch row details based on billing type
billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
                                ["client_code", "integration_key", "x_api_key"], as_dict=True)

headers_token = fetch_api_details(billing_type)


def fetch_advance_billing(jwt_token, from_date, to_date, headers):
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    headers_billing = headers.copy()
    headers_billing["Authorization"] = f"Bearer {jwt_token}"

    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch OP Pharmacy Billing data: {response.status_code} - {response.text}")


@frappe.whitelist()
def main():
    try:
        settings = frappe.get_single("Karexpert Settings")

        # ✅ Collect all facility IDs from child table
        facility_list = [row.facility_id for row in settings.get("facility_id_details") or [] if row.facility_id]

        if not facility_list:
            frappe.throw("No facility IDs found in Karexpert Settings.")

        # Prepare date range
        to_date_raw = settings.get("date")
        t_date = getdate(to_date_raw) if to_date_raw else getdate(add_days(nowdate(), 0))
        no_of_days = cint(settings.get("no_of_days") or 25)
        f_date = getdate(add_days(t_date, -no_of_days))

        # Convert to timestamps (GMT+4)
        gmt_plus_4 = timezone(timedelta(hours=4))
        from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

        all_billing_data = []

        # ✅ Loop through each facility
        for row in settings.get("facility_id_details") or []:
            facility_id = row.facility_id
            if not facility_id:
                continue

            # Prepare headers for this facility
            billing_row = frappe.get_value(
                "Karexpert  Table",
                {"billing_type": "ADVANCE DEPOSIT REFUND"},
                ["client_code", "integration_key", "x_api_key"],
                as_dict=True
            )

            headers = {
                "Content-Type": "application/json",
                "clientCode": billing_row["client_code"],
                "integrationKey": billing_row["integration_key"],
                "facilityId": facility_id,
                "messageType": "request",
                "x-api-key": billing_row["x_api_key"]
            }

            # Fetch JWT for this facility
            jwt_token = get_jwt_token_for_headers(headers)

            frappe.log(f"Fetching advance deposit refund for Facility ID: {facility_id}")
            print("Fetching advance deposit refund for Facility ID",facility_id)
            billing_data = fetch_advance_billing(jwt_token, from_date, to_date, headers)

            if billing_data and "jsonResponse" in billing_data:
                all_billing_data.extend(billing_data["jsonResponse"])
            else:
                frappe.log(f"No data returned for {facility_id}")

        # ✅ Process all collected billing data
        for billing in all_billing_data:
            create_advance_refund_entry(billing["advance_refund"])

        frappe.log("All facility billing data processed successfully.")

    except Exception as e:
        frappe.log_error(f"Error in Advance deposit Fetch: {e}")


def get_jwt_token_for_headers(headers):
    """
    Fetch JWT token using the provided headers dict.
    """
    try:
        response = requests.post(TOKEN_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.json().get("jwttoken")
        else:
            frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")
    except requests.exceptions.RequestException as e:
        frappe.throw(f"JWT request failed: {e}")

if __name__ == "__main__":
    main()

def create_advance_refund_entry(billing_data):
    try:
        mode_of_payment = billing_data["payment_transaction_details"][0]["payment_mode_display"]

        mode_of_payment_accounts = frappe.get_all(
            "Mode of Payment Account",
            filters={"parent": mode_of_payment},
            fields=["default_account"],
            limit=1
        )

        if not mode_of_payment_accounts:
            return f"Failed: No default account found for mode of payment {mode_of_payment}"
        # --- Fetch accounts dynamically from Company ---
        company = frappe.defaults.get_user_default("Company")
        company_doc = frappe.get_doc("Company", company)
        cash_account = company_doc.default_cash_account
        bank_account = company_doc.default_bank_account
        # Use fixed account based on mode of payment
        if mode_of_payment.lower() == "cash":
            paid_to_account = cash_account
        else:
            paid_to_account = bank_account

        paid_to_account_currency = frappe.db.get_value("Account", paid_to_account, "account_currency")

        transaction_date_time = billing_data["payment_transaction_details"][0].get("transaction_date_time")
        if not transaction_date_time:
            return "Failed: Transaction Date is missing."

        # Define GMT+4 offset
        gmt_plus_4 = timezone(timedelta(hours=4))
        dt = datetime.fromtimestamp(transaction_date_time / 1000.0, gmt_plus_4)
        print("formt", dt)
        formatted_date = dt.strftime('%Y-%m-%d')
        print("date--", formatted_date)

        reference_no = billing_data.get("receipt_no")
        if not reference_no:
            return "Failed: Reference No is missing."

        existing_je = frappe.get_value(
            "Journal Entry",
            {
                "bill_no": reference_no
            },
            "name"
        )

        if frappe.db.exists("Journal Entry", {"custom_bill_number": reference_no}):
            return f"Skipped: Journal Entry already exists."


    
        transaction_id = ""
        for tx in billing_data.get("payment_transaction_details", []):
            if tx.get("transaction_id"):
                transaction_id = tx.get("transaction_id")
                break

        frappe.log_error("Transaction ID: " + str(transaction_id), "Advance Billing Log")


        # # Check for existing Journal Entry
        # existing_je = frappe.get_value(
        #     "Journal Entry",
        #     {"cheque_no": reference_no, "posting_date": formatted_date},
        #     "name"
        # )
        # if existing_je:
        #     return f"Skipped: Journal Entry {existing_je} already exists."

        customer_name = billing_data.get("patient_name")
        payer_type = billing_data["payer_type"]
        customer = get_or_create_customer(customer_name,payer_type)

        custom_advance_type = billing_data.get("advance_type")
        custom_patient_type = billing_data.get("patient_type_display")
        custom_uh_id = billing_data.get("uhId")
        amount = billing_data.get("amount")

        # Fetch default receivable account or use a custom "Customer Advances" account
        # customer_advance_account = frappe.db.get_value("Company", frappe.defaults.get_user_default("Company"), "default_receivable_account")
        customer_advance_account = "Debtors - OP"
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": formatted_date,
            "naming_series": "KX-JV-.YYYY.-",
            "custom_bill_number": reference_no,
            "bill_date":formatted_date,
            "remark": f"Advance refund to {customer_name}",
            "custom_advance_type": custom_advance_type,
            "custom_patient_type": custom_patient_type,
            "custom_uhid": custom_uh_id,
            "custom_bill_category": "UHID Advance Refund",
            "accounts": [
                {
                    "account": paid_to_account,
                    "credit_in_account_currency": amount,
                    "account_currency": paid_to_account_currency
                },
                {
                    "account": customer_advance_account,
                    "debit_in_account_currency": amount,
                    "account_currency": paid_to_account_currency,
                    "party_type": "Customer",
                    "party": customer,
                    # "is_advance":"Yes"
                }
            ]
        })
        if transaction_id:
            journal_entry.cheque_no = transaction_id
            journal_entry.cheque_date = formatted_date
        journal_entry.insert()
        frappe.db.commit()
        journal_entry.submit()

        return f"Journal Entry {journal_entry.name} created successfully!"
    
    except Exception as e:
        frappe.log_error(f"Error creating Journal Entry: {str(e)}")
        return f"Failed to create Journal Entry: {str(e)}"


def get_or_create_customer(customer_name, payer_type=None):
    # If payer type is cash, don't create a customer
    if payer_type and payer_type.lower() == "cash":
        return None
    # Check if the customer already exists
    existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name , "customer_group":payer_type})
    if existing_customer:
        return existing_customer

    # Determine customer group based on payer_type
    if payer_type:
        payer_type = payer_type.lower()
        if payer_type == "tpa":
            customer_group = "TPA"
        elif payer_type == "credit":
            customer_group = "Credit"
        else:
            customer_group = "Individual"  # default fallback
    else:
        customer_group = "Individual"

    # Create new customer
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_group": customer_group,
        "territory": "All Territories"
    })
    customer.insert(ignore_permissions=True)
    frappe.db.commit()

    return customer.name