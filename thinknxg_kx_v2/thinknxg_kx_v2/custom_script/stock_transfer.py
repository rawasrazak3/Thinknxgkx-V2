import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v2.thinknxg_kx_v2.doctype.karexpert_settings.karexpert_settings import fetch_api_details
billing_type = "IF STOCK TRANSFER DETAIL"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")
facility_id = settings.get("facility_id")

# Fetch row details based on billing type
billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
                                ["client_code", "integration_key", "x_api_key"], as_dict=True)


headers_token = fetch_api_details(billing_type)
# TOKEN_URL = "https://metro.kxstage.com/external/api/v1/token"
# BILLING_URL = "https://metro.kxstage.com/external/api/v1/integrate"
# headers_token = {
#     "Content-Type": "application/json",
#     # "clientCode": "METRO_THINKNXG_FI",
#     "clientCode": billing_row["client_code"],
#     # "facilityId": "METRO_THINKNXG",
#     "facilityId": facility_id,
#     "messageType": "request",
#     # "integrationKey": "OP_BILLING",
#     "integrationKey": billing_row["integration_key"],
#     # "x-api-key": "kfhgjfgjf0980gdfgfds"
#     "x-api-key": billing_row["x_api_key"]
# }

def get_jwt_token():
    response = requests.post(TOKEN_URL, headers=headers_token)
    if response.status_code == 200:
        return response.json().get("jwttoken")
    else:
        frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

def fetch_op_billing(jwt_token, from_date, to_date):
    print("----fetching---")
    headers_billing = {
        "Content-Type": headers_token["Content-Type"],
        # "clientCode": "METRO_THINKNXG_FI",
        "clientCode": headers_token["clientCode"],
        # "integrationKey": "OP_BILLING",
        "integrationKey": headers_token["integrationKey"],
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        print("---failed--")
        frappe.throw(f"Failed to fetch Stock Transfer data: {response.status_code} - {response.text}")

def get_or_create_customer(customer_name):
    existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name})
    if existing_customer:
        return existing_customer
    
    customer = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": customer_name,
        "customer_group": "Individual",
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


def get_or_create_cost_center1(facility_name):
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

def get_or_create_cost_center2(facility_name):
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

def get_or_create_stock_account1(facility_name):
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
        "parent_account": parent_cost_center,
        "company": "Oxygen Pharmacy"
    })
    stock_acc.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"Account '{stock_acc_name}' created under '{parent_cost_center}'")
    
    return stock_acc_name  # Always return the full cost center name with suffix

def get_or_create_stock_account2(facility_name):
    stock_acc_name = f"STOCK IN HAND {facility_name} - OP"
    
    # Check if the cost center already exists by full name
    existing = frappe.db.exists("Account", stock_acc_name)
    if existing:
        return stock_acc_name
    
   
    parent_cost_center = "Stock Assets - OP"

    # Create new cost center with full cost_center_name as document name
    stock_acc = frappe.get_doc({
        "doctype": "Account",
        "account_name": f"STOCK IN HAND - {facility_name}",               
        "parent_account": parent_cost_center,
        "company": "Oxygen Pharmacy"
    })
    stock_acc.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"Account '{stock_acc_name}' created under '{parent_cost_center}'")
    
    return stock_acc_name  # Always return the full cost center name with suffix

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
#         billing_data = fetch_op_billing(jwt_token, from_date, to_date)
#         frappe.log("OP Billing data fetched successfully.")

#         for billing in billing_data.get("jsonResponse", []):
#             create_journal_entry_from_billing(billing)

#     except Exception as e:
#         frappe.log_error(f"Error: {e}")

# if __name__ == "__main__":
#     main()

# def create_journal_entry_from_billing(billing_data):
#     print("----creating journal----")
#     # bill_no = billing_data["bill_no"]
#     transfer_type = billing_data["transfer_type"]
#     date = billing_data["g_creation_time"]
#     datetimes = date / 1000.0

#     # Define GMT+4
#     gmt_plus_4 = timezone(timedelta(hours=4))
#     dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
#     formatted_date = dt.strftime('%Y-%m-%d')
#     posting_time = dt.strftime('%H:%M:%S')

#     if frappe.db.exists("Journal Entry", { "custom_indent_no": billing_data["indentno"],"custom_bill_category" : "STOCK TRANSFER","docstatus": ["=", 1]}):
#         frappe.log(f"Journal Entry with bill_no  already exists.")
#         return
#     elif frappe.db.exists("Journal Entry", { "custom_return_no": billing_data["return_no"],"custom_bill_category" : "STOCK RETURN","docstatus": ["=", 1]}):
#         frappe.log(f"Journal Entry with bill_no  already exists.")
#         return

#     # # Patient & Customer
#     # customer_name = billing_data["payer_name"]
#     # patient_name = billing_data["patient_name"]
#     # gender = billing_data["patient_gender"]

#     # customer = get_or_create_customer(customer_name)
#     # patient = get_or_create_patient(patient_name, gender)

#     from_facility_name = billing_data.get("facility_name", "Default Dept")
#     to_facility_name = billing_data.get("to_facility_name", "Default Dept")
#     from_store_name = billing_data.get("fromStoreName")
#     to_store_name = billing_data.get("toStoreName")
#     cost_center1 = get_or_create_cost_center1(from_store_name)
#     cost_center2 = get_or_create_cost_center1(to_store_name)

#     # # Amounts
#     # round_off = billing_data.get("roundOff", 0)
#     # if round_off < 0:
#     #     print("roundoff----", round_off)
#     #     item_rate = billing_data["total_amount"]+round_off
#     #     print("item rate----",item_rate)
#     # else:
#     #     item_rate = billing_data["selling_amount"]
#     # authorized_amount = billing_data.get("authorized_amount", 0)
#     # discount_amount = billing_data["selling_amount"] - billing_data["total_amount"]
#     # tax_amount = billing_data["tax"]

#     # --- Fetch accounts dynamically from Company ---
#     company = frappe.defaults.get_user_default("Company")
#     company_doc = frappe.get_doc("Company", company)

#     # debit_account = company_doc.default_receivable_account
#     # credit_account = company_doc.default_income_account
#     # cash_account = company_doc.default_cash_account
#     # bank_account = company_doc.default_bank_account
#     stock_acc1 = get_or_create_stock_account1(from_store_name)
#     stock_acc2 = get_or_create_stock_account1(to_store_name)

#     # vat_account = getattr(company_doc, "default_tax_account", None) or frappe.db.get_single_value("Company", "default_tax_account")
#     vat_account = "VAT 5% - OP"
#     # default_expense_account = company_doc.default_expense_account
#     # default_stock_in_hand = company_doc.default_inventory_account
#     # # discount_account = getattr(company_doc, "default_discount_account", None) or frappe.db.get_single_value("Company", "default_discount_account")

#     # if not debit_account or not credit_account:
#     #     frappe.throw("Please set Default Receivable and Income accounts in Company settings.")

#     # total_uepr = sum(
#     #     (item.get("ueprValue") or 0)
#     #     for item in billing_data.get("item_details", [])
#     # )
#     total_uepr = billing_data["ueprValue"]

#     je_accounts = [
#         {
#             "account": stock_acc1,
#             "debit_in_account_currency": 0,
#             "credit_in_account_currency": total_uepr,
#             "cost_center": cost_center1
#         },
#         {
#             "account": stock_acc2,
#             "debit_in_account_currency": total_uepr,
#             "credit_in_account_currency": 0,
#             "cost_center": cost_center2
#         }
#     ]
    




#     # # Handling Credit Payment Mode
#     # credit_payment = next((p for p in payment_details if p["payment_mode_code"].lower() == "credit"), None)
#     # if authorized_amount>0:
#     #     je_accounts.append({
#     #         "account": debit_account,  # Replace with actual debtors account
#     #         "party_type": "Customer",
#     #         "party": customer,
#     #         "debit_in_account_currency": authorized_amount,
#     #         "credit_in_account_currency": 0,
#     #         "cost_center": cost_center
#     #     })
        

#     # # Handling Cash Payment Mode
#     # for payment in payment_details:
#     #     if payment["payment_mode_code"].lower() == "cash":
#     #         je_accounts.append({
#     #             "account": cash_account,  # Replace with actual cash account
#     #             "debit_in_account_currency": payment["amount"],
#     #             "credit_in_account_currency": 0,
#     #             "cost_center": cost_center
#     #         })

#     # # Handling Advance Payment Mode
#     # for payment in payment_details:
#     #     if payment["payment_mode_code"].lower() == "ip advance":
#     #         je_accounts.append({
#     #             "account": "Advance Received - K",  # Replace with actual advance account
#     #             "debit_in_account_currency": payment["amount"],
#     #             "credit_in_account_currency": 0,
#     #             "cost_center": cost_center
#     #         })

#     # # Handling Other Payment Modes (UPI, Card, etc.)
#     # bank_payment_total = sum(
#     #     p["amount"] for p in payment_details if p["payment_mode_code"].lower() not in ["cash", "credit","IP ADVANCE"]
#     # )
#     # if bank_payment_total > 0:
#     #     je_accounts.append({
#     #         "account": bank_account,  # Replace with actual bank account
#     #         "debit_in_account_currency": bank_payment_total,
#     #         "credit_in_account_currency": 0,
#     #         "cost_center": cost_center
#     #         # "reference_type": "Sales Invoice",
#     #         # "reference_name":sales_invoice_name
#     #     })

#     # # Tax line
#     # if tax_amount > 0:
#     #     if not vat_account:
#     #         frappe.throw("Please set Default Tax Account in Company settings.")
#     #     je_accounts.append({
#     #         "account": vat_account,
#     #         "debit_in_account_currency": 0,
#     #         "credit_in_account_currency": tax_amount,
#     #     })
#     # if total_uepr > 0:
#     #     je_accounts.extend([
#     #         {
#     #             "account": default_expense_account,
#     #             "debit_in_account_currency": total_uepr,
#     #             "credit_in_account_currency": 0,
#     #             "cost_center": cost_center
#     #         },
#     #         {
#     #             "account": stock_acc,
#     #             "debit_in_account_currency": 0,
#     #             "credit_in_account_currency": total_uepr,
#     #             "cost_center": cost_center
#     #         }
#     #     ])


#     # # Discount line
#     # if discount_amount > 0:
#     #     if not discount_account:
#     #         frappe.throw("Please set Default Discount Account in Company settings.")
#     #     je_accounts.append({
#     #         "account": discount_account,
#     #         "debit_in_account_currency": discount_amount,
#     #         "credit_in_account_currency": 0,
#     #         "cost_center": cost_center
#     #     })

#     # --- Create Journal Entry ---
#     je = frappe.get_doc({
#         "doctype": "Journal Entry",
#         "naming_series": "KX-JV-.YYYY.-",
#         "voucher_type": "Journal Entry",
#         "posting_date": formatted_date,
#         "posting_time": posting_time,
#         "custom_bill_category" : "STOCK TRANSFER" if transfer_type=="stock_transfer" else "STOCK RETURN",
#         "custom_indent_no": billing_data["indentno"] if transfer_type=="stock_transfer" else None,
#         "custom_issue_no": billing_data["issueno"] if transfer_type=="stock_transfer" else None,
#         "company": company,
#         "user_remark": f"Stock Transfer" ,
#         "accounts": je_accounts,
#     })
#     #For stock Return
#     if transfer_type == "INDENT RETURN":
#         je.custom_return_no = billing_data.get("return_no")

#     try:
#         je.insert(ignore_permissions=True)
#         je.submit()
#         frappe.db.commit()
#         frappe.log(f"Stock Transfer Journal created successfully")
#         return je.name
#     except Exception as e:
#         frappe.log_error(f"Failed to create Journal Entry: {e}")
#         return None


@frappe.whitelist()
def main():
    try:
        jwt_token = get_jwt_token()
        frappe.log("JWT Token fetched successfully.")

        settings = frappe.get_single("Karexpert Settings")
        to_date_raw = settings.get("date")
        t_date = getdate(to_date_raw) if to_date_raw else add_days(nowdate(), -4)

        no_of_days = cint(settings.get("no_of_days") or 25)
        f_date = add_days(t_date, -no_of_days)

        gmt_plus_4 = timezone(timedelta(hours=4))
        from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

        billing_data = fetch_op_billing(jwt_token, from_date, to_date)
        frappe.log("Stock Transfer data fetched successfully.")

        # Step 1: Group by issueno or returnno
        grouped_data = {}
        for record in billing_data.get("jsonResponse", []):
            transfer_type = record.get("transfer_type", "").lower()

            if transfer_type == "stock_transfer":
                key = record.get("issueno") or record.get("indentno")
                category = "STOCK TRANSFER"
            elif transfer_type == "indent return":
                key = record.get("return_no")
                category = "STOCK RETURN"
            else:
                continue  # skip invalid records

            if not key:
                frappe.log(f"⚠️ Missing key for record {record.get('id')}")
                continue

            if key not in grouped_data:
                grouped_data[key] = {"records": [], "category": category}
            grouped_data[key]["records"].append(record)

        # Step 2: Process each group once
        for key, data in grouped_data.items():
            create_journal_entry_from_billing_group(key, data["records"], data["category"])

    except Exception as e:
        frappe.log_error(f"Error in Stock Transfer Import: {frappe.get_traceback()}")
        frappe.throw(f"Stock Transfer Sync Failed: {e}")


def create_journal_entry_from_billing_group(key, records, category):
    """Creates a single Journal Entry for all items with the same issueno/returnno"""
    if category == "STOCK TRANSFER":
        if frappe.db.exists("Journal Entry", {"custom_issue_no": key, "custom_bill_category": category, "docstatus": 1}):
            frappe.log(f"Journal Entry for Issueno {key} already exists.")
            return
    elif category == "STOCK RETURN":
        if frappe.db.exists("Journal Entry", {"custom_return_no": key, "custom_bill_category": category, "docstatus": 1}):
            frappe.log(f"Journal Entry for Returnno {key} already exists.")
            return

    first_record = records[0]
    transfer_type = first_record.get("transfer_type")
    from_store_name = first_record.get("fromStoreName")
    to_store_name = first_record.get("toStoreName")
    indent_no = first_record.get("indentno")

    cost_center1 = get_or_create_cost_center1(from_store_name)
    cost_center2 = get_or_create_cost_center2(to_store_name)
    stock_acc1 = get_or_create_stock_account1(from_store_name)
    stock_acc2 = get_or_create_stock_account2(to_store_name)

    # Use creation date of first record for JE posting
    date_ms = first_record.get("g_creation_time")
    dt = datetime.fromtimestamp(date_ms / 1000.0, timezone(timedelta(hours=4)))
    posting_date = dt.strftime('%Y-%m-%d')
    posting_time = dt.strftime('%H:%M:%S')

    total_value = sum([float(r.get("ueprValue", 0)) for r in records])

    je = frappe.new_doc("Journal Entry")
    je.naming_series = 'KX-JV-.YYYY.-'
    je.posting_date = posting_date
    je.posting_time = posting_time
    je.company = "Oxygen Pharmacy"
    je.custom_bill_category = category
    je.custom_issue_no = key if category == "STOCK TRANSFER" else None
    je.custom_indent_no = indent_no
    je.custom_return_no = key if category == "STOCK RETURN" else None
    je.voucher_type = "Journal Entry"
    je.user_remark = f"{category} for {key}"

    # Add entries
    if category == "STOCK TRANSFER":
        # From store → credit
        je.append("accounts", {
            "account": stock_acc1,
            "credit_in_account_currency": total_value,
            "cost_center": cost_center1
        })
        # To store → debit
        je.append("accounts", {
            "account": stock_acc2,
            "debit_in_account_currency": total_value,
            "cost_center": cost_center2
        })

    elif category == "STOCK RETURN":
        # Reverse for return
        je.append("accounts", {
            "account": stock_acc2,
            "credit_in_account_currency": total_value,
            "cost_center": cost_center2
        })
        je.append("accounts", {
            "account": stock_acc1,
            "debit_in_account_currency": total_value,
            "cost_center": cost_center1
        })

    je.save(ignore_permissions=True)
    je.submit()

    frappe.db.commit()
    frappe.log(f"Journal Entry {je.name} created for {category} ({key}) with {len(records)} items.")
