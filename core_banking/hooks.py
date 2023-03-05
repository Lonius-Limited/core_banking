from . import __version__ as app_version
from frappe import _

app_name = "core_banking"
app_title = "Core Banking"
app_publisher = "Lonius Limited"
app_description = "For all core banking modules in ERPNext. Initially to be used for Pension Schemes and any instioffering core banking features"
app_icon = "octicon octicon-file-directory"
app_color = "blue"
app_email = "info@lonius.co.ke"
app_license = "MIT"

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
app_include_css = ["/assets/core_banking/css/custom_table.css",
"/assets/core_banking/css/pos-custom.css"]
app_include_js = [
    "/assets/core_banking/js/custom_scripts/member.js",
    "/assets/core_banking/js/custom_scripts/payment_entry.js",
    "/assets/core_banking/js/custom_scripts/additional_salary.js",
    "/assets/core_banking/js/custom_scripts/pension_contributions_upload.js",
    "/assets/core_banking/js/custom_scripts/payroll_entry.js",
]



# include js, css files in header of web template
# web_include_css = "/assets/core_banking/css/core_banking.css"
# web_include_js = "/assets/core_banking/js/core_banking.js"


# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "core_banking/public/scss/website"

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

# Installation
# ------------

# before_install = "core_banking.install.before_install"
# after_install = "core_banking.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "core_banking.uninstall.before_uninstall"
# after_uninstall = "core_banking.uninstall.after_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "core_banking.notifications.get_notification_config"

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
fixtures = [
    dict(dt="Report", filters=dict(module="Core Banking")),
    dict(dt="Print Format", filters=dict(name="Company Totals")),
]
doc_events = {
    "Member": {
        "after_insert": "core_banking.api.member.make_member_customer",
        "before_save": [
            "core_banking.api.member.set_date_of_retirement",
            "core_banking.api.member.validate_percentages",
            "core_banking.api.member.validate_transfers_in",
        ],
        # "on_trash": "method"
    },
    "Pension Contributions Upload": {
        "before_save": "core_banking.api.member.populate_upload",
        "before_submit": "core_banking.api.member.post_pension_schedule_hook",
    },
    "Salary Slip": {
        "before_save": [
            "core_banking.core_banking_payroll.salary_slip.salary_slip_save"
        ],
        "on_submit": ["core_banking.api.payroll_entry.override_salary_slip_submit"],
        "before_submit": ["core_banking.api.payroll_entry.override_salary_slip_submit"],
    },
    "Payroll Entry": {
        "before_save": ["core_banking.api.payroll_entry.set_title_field"],
        "on_update_after_submit": [
            "core_banking.api.payroll_entry.process_approved_payrolls"
        ],
    },
}

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"core_banking.tasks.all"
# 	],
# 	"daily": [
# 		"core_banking.tasks.daily"
# 	],
# 	"hourly": [
# 		"core_banking.tasks.hourly"
# 	],
# 	"weekly": [
# 		"core_banking.tasks.weekly"
# 	]
# 	"monthly": [
# 		"core_banking.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "core_banking.install.before_tests"

# Overriding Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "core_banking.event.get_events"
# }
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "core_banking.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]


# User Data Protection
# --------------------

user_data_fields = [
    {
        "doctype": "{doctype_1}",
        "filter_by": "{filter_by}",
        "redact_fields": ["{field_1}", "{field_2}"],
        "partial": 1,
    },
    {
        "doctype": "{doctype_2}",
        "filter_by": "{filter_by}",
        "partial": 1,
    },
    {
        "doctype": "{doctype_3}",
        "strict": False,
    },
    {"doctype": "{doctype_4}"},
]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"core_banking.auth.validate"
# ]

# Translation
# --------------------------------

# Make link fields search translated document names for these DocTypes
# Recommended only for DocTypes which have limited documents with untranslated names
# For example: Role, Gender, etc.
# translated_search_doctypes = []
