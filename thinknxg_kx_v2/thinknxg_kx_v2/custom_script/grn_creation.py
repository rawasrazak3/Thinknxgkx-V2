import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v2.thinknxg_kx_v2.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "GRN CREATION SUMMARY"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")
facility_id = settings.get("facility_id")

# Fetch row details based on billing type
billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
                                ["client_code", "integration_key", "x_api_key"], as_dict=True)
print("---billing row",billing_row)
 
headers_token = fetch_api_details(billing_type)
# TOKEN_URL = "https://metro.kxstage.com/external/api/v1/token"
# BILLING_URL = "https://metro.kxstage.com/external/api/v1/integrate"

# headers_token = {
#     "Content-Type": "application/json",
#     "clientCode": "METRO_THINKNXG_MM",
#     "facilityId": "METRO_THINKNXG",
#     "messageType": "request",
#     "integrationKey": "GRN_CREATION_SUMMARY",
#     "x-api-key": "dkjsag7438hgf76"
# }

def get_jwt_token():
    response = requests.post(TOKEN_URL, headers=headers_token)
    if response.status_code == 200:
        return response.json().get("jwttoken")
    else:
        frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

def fetch_op_billing(jwt_token, from_date, to_date):
    print("---entered function--")
    # headers_billing = {
    #     "Content-Type": "application/json",
    #     "clientCode": "METRO_THINKNXG_MM",
    #     "integrationKey": "GRN_CREATION_SUMMARY",
    #     "Authorization": f"Bearer {jwt_token}"
    # }
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
        frappe.throw(f"Failed to fetch GRN data: {response.status_code} - {response.text}")

def get_or_create_supplier(supplier_code, supplier_name):
    # Check if supplier already exists by custom supplier code
    existing_supplier = frappe.db.exists("Supplier", {"custom_supplier_code": supplier_code,"disabled":0})
    
    if existing_supplier:
        return existing_supplier
    
    # Create new supplier if not found
    try:
        supplier = frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": supplier_name,
            "custom_supplier_code": supplier_code,
            "supplier_group": "All Supplier Groups",  # or replace with your default group
            "supplier_type": "Company"  # optional, can change to "Individual" if needed
        })
        supplier.insert(ignore_permissions=True)
        frappe.db.commit()
        return supplier.name
    except Exception as e:
        frappe.log_error(f"Error creating supplier for code '{supplier_code}': {str(e)}", "Supplier Creation Error")
        return None

def get_existing_supplier(supplier_code):
    existing_supplier = frappe.db.exists("Supplier", {"custom_supplier_code": supplier_code,"disabled":0})
    
    if existing_supplier:
        return existing_supplier
    else:
        frappe.log_error(f"Supplier with code '{supplier_code}' not found.", "Missing Supplier")
        return None

def get_or_create_cost_center(facility_name):
    cost_center_name = f"{facility_name} - OP"
    
    # Check if the cost center already exists by full name
    existing = frappe.db.exists("Cost Center", cost_center_name)
    if existing:
        return cost_center_name
    
    # # Determine parent based on facility_name
    # if facility_name == "LABORATORY(G) - MH":
    #     parent_cost_center = "PARAMEDICAL(G) - MH"
    # else:
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
        "account_name": facility_name,  
        "account_type": "Stock",           
        "parent_account": parent_cost_center,
        "company": "Oxygen Pharmacy"
    })
    stock_acc.insert(ignore_permissions=True)
    frappe.db.commit()
    frappe.msgprint(f"Account '{stock_acc_name}' created under '{parent_cost_center}'")
    
    return stock_acc_name  # Always return the full account name with suffix

def get_default_warehouse():
    return frappe.db.get_single_value("Stock Settings", "default_warehouse") or "Stores - K"

def create_journal_entry(billing_data):
    print("----creating journal----")
    try:
        # Convert bill date to GMT+4
        date_ts = float(billing_data["billDate"])
        datetimes = date_ts / 1000.0
        gmt_plus_4 = timezone(timedelta(hours=4))
        dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
        formatted_date = dt.strftime('%Y-%m-%d')
        posting_time = dt.strftime('%H:%M:%S')

        bill_no = billing_data["billNo"]
        grn_number = billing_data["grn_number"]
        store_name = billing_data["storeName"]

        # Check if already exists
        existing_jv = frappe.db.exists("Journal Entry", {"custom_grn_number": grn_number,"docstatus":1})
        if existing_jv:
            frappe.log(f"Journal Entry with GRN {grn_number} already exists.")
            return

        supplier_code = billing_data["supplierCode"]
        supplier_name = billing_data["supplierName"]
        # supplier = get_or_create_supplier(supplier_code,supplier_name)
        supplier = get_existing_supplier(supplier_code)
        # if not supplier:
            # frappe.throw(f"Supplier {supplier_code} not found, cannot create Journal Entry")

        total_net_amount = float(billing_data.get("totalNetAmount", 0) or 0.0)
        total_tax = float(billing_data.get("total_tax", 0) or 0.0)
        bill_amount = float(billing_data.get("billAmount", 0) or 0.0)

        facility_name = billing_data.get("storeName")
        if facility_name:
            cost_center = get_or_create_cost_center(facility_name)
        # else:
        #     cost_center = "HEADOFFICE - K"

        # Fetch company defaults
        company = frappe.defaults.get_user_default("Company")
        company_defaults = frappe.get_doc("Company", company)
        default_payable = company_defaults.default_payable_account
        default_inventory = company_defaults.default_inventory_account
        stock_acc = get_or_create_stock_account(facility_name)
        if not default_payable or not default_inventory:
            frappe.throw("Please set Default Payable Account and Default Inventory Account in Company master.")
        vat_account = "VAT 5% - OP"

        # Fetch Supplier Name
        supplier_doc = frappe.get_doc("Supplier", supplier)
        supplier_name = supplier_doc.supplier_name

        # Build Journal Entry (Basic Example: Debit Expense / Credit Supplier)
        journal_entry = {
            "doctype": "Journal Entry",
            "posting_date": formatted_date,
            "posting_time": posting_time,
            "naming_series": "KX-JV-.YYYY.-",
            "custom_bill_category": "GRN",
            "company": company,
            "custom_bill_number": bill_no,
            "custom_grn_number": grn_number,
            "custom_store": store_name,
            "custom_supplier_name": supplier_name,
            "user_remark": f"Auto-created from GRN {grn_number}",
            "accounts": []
        }

        # Credit Payable (total bill amount)
        journal_entry["accounts"].append({
            "account": default_payable,
            "party_type": "Supplier",
            "party": supplier,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": bill_amount,
            # "cost_center": cost_center
        })

        # Debit Inventory (net amount)
        if total_net_amount:
            journal_entry["accounts"].append({
                "account": stock_acc,
                "debit_in_account_currency": total_net_amount-total_tax,
                "credit_in_account_currency": 0,
                "cost_center": cost_center
            })

        # Debit VAT (if applicable)
        if total_tax:
            journal_entry["accounts"].append({
                "account": vat_account,
                "debit_in_account_currency": total_tax,
                "credit_in_account_currency": 0,
                # "cost_center": cost_center
            })

        #     "accounts": [
        #         {
        #             "account": default_inventory,  # Replace with your expense account
        #             "debit_in_account_currency": bill_amount,
        #             "credit_in_account_currency": 0,
        #             "cost_center": cost_center
        #         },
        #         {
        #             "account": default_payable,  # Supplier payable account
        #             "party_type": "Supplier",
        #             "party": supplier,
        #             "debit_in_account_currency": 0,
        #             "credit_in_account_currency": bill_amount,
        #             "cost_center": cost_center
        #         }
        #     ]
        # }

        # if total_tax:
        #     journal_entry["accounts"].append({
        #         "account": "2370 - VAT 5% - MH",
        #         "debit_in_account_currency": total_tax,
        #         "credit_in_account_currency": 0,
        #         "cost_center": cost_center
        #     })

        # Save and Submit
        doc = frappe.get_doc(journal_entry)
        doc.insert(ignore_permissions=True)
        doc.submit()
        frappe.db.commit()

        frappe.log(f"Journal Entry created successfully for GRN: {grn_number}")

    except Exception as e:
        frappe.log_error(f"Failed to create Journal Entry: {e}")


@frappe.whitelist()
def main():
    try:
        print("--main--")
        jwt_token = get_jwt_token()
        frappe.log("JWT Token fetched successfully.")

        # from_date = 1751341619000  
        # to_date = 1754654136000    
        # Fetch dynamic date and number of days from settings
        settings = frappe.get_single("Karexpert Settings")
        # Get to_date from settings or fallback to nowdate() - 4 days
        to_date_raw = settings.get("date")
        if to_date_raw:
            t_date = getdate(to_date_raw)
        else:
            t_date = add_days(nowdate(), -4)

        # Get no_of_days from settings and calculate from_date
        no_of_days = cint(settings.get("no_of_days") or 25)  # default 3 days if not set
        f_date = add_days(t_date, -no_of_days)
        # Define GMT+4 timezone
        gmt_plus_4 = timezone(timedelta(hours=4))

        # Convert to timestamps in milliseconds for GMT+4
        from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
        billing_data = fetch_op_billing(jwt_token, from_date, to_date)

        frappe.log("GRN Billing data fetched successfully.")

        for billing in billing_data.get("jsonResponse", []):
            create_journal_entry(billing)

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()
