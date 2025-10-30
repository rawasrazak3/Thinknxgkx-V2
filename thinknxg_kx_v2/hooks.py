app_name = "thinknxg_kx_v2"
app_title = "thinkNXG KX V2"
app_publisher = "Kreatao - thinkNXG"
app_description = "thinkNXG KX V2"
app_email = "thinknxgkx@gmail.com"
app_license = "mit"

# Apps
# ------------------

# required_apps = []

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "thinknxg_kx_v2",
# 		"logo": "/assets/thinknxg_kx_v2/logo.png",
# 		"title": "Thinknxg Kx V2",
# 		"route": "/thinknxg_kx_v2",
# 		"has_permission": "thinknxg_kx_v2.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------
fixtures = [
    {
    "doctype": "Custom Field",
        "filters": {
            "module": ["in", ["Thinknxg Kx V2"]]
            }
    },
]
# include js, css files in header of desk.html
# app_include_css = "/assets/thinknxg_kx_v2/css/thinknxg_kx_v2.css"
# app_include_js = "/assets/thinknxg_kx_v2/js/thinknxg_kx_v2.js"

# include js, css files in header of web template
# web_include_css = "/assets/thinknxg_kx_v2/css/thinknxg_kx_v2.css"
# web_include_js = "/assets/thinknxg_kx_v2/js/thinknxg_kx_v2.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "thinknxg_kx_v2/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
# doctype_list_js = {"doctype" : "public/js/doctype_list.js"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "thinknxg_kx_v2/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "thinknxg_kx_v2.utils.jinja_methods",
# 	"filters": "thinknxg_kx_v2.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "thinknxg_kx_v2.install.before_install"
# after_install = "thinknxg_kx_v2.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "thinknxg_kx_v2.uninstall.before_uninstall"
# after_uninstall = "thinknxg_kx_v2.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "thinknxg_kx_v2.utils.before_app_install"
# after_app_install = "thinknxg_kx_v2.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "thinknxg_kx_v2.utils.before_app_uninstall"
# after_app_uninstall = "thinknxg_kx_v2.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "thinknxg_kx_v2.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# DocType Class
# ---------------
# Override standard doctype classes

# override_doctype_class = {
# 	"ToDo": "custom_app.overrides.CustomToDo"
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
# 	}
# }

# Scheduled Tasks
# ---------------
scheduler_events = {
    "cron": {
        "52 23 * * *": [  # Daily at 11:52
            "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.advance_deposit.main"
        ],
        "54 23 * * *": [  # Daily at 11:54
            "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.supplier_creation.main",
        ],
        "56 23 * * *": [  # Daily at 11:56
            "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.pharmacy_bill.main",
            "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.pharmacy_refund.main",
            # "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.due_settlement.main",
            "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.grn_creation.main",
            "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.advance_deposit_refund.main",
            "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.grn_return.main",
            "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.stock_transfer.main",
            "thinknxg_kx_v2.thinknxg_kx_v2.custom_script.ar_bill_settlement.main",
        ],
    }
}
# scheduler_events = {
# 	"all": [
# 		"thinknxg_kx_v2.tasks.all"
# 	],
# 	"daily": [
# 		"thinknxg_kx_v2.tasks.daily"
# 	],
# 	"hourly": [
# 		"thinknxg_kx_v2.tasks.hourly"
# 	],
# 	"weekly": [
# 		"thinknxg_kx_v2.tasks.weekly"
# 	],
# 	"monthly": [
# 		"thinknxg_kx_v2.tasks.monthly"
# 	],
# }

# Testing
# -------

# before_tests = "thinknxg_kx_v2.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "thinknxg_kx_v2.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "thinknxg_kx_v2.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["thinknxg_kx_v2.utils.before_request"]
# after_request = ["thinknxg_kx_v2.utils.after_request"]

# Job Events
# ----------
# before_job = ["thinknxg_kx_v2.utils.before_job"]
# after_job = ["thinknxg_kx_v2.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"thinknxg_kx_v2.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

