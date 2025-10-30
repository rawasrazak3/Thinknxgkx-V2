import frappe
import requests
import json
from frappe.utils import nowdate
from datetime import datetime
from frappe.utils import getdate, add_days, cint
from datetime import datetime, timedelta, time, timezone
from thinknxg_kx_v2.thinknxg_kx_v2.doctype.karexpert_settings.karexpert_settings import fetch_api_details

billing_type = "SUPPLIER CREATION"
settings = frappe.get_single("Karexpert Settings")
TOKEN_URL = settings.get("token_url")
BILLING_URL = settings.get("billing_url")
facility_id = settings.get("facility_id")

# Fetch row details based on billing type
billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
                                ["client_code", "integration_key", "x_api_key"], as_dict=True)
print("---billing row",billing_row)
 
headers_token = fetch_api_details(billing_type)

def get_jwt_token():
    response = requests.post(TOKEN_URL, headers=headers_token)
    if response.status_code == 200:
        return response.json().get("jwttoken")
    else:
        frappe.throw(f"Failed to fetch JWT token: {response.status_code} - {response.text}")

def fetch_op_billing(jwt_token, from_date, to_date):
    headers_billing = {
        "Content-Type": headers_token["Content-Type"],
        "clientCode": headers_token["clientCode"],
        "integrationKey": headers_token["integrationKey"],
        "Authorization": f"Bearer {jwt_token}"
    }
    payload = {"requestJson": {"FROM": from_date, "TO": to_date}}
    response = requests.post(BILLING_URL, headers=headers_billing, json=payload)
    if response.status_code == 200:
        return response.json()
    else:
        frappe.throw(f"Failed to fetch GRN data: {response.status_code} - {response.text}")


def supplier_creation(billing_data):
    print("---entered creation---")
    try:
        # Convert bill date to GMT+4
        date_ts = float(billing_data.get("g_creation_time", 0))
        datetimes = date_ts / 1000.0
        gmt_plus_4 = timezone(timedelta(hours=4))
        dt = datetime.fromtimestamp(datetimes, gmt_plus_4)
        formatted_date = dt.strftime('%Y-%m-%d')
        posting_time = dt.strftime('%H:%M:%S')

        # Extract fields from billing data
        supplier_code = billing_data.get("supplier_code")
        print("---sup code---",supplier_code)
        supplier_name = billing_data.get("name")
        print("---sup name---",supplier_name)
        address = billing_data.get("primary_address")
        address_line1 = address.get("street1")
        address_line2 = address.get("street2")
        city = address.get("city")
        state = address.get("state")
        country = address.get("country")
        postal_code = address.get("pincode")
        phone = billing_data.get("alternate_telecom") 
        # email = billing_data.get("email") or ""

        if not supplier_name or not supplier_code:
            print("---no sup name---")
            frappe.log_error("Missing supplier code or name in API response.", "Supplier Creation Error")
            return

        # Check if supplier already exists
        existing_supplier = frappe.db.exists("Supplier", {"custom_supplier_code": supplier_code, "disabled": 0})
        if existing_supplier:
            print("----sup exists---")
            frappe.log(f"Supplier with code {supplier_code} already exists as {existing_supplier}.")
            return existing_supplier

        # Create Supplier
        supplier = frappe.get_doc({
            "doctype": "Supplier",
            "supplier_name": supplier_name,
            "custom_supplier_code": supplier_code,
            "supplier_group": "All Supplier Groups",  # Change if needed
            "supplier_type": "Company",
        })
        supplier.insert(ignore_permissions=True)
        print("---sup data inserted--")
        frappe.db.commit()

        frappe.log(f"Supplier '{supplier_name}' created successfully with code {supplier_code}.")

        # Create Address linked to the Supplier
        address_doc = frappe.get_doc({
            "doctype": "Address",
            "address_title": supplier_name,
            "address_type": "Billing",
            "address_line1": address_line1 or "",
            "address_line2": address_line2 or "",
            "city": city or "",
            "state": state or "",
            "country": country or "",
            "pincode": postal_code or "",
            "phone": phone,
            # "email_id": email,
            "links": [{
                "link_doctype": "Supplier",
                "link_name": supplier.name
            }]
        })
        address_doc.insert(ignore_permissions=True)
        frappe.db.commit()

        frappe.log(f"Address created and linked to Supplier: {supplier.name}")

        return supplier.name

    except Exception as e:
        frappe.log_error(f"Failed to create Supplier or Address: {e}", "Supplier Creation Error")
        return None


@frappe.whitelist()
def main():
    try:
        print("--main--")
        jwt_token = get_jwt_token()
        frappe.log("JWT Token fetched successfully.")

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
            supplier_creation(billing)

    except Exception as e:
        frappe.log_error(f"Error: {e}")

if __name__ == "__main__":
    main()
