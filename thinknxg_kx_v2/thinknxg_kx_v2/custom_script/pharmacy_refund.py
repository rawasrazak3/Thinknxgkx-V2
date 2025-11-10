import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta,timezone,time
from thinknxg_kx_v2.thinknxg_kx_v2.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "PHARMACY BILLING REFUND"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")
facility_id = settings.get("facility_id")

# Fetch row details based on billing type
billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
                                ["client_code", "integration_key", "x_api_key"], as_dict=True)

headers_token = fetch_api_details(billing_type)


# def get_jwt_token():
#     frappe.log_error(json.dumps(headers_token, indent=2), "JWT Header Details")
#     response = requests.post(TOKEN_URL, headers=headers_token)
#     if response.status_code == 200:
#         return response.json().get("jwttoken")
#     else:
#         frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

def fetch_op_billing_refund(jwt_token, from_date, to_date, headers):
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    headers_billing = headers.copy()
    headers_billing["Authorization"] = f"Bearer {jwt_token}"

    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch OP Pharmacy Billing data: {response.status_code} - {response.text}")

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

def get_or_create_patient(patient_name,gender):
    existing_patient = frappe.db.exists("Patient", {"patient_name": patient_name})
    if existing_patient:
        return existing_patient
    
    customer = frappe.get_doc({
        "doctype": "Patient",
        "first_name": patient_name,
        "sex": gender
    })
    customer.insert(ignore_permissions=True)
    frappe.db.commit()
    return customer.name
def get_or_create_cost_center(facility_name):
    cost_center_name = f"{facility_name} - OP"
    
    # Check if the cost center already exists by full name
    existing = frappe.db.exists("Cost Center", cost_center_name)
    if existing:
        return cost_center_name
    
    parent_cost_center = "Oxygen Pharmacy - OP"

    # Create new cost center with full cost_center_name as document name
    cost_center = frappe.get_doc({
        "doctype": "Cost Center",
        "name": cost_center_name,               # Explicitly set doc name to full name with suffix
        "cost_center_name": facility_name,  # Display name without suffix
        "parent_cost_center": parent_cost_center,
        "is_group": 0,
        "company": "Oxygen Pharmacy"
    })
    cost_center.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"Cost Center '{cost_center_name}' created under '{parent_cost_center}'")
    
    return cost_center_name  # Always return the full cost center name with suffix

def get_or_create_stock_account(facility_name):
    stock_acc_name = f"STOCK IN HAND - {facility_name} - OP"
    
    # Check if the cost center already exists by full name
    existing = frappe.db.exists("Account", stock_acc_name)
    if existing:
        return stock_acc_name
    
   
    parent_cost_center = "Stock Assets - OP"

    # Create new cost center with full cost_center_name as document name
    stock_acc = frappe.get_doc({
        "doctype": "Account",
        "account_name": f"STOCK IN HAND - {facility_name}",  
        "account_type": "Stock",           
        "parent_account": parent_cost_center,
        "company": "Oxygen Pharmacy"
    })
    stock_acc.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"Account '{stock_acc_name}' created under '{parent_cost_center}'")
    
    return stock_acc_name  # Always return the full account name with suffix

def get_or_create_cash_account(facility_name):
    company = "Oxygen Pharmacy"
    account_name = f"CASH IN HAND - {facility_name}"
    parent_account = "Cash In Hand - OP"  

    # Try to find existing account by account_name and company
    existing = frappe.db.get_value(
        "Account",
        {"account_name": account_name, "company": company},
        "name"
    )
    if existing:
        return existing  # Return the actual Account.name

    # Create new account if not found
    account = frappe.get_doc({
        "doctype": "Account",
        "account_name": account_name,
        "account_type": "Cash",
        "parent_account": parent_account,
        "company": company
    })
    account.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"Created Cash Account '{account_name}' under '{parent_account}'")

    return account.name  # Always return the real document name

# @frappe.whitelist()
# def main():
#     try:
#         jwt_token = get_jwt_token()
#         frappe.log("JWT Token fetched successfully.")

#         # from_date = 1672531200000  
#         # to_date = 1940009600000    
#         # Fetch dynamic date and number of days from settings
#         settings = frappe.get_single("Karexpert Settings")
#         # Get to_date from settings or fallback to nowdate() - 4 days
#         to_date_raw = settings.get("date")
#         if to_date_raw:
#             t_date = getdate(to_date_raw)
#         else:
#             t_date = add_days(nowdate(), -4)

#         # Get no_of_days from settings and calculate from_date
#         no_of_days = cint(settings.get("no_of_days") or 25)  # default 3 days if not set
#         f_date = add_days(t_date, -no_of_days)
#          # Define GMT+4 timezone
#         gmt_plus_4 = timezone(timedelta(hours=4))

#         # Convert to timestamps in milliseconds for GMT+4
#         from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
#         print("---f", from_date)
#         to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
#         print("----t", to_date)
#         billing_data = fetch_op_billing_refund(jwt_token, from_date, to_date)
#         frappe.log("Pharmacy Billing refund data fetched successfully.")

#         for billing in billing_data.get("jsonResponse", []):
#             create_journal_entry_from_pharmacy_refund(billing["pharmacy_refund"])

#     except Exception as e:
#         frappe.log_error(f"Error: {e}")

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
                {"billing_type": "OP PHARMACY BILLING"},
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

            frappe.log(f"Fetching billing data for Facility ID: {facility_id}")
            print("Fetching billing data for Facility ID",facility_id)
            billing_data = fetch_op_billing_refund(jwt_token, from_date, to_date, headers)

            if billing_data and "jsonResponse" in billing_data:
                all_billing_data.extend(billing_data["jsonResponse"])
            else:
                frappe.log(f"No data returned for {facility_id}")

        # ✅ Process all collected billing data
        for billing in all_billing_data:
            create_journal_entry_from_pharmacy_refund(billing["pharmacy_refund"])

        frappe.log("All facility billing data processed successfully.")

    except Exception as e:
        frappe.log_error(f"Error in Pharmacy Billing Fetch: {e}")


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

def create_journal_entry_from_pharmacy_refund(refund_data):
    bill_no = refund_data["bill_no"]
    receipt_no = refund_data.get("receipt_no")

    payment_details = refund_data.get("payment_transaction_details", [])
    date = refund_data["g_creation_time"]
    datetimes = date / 1000.0

    # Define GMT+4
    gmt_plus_4 = timezone(timedelta(hours=4))
    dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
    formatted_date = dt.strftime('%Y-%m-%d')
    posting_time = dt.strftime('%H:%M:%S')
    modification_time = refund_data.get("g_modify_time", date)  # fallback if not present
    mod_date = modification_time / 1000.0

    # Define GMT+4
    gmt_plus_4 = timezone(timedelta(hours=4))
    mod_dt = datetime.fromtimestamp(mod_date, gmt_plus_4)
    mod_time = mod_dt.strftime('%Y-%m-%d %H:%M:%S')


    existing_jv = frappe.db.get_value(
        "Journal Entry",
        {"custom_bill_number": bill_no, "docstatus": ["!=", 2]},
        ["name", "custom_modification_time"],
        as_dict=True
    )

    if existing_jv:
        stored_mod_time = existing_jv.get("custom_modification_time")
        if stored_mod_time and str(stored_mod_time) == str(mod_time):
            frappe.log(f"Journal Entry {bill_no} already up-to-date. Skipping...")
            return existing_jv["name"]

        # Cancel old invoice + related journals
        je_doc = frappe.get_doc("Journal Entry", existing_jv["name"])
        try:
            # # Cancel linked journals
            # journals = frappe.get_all("Journal Entry",
            #     filters={"custom_bill_number": bill_no, "docstatus": 1},
            #     pluck="name")
            # for jn in journals:
            #     je_doc = frappe.get_doc("Journal Entry", jn)
            #     je_doc.cancel()
            #     frappe.db.commit()
            #     frappe.log(f"Cancelled JE {jn} for bill {bill_no}")

            # Cancel invoice
            je_doc.reload()
            je_doc.cancel()
            frappe.db.commit()
            frappe.log(f"Cancelled JV {existing_jv['name']} for modified bill {bill_no}")
        except Exception as e:
            frappe.log_error(f"Error cancelling JE for bill {bill_no}: {e}")
            return None

    if frappe.db.exists("Journal Entry", {"custom_bill_number": bill_no, "docstatus": ["!=", 2] ,"custom_bill_category": "PHARMACY REFUND"}):
        frappe.log(f"Refund Journal Entry with bill_no {bill_no} already exists.")
        return

    # Patient & Customer
    customer_name = refund_data["payer_name"]
    payer_type = refund_data["payer_type"]
    patient_name = refund_data["patient_name"]
    gender = refund_data["patient_gender"]

    customer = get_or_create_customer(customer_name,payer_type)
    patient = get_or_create_patient(patient_name, gender)

    treating_department_name = refund_data.get("treating_department_name", "Default Dept")
    facility_name = refund_data.get("facility_name", "Default Dept")
    store_name = refund_data.get("StoreName")
    cost_center = get_or_create_cost_center(store_name)
    # cost_center = get_or_create_cost_center(treating_department_name)

    # Amounts (Refund)
    item_rate = refund_data["patient_refund_amount"]
    tax_amount = refund_data.get("tax", 0)
    authorized_amount = refund_data.get("authorized_amount", 0)
    discount_amount = refund_data.get("discount", 0)
    round_off = refund_data.get("roundOff", 0)

    # --- Fetch accounts dynamically from Company ---
    company = frappe.defaults.get_user_default("Company")
    company_doc = frappe.get_doc("Company", company)

    credit_account = company_doc.default_income_account     # opposite of billing
    debit_account = company_doc.default_receivable_account
    cash_account = get_or_create_cash_account(store_name)
    bank_account = company_doc.default_bank_account
    stock_acc = get_or_create_stock_account(store_name)
    vat_account = "VAT 5% - OP"
    default_expense_account = company_doc.default_expense_account

    total_uepr = sum(
        (item.get("ueprValue") or 0)
        for item in refund_data.get("item_details", [])
    )

    je_accounts = [
        # {
        #     "account": debit_account,   # Reverse sales (debit sales account)
        #     "debit_in_account_currency": item_rate,
        #     "credit_in_account_currency": 0,
        #     "cost_center": cost_center
        # },
        {
            "account": credit_account,  # Credit receivable/customer
            "debit_in_account_currency": item_rate,
            "credit_in_account_currency": 0,
            # "party_type": "Customer",
            # "party": customer
        },
    ]

    # Tax reversal
    if tax_amount > 0:
        je_accounts.append({
            "account": vat_account,
            "debit_in_account_currency": tax_amount,
            "credit_in_account_currency": 0,
        })

    # UEPR reversal
    if total_uepr > 0:
        je_accounts.extend([
            {
                "account": stock_acc,
                "debit_in_account_currency": total_uepr,
                "credit_in_account_currency": 0,
                "cost_center": cost_center
            },
            {
                "account": default_expense_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": total_uepr,
                "cost_center": cost_center
            }
        ])

    # Payment Modes (Refunds)
    for payment in payment_details:
        mode = payment["payment_mode_code"].lower()
        amount = payment.get("amount", 0.0)
        if amount <= 0:
            continue

        if mode == "cash":
            je_accounts.append({
                "account": cash_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
                "cost_center": cost_center
            })
        elif mode == "credit":
            je_accounts.append({
                "account": debit_account,
                "debit_in_account_currency":0,
                "credit_in_account_currency":amount,
                "party_type": "Customer",
                "party": customer,
                "cost_center": cost_center
            })
        elif mode in ["upi", "card_payment", "bank"]:
            je_accounts.append({
                "account": bank_account,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
                "cost_center": cost_center
            })
        elif mode == "ip advance":
            je_accounts.append({
                "account": "Advance Received - OP",
                "debit_in_account_currency": 0,
                "credit_in_account_currency": amount,
                "cost_center": cost_center
            })

    # --- Create Refund JE ---
    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "naming_series": "KX-JV-.YYYY.-",
        "voucher_type": "Journal Entry",
        "posting_date": formatted_date,
        "posting_time": posting_time,
        "custom_modification_time": mod_time,  # store mod time
        "custom_patient_name": patient_name,
        "custom_bill_number": bill_no,
        "custom_bill_category": "PHARMACY REFUND",
        "custom_payer_name": customer_name,
        "custom_uhid": refund_data["uhId"],
        "custom_receipt_no": receipt_no,
        "custom_admission_id": refund_data["admissionId"],
        "custom_admission_type": refund_data["admissionType"],
        "company": company,
        "custom_store": store_name,
        "custom_discount":discount_amount,
        "custom_round_off": round_off,
        "custom_facility_name": facility_name,
        "user_remark": f"Pharmacy Refund for bill no {bill_no}",
        "accounts": je_accounts
    })

    try:
        je.insert(ignore_permissions=True)
        je.submit()
        frappe.db.commit()
        frappe.log(f"Refund Journal Entry created successfully with bill_no: {bill_no}")
        return je.name
    except Exception as e:
        frappe.log_error(f"Failed to create refund Journal Entry: {e}")
        return None
