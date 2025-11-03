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

def get_jwt_token_for_facility(headers):
    response = requests.post(TOKEN_URL, headers=headers)
    if response.status_code == 200:
        return response.json().get("jwttoken")
    else:
        frappe.throw(f"Failed to fetch JWT token for facility {headers['facilityId']}: {response.status_code} - {response.text}")

def fetch_op_billing(jwt_token, from_date, to_date, headers):
    headers_billing = headers.copy()
    headers_billing["Authorization"] = f"Bearer {jwt_token}"
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch Stock Transfer data for facility {headers['facilityId']}: {response.status_code} - {response.text}")


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
        print("acc--",stock_acc_name)
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
    stock_acc_name = f"STOCK IN HAND - {facility_name} - OP"
    
    # Check if the cost center already exists by full name
    existing = frappe.db.exists("Account", stock_acc_name)
    if existing:
        print("acc2--",stock_acc_name)
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

@frappe.whitelist()
def main():
    try:
        settings = frappe.get_single("Karexpert Settings")
        billing_row = frappe.get_value(
            "Karexpert  Table",
            {"billing_type": billing_type},
            ["client_code", "integration_key", "x_api_key"],
            as_dict=True
        )

        facility_list = frappe.get_all("Facility ID", filters={"parent": settings.name}, fields=["facility_id"])
        print("facility ---",facility_list)
        for row in facility_list:
            facility_id = row["facility_id"]

            # Prepare headers per facility
            headers_token = {
                "Content-Type": "application/json",
                "clientCode": billing_row["client_code"],
                "integrationKey": billing_row["integration_key"],
                "facilityId": facility_id,
                "messageType": "request",
                "x-api-key": billing_row["x_api_key"]
            }

            jwt_token = get_jwt_token_for_facility(headers_token)

            # Date logic
            to_date_raw = settings.get("date")
            t_date = getdate(to_date_raw) if to_date_raw else add_days(nowdate(), -4)
            no_of_days = cint(settings.get("no_of_days") or 25)
            f_date = add_days(t_date, -no_of_days)
            gmt_plus_4 = timezone(timedelta(hours=4))
            from_date = int(datetime.combine(f_date, time.min, tzinfo=gmt_plus_4).timestamp() * 1000)
            to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)

            billing_data = fetch_op_billing(jwt_token, from_date, to_date, headers_token)
            frappe.log(f"Stock Transfer data fetched for facility {facility_id}")

            # Process billing data per facility
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
                    continue

                if not key:
                    frappe.log(f"⚠️ Missing key for record {record.get('id')}")
                    continue

                if key not in grouped_data:
                    grouped_data[key] = {"records": [], "category": category}
                grouped_data[key]["records"].append(record)

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
    facility_name = first_record.get("facility_name")

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
    je.custom_facility_name = facility_name
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
