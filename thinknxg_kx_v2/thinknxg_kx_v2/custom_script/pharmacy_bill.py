import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v2.thinknxg_kx_v2.doctype.karexpert_settings.karexpert_settings import fetch_api_details
billing_type = "OP PHARMACY BILLING"
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
        frappe.throw(f"Failed to fetch OP Pharmacy Billing data: {response.status_code} - {response.text}")

# def get_or_create_customer(customer_name):
#     existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name})
#     if existing_customer:
#         return existing_customer
    
#     customer = frappe.get_doc({
#         "doctype": "Customer",
#         "customer_name": customer_name,
#         "customer_group": "Individual",
#         "territory": "All Territories"
#     })
#     customer.insert(ignore_permissions=True)
#     frappe.db.commit()
#     return customer.name
def get_or_create_customer(customer_name, payer_type=None):
    # Check if the customer already exists
    existing_customer = frappe.db.exists("Customer", {"customer_name": customer_name , "customer_group":payer_type})
    if existing_customer:
        return existing_customer

    # Determine customer group based on payer_type
    if payer_type:
        payer_type = payer_type.lower()
        if payer_type == "tpa":
            customer_group = "TPA"
        elif payer_type == "cash":
            customer_group = "Cash"
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


# def get_or_create_cost_center(department, sub_department):
#     parent_cost_center_name = f"{department}(G)"
#     sub_cost_center_name = f"{sub_department}"

#     # Check if parent cost center exists, if not, create it
#     existing_parent = frappe.db.exists("Cost Center", {"cost_center_name": parent_cost_center_name})
#     if not existing_parent:
#         parent_cost_center = frappe.get_doc({
#             "doctype": "Cost Center",
#             "cost_center_name": parent_cost_center_name,
#             "parent_cost_center": "METRO HOSPITALS & POLYCLINCS LLC - MH",  # Root level
#             "is_group":1,
#             "company": frappe.defaults.get_defaults().get("company")
#         })
#         parent_cost_center.insert(ignore_permissions=True)
#         frappe.db.commit()
#         existing_parent = parent_cost_center.name

#     # Check if sub cost center exists, if not, create it
#     existing_sub = frappe.db.exists("Cost Center", {"cost_center_name": sub_cost_center_name})
#     if existing_sub:
#         return existing_sub

#     sub_cost_center = frappe.get_doc({
#         "doctype": "Cost Center",
#         "cost_center_name": sub_cost_center_name,
#         "parent_cost_center": existing_parent,
#         "company": frappe.defaults.get_defaults().get("company")
#     })
#     sub_cost_center.insert(ignore_permissions=True)
#     frappe.db.commit()

#     return sub_cost_center.name

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
        "account_name": stock_acc_name,  
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


@frappe.whitelist()
def main():
    try:
        jwt_token = get_jwt_token()
        frappe.log("JWT Token fetched successfully.")

        # from_date = 1672531200000  
        # to_date = 1940009600000  
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
        print("---f", from_date)
        to_date = int(datetime.combine(t_date, time.max, tzinfo=gmt_plus_4).timestamp() * 1000)
        print("----t", to_date)
        billing_data = fetch_op_billing(jwt_token, from_date, to_date)
        frappe.log("OP Billing data fetched successfully.")

        for billing in billing_data.get("jsonResponse", []):
            create_journal_entry_from_billing(billing["pharmacy_billing"])

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()

def create_journal_entry_from_billing(billing_data):
    print("----creating journal----")
    bill_no = billing_data["bill_no"]
    payment_details = billing_data.get("payment_transaction_details", [])
    date = billing_data["g_creation_time"]
    datetimes = date / 1000.0

    # Define GMT+4
    gmt_plus_4 = timezone(timedelta(hours=4))
    dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
    formatted_date = dt.strftime('%Y-%m-%d')
    posting_time = dt.strftime('%H:%M:%S')

    if frappe.db.exists("Journal Entry", {"custom_bill_number": bill_no, "docstatus": ["!=", 2]}):
        frappe.log(f"Journal Entry with bill_no {bill_no} already exists.")
        return

    # Patient & Customer
    customer_name = billing_data["payer_name"]
    patient_name = billing_data["patient_name"]
    gender = billing_data["patient_gender"]
    payer_type = billing_data["payer_type"]

    customer = get_or_create_customer(customer_name,payer_type)
    patient = get_or_create_patient(patient_name, gender)

    facility_name = billing_data.get("facility_name", "Default Dept")
    store_name = billing_data.get("StoreName")
    cost_center = get_or_create_cost_center(store_name)

    # Amounts
    discount_amount = billing_data["selling_amount"] - billing_data["total_amount"]
    round_off = billing_data.get("roundOff", 0)
    if round_off < 0:
        item_rate = billing_data["total_amount"]+round_off
    elif discount_amount >0:
        item_rate = billing_data["selling_amount"] - discount_amount
    else:
        item_rate = billing_data["selling_amount"]
    authorized_amount = billing_data.get("authorized_amount", 0)
    tax_amount = billing_data["tax"]

    # --- Fetch accounts dynamically from Company ---
    company = frappe.defaults.get_user_default("Company")
    company_doc = frappe.get_doc("Company", company)

    debit_account = company_doc.default_receivable_account
    credit_account = company_doc.default_income_account
    cash_account = get_or_create_cash_account(store_name)
    bank_account = company_doc.default_bank_account
    stock_acc = get_or_create_stock_account(store_name)

    # vat_account = getattr(company_doc, "default_tax_account", None) or frappe.db.get_single_value("Company", "default_tax_account")
    vat_account = "VAT 5% - OP"
    default_expense_account = company_doc.default_expense_account
    default_stock_in_hand = company_doc.default_inventory_account
    # discount_account = getattr(company_doc, "default_discount_account", None) or frappe.db.get_single_value("Company", "default_discount_account")

    if not debit_account or not credit_account:
        frappe.throw("Please set Default Receivable and Income accounts in Company settings.")

    total_uepr = sum(
        (item.get("ueprValue") or 0)
        for item in billing_data.get("item_details", [])
    )

    je_accounts = [
        # {
        #     "account": debit_account,
        #     "party_type": "Customer",
        #     "party": customer,
        #     "debit_in_account_currency": item_rate + tax_amount,
        #     "credit_in_account_currency": 0,
        #     "cost_center": cost_center
        # },
        {
            "account": credit_account,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": item_rate,
            "cost_center": cost_center
        },
    ]
    # Handling Credit Payment Mode
    credit_payment = next((p for p in payment_details if p["payment_mode_code"].lower() == "credit"), None)
    if authorized_amount>0:
        je_accounts.append({
            "account": debit_account,  # Replace with actual debtors account
            "party_type": "Customer",
            "party": customer,
            "debit_in_account_currency": authorized_amount,
            "credit_in_account_currency": 0,
            "cost_center": cost_center
        })
        

    # Handling Cash Payment Mode
    for payment in payment_details:
        if payment["payment_mode_code"].lower() == "cash":
            je_accounts.append({
                "account": cash_account,  # Replace with actual cash account
                "debit_in_account_currency": payment["amount"],
                "credit_in_account_currency": 0,
                "cost_center": cost_center
            })

    # Handling Advance Payment Mode
    for payment in payment_details:
        if payment["payment_mode_code"].lower() == "ip advance":
            je_accounts.append({
                "account": "Advance Received - K",  # Replace with actual advance account
                "debit_in_account_currency": payment["amount"],
                "credit_in_account_currency": 0,
                "cost_center": cost_center
            })

    # Handling Other Payment Modes (UPI, Card, etc.)
    bank_payment_total = sum(
        p["amount"] for p in payment_details if p["payment_mode_code"].lower() not in ["cash", "credit","IP ADVANCE"]
    )
    if bank_payment_total > 0:
        je_accounts.append({
            "account": bank_account,  # Replace with actual bank account
            "debit_in_account_currency": bank_payment_total,
            "credit_in_account_currency": 0,
            "cost_center": cost_center
            # "reference_type": "Sales Invoice",
            # "reference_name":sales_invoice_name
        })

    # Tax line
    if tax_amount > 0:
        if not vat_account:
            frappe.throw("Please set Default Tax Account in Company settings.")
        je_accounts.append({
            "account": vat_account,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": tax_amount,
        })
    if total_uepr > 0:
        je_accounts.extend([
            {
                "account": default_expense_account,
                "debit_in_account_currency": total_uepr,
                "credit_in_account_currency": 0,
                "cost_center": cost_center
            },
            {
                "account": stock_acc,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": total_uepr,
                "cost_center": cost_center
            }
        ])


    # # Discount line
    # if discount_amount > 0:
    #     if not discount_account:
    #         frappe.throw("Please set Default Discount Account in Company settings.")
    #     je_accounts.append({
    #         "account": discount_account,
    #         "debit_in_account_currency": discount_amount,
    #         "credit_in_account_currency": 0,
    #         "cost_center": cost_center
    #     })

    # --- Create Journal Entry ---
    je = frappe.get_doc({
        "doctype": "Journal Entry",
        "naming_series": "KX-JV-.YYYY.-",
        "voucher_type": "Journal Entry",
        "posting_date": formatted_date,
        "posting_time": posting_time,
        "custom_patient_name": patient_name,
        "custom_bill_number": bill_no,
        "custom_bill_category" :"PHARMACY",
        "custom_payer_name": customer_name,
        "custom_uhid": billing_data["uhId"],
        "custom_admission_id": billing_data["admissionId"],
        "custom_admission_type": billing_data["admissionType"],
        "company": company,
        "user_remark": f"Pharmacy Billing for bill no {bill_no}" ,
        "accounts": je_accounts,
        "custom_discount":discount_amount,
        "custom_round_off": round_off,
        "custom_store": store_name,
        "custom_facility_name": facility_name
    })

    try:
        je.insert(ignore_permissions=True)
        je.submit()
        frappe.db.commit()
        frappe.log(f"Journal Entry created successfully with bill_no: {bill_no}")
        return je.name
    except Exception as e:
        frappe.log_error(f"Failed to create Journal Entry: {e}")
        return None
