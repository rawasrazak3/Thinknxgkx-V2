# Copyright (c) 2025, Thinknxg and contributors
# For license information, please see license.txt

## import frappe
# from frappe.model.document import Document


# class KarexpertSettings(Document):
# 	pass

import frappe
from frappe.model.document import Document


class KarexpertSettings(Document):
	pass

# @frappe.whitelist()
# def fetch_api_details(billing_type):
# 	print("----fetching details from function---")
# 	settings = frappe.get_single("Karexpert Settings")
# 	facility_id = settings.get("facility_id")

# 	# Fetch row details based on billing type
# 	billing_row = frappe.get_value("Karexpert  Table", {"billing_type": billing_type},
# 									["client_code", "integration_key", "x_api_key"], as_dict=True)

# 	# TOKEN_URL = "https://metro.kxstage.com/external/api/v1/token"
# 	# BILLING_URL = "https://metro.kxstage.com/external/api/v1/integrate"

# 	headers_token = {
# 		"Content-Type": "application/json",
# 		# "clientCode": "METRO_THINKNXG_FI",
# 		"clientCode": billing_row["client_code"],
# 		# "facilityId": "METRO_THINKNXG",
# 		"facilityId": facility_id,
# 		"messageType": "request",
# 		# "integrationKey": "OP_BILLING",
# 		"integrationKey": billing_row["integration_key"],
# 		# "x-api-key": "kfhgjfgjf0980gdfgfds"
# 		"x-api-key": billing_row["x_api_key"]
# 	}
# 	return headers_token


@frappe.whitelist()
def fetch_api_details(billing_type):
    print("----fetching details from function---")
    settings = frappe.get_single("Karexpert Settings")
    print("---settings",settings)

    # Fetch facility IDs list (from your child table)
    facility_list = frappe.get_all(
        "Facility ID",  # replace with your actual child table name
        filters={"parent": settings.name},
        fields=["facility_id"]
    )
    # Fetch billing row details
    billing_row = frappe.get_value(
        "Karexpert  Table",
        {"billing_type": billing_type},
        ["client_code", "integration_key", "x_api_key"],
        as_dict=True
    )

    # Build headers for each facility
    all_facility_headers = []
    print("---facility list--",facility_list)
    print("---billing row--",billing_row)
    for facility_data in facility_list:
        facility_id = facility_data["facility_id"]

        headers_token = {
            "Content-Type": "application/json",
            "clientCode": billing_row["client_code"],
            "facilityId": facility_id,
            "messageType": "request",
            "integrationKey": billing_row["integration_key"],
            "x-api-key": billing_row["x_api_key"]
        }

        all_facility_headers.append(headers_token)

    return all_facility_headers
