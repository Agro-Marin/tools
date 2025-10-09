models = [
    "res_users", "res_partner", "res_partner_bank",
    "resource_resource", "hr_employee", "hr_contract", "hr_department",
    "hr_salary_rule", "hr_payslip_run", "hr_payslip", "hr_payslip_line",
    "fleet_vehicle",
    "product_template", "product_product", "product_supplierinfo",
    "stock_lot", "stock_warehouse_orderpoint", "stock_quant", "procurement_group",
    "stock_picking", "stock_move", "stock_move_line", "stock_rule",
    "mrp_bom", "mrp_bom_line", "mrp_production", 
    "account_account", "account_report_budget", "account_report_budget_item",
    "account_analytic_account", "account_analytic_distribution_model", "account_reconcile_model", "account_full_reconcile", "account_partial_reconcile",
    "account_bank_statement", "account_bank_statement_line", "account_move", "account_move_line", "account_payment", "account_asset",
    "purchase_order", "purchase_order_line",
    "sale_order_template", "sale_order_template_line", "sale_order", "sale_order_line",
    "pos_session", "pos_order", "pos_order_line", "pos_payment",
    "project_tags", "project_project", "project_task_type", "project_task",
    #"calendar_event", "calendar_attendee", "calendar_recurrence",
    "survey_survey", "survey_question", "survey_question_answer", "survey_user_input", "survey_user_input_line",
    "slide_channel", "slide_answer", "slide_question", "slide_slide",
    "syngenta_commercial_agreement",
    "approval_category", "approval_category_approver", "approval_request", "approval_approver",
    #"approval_product_line",
    "date_range_type", "date_range",
    "project_task_user_rel"
    
]
for model in models:
    env.cr.execute("""SELECT MAX(id) FROM %s""" % model)
    records = env.cr.fetchall()
    env.cr.execute("""SELECT setval('"public"."%s_id_seq"', %s, true);""" % (model, records[0][0]))
