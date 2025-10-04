queries = [

    """ALTER TABLE account_account_res_company_rel DROP CONSTRAINT "account_account_res_company_rel_res_company_id_fkey";""",
    """ALTER TABLE account_account_res_company_rel ADD  CONSTRAINT "account_account_res_company_rel_res_company_id_fkey" FOREIGN KEY ("res_company_id") REFERENCES "public"."res_company" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

    """ALTER TABLE account_asset DROP CONSTRAINT "account_asset_company_id_fkey";""",
    """ALTER TABLE account_asset ADD  CONSTRAINT "account_asset_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE account_analytic_account DROP CONSTRAINT "account_analytic_account_company_id_fkey";""",
    """ALTER TABLE account_analytic_account  ADD CONSTRAINT "account_analytic_account_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE account_analytic_distribution_model DROP CONSTRAINT "account_analytic_distribution_model_company_id_fkey";""",
    """ALTER TABLE account_analytic_distribution_model ADD  CONSTRAINT "account_analytic_distribution_model_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
    """ALTER TABLE account_analytic_line DROP CONSTRAINT "account_analytic_line_company_id_fkey";""",
    """ALTER TABLE account_analytic_line ADD  CONSTRAINT "account_analytic_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE account_bank_statement DROP CONSTRAINT "account_bank_statement_company_id_fkey";""",
    """ALTER TABLE account_bank_statement  ADD CONSTRAINT "account_bank_statement_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE account_fiscal_position DROP CONSTRAINT "account_fiscal_position_company_id_fkey";""",
    """ALTER TABLE account_fiscal_position  ADD CONSTRAINT "account_fiscal_position_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE account_fiscal_position_tax DROP CONSTRAINT "account_fiscal_position_tax_company_id_fkey";""",
    """ALTER TABLE account_fiscal_position_tax  ADD CONSTRAINT "account_fiscal_position_tax_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE account_followup_followup_line DROP CONSTRAINT "account_followup_followup_line_company_id_fkey";""",
    """ALTER TABLE account_followup_followup_line  ADD CONSTRAINT "account_followup_followup_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE account_fiscal_year DROP CONSTRAINT "account_fiscal_year_company_id_fkey";""",
    """ALTER TABLE account_fiscal_year ADD  CONSTRAINT "account_fiscal_year_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE account_group DROP CONSTRAINT "account_group_company_id_fkey";""",
    """ALTER TABLE account_group  ADD CONSTRAINT "account_group_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE account_journal DROP CONSTRAINT "account_journal_company_id_fkey";""",
    """ALTER TABLE account_journal ADD  CONSTRAINT "account_journal_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE account_journal_group DROP CONSTRAINT "account_journal_group_company_id_fkey";""",
    """ALTER TABLE account_journal_group ADD  CONSTRAINT "account_journal_group_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE account_move DROP CONSTRAINT "account_move_company_id_fkey";""",
    """ALTER TABLE account_move  ADD CONSTRAINT "account_move_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_company_id_fkey";""",
    """ALTER TABLE account_move_line  ADD CONSTRAINT "account_move_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",



    """ALTER TABLE account_partial_reconcile DROP CONSTRAINT "account_partial_reconcile_company_id_fkey";""",
    """ALTER TABLE account_partial_reconcile  ADD CONSTRAINT "account_partial_reconcile_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE account_reconcile_model DROP CONSTRAINT "account_reconcile_model_company_id_fkey";""",
    """ALTER TABLE account_reconcile_model  ADD CONSTRAINT "account_reconcile_model_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE account_tax DROP CONSTRAINT "account_tax_company_id_fkey";""",
    """ALTER TABLE account_tax  ADD CONSTRAINT "account_tax_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE account_tax_group DROP CONSTRAINT "account_tax_group_company_id_fkey";""",
    """ALTER TABLE account_tax_group ADD  CONSTRAINT "account_tax_group_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE account_tax_repartition_line DROP CONSTRAINT "account_tax_repartition_line_company_id_fkey";""",
    """ALTER TABLE account_tax_repartition_line  ADD CONSTRAINT "account_tax_repartition_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

 =
    """ALTER TABLE crm_team DROP CONSTRAINT "crm_team_company_id_fkey";""",
    """ALTER TABLE crm_team ADD  CONSTRAINT "crm_team_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE date_range DROP CONSTRAINT "date_range_company_id_fkey";""",
    """ALTER TABLE date_range ADD  CONSTRAINT "date_range_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE date_range_type DROP CONSTRAINT "date_range_type_company_id_fkey";""",
    """ALTER TABLE date_range_type ADD  CONSTRAINT "date_range_type_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE fleet_vehicle DROP CONSTRAINT "fleet_vehicle_company_id_fkey";""",
    """ALTER TABLE fleet_vehicle ADD  CONSTRAINT "fleet_vehicle_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE fleet_vehicle_log_services DROP CONSTRAINT "fleet_vehicle_log_services_company_id_fkey";""",
    """ALTER TABLE fleet_vehicle_log_services ADD  CONSTRAINT "fleet_vehicle_log_services_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE hr_appraisal_note DROP CONSTRAINT "hr_appraisal_note_company_id_fkey";""",
    """ALTER TABLE hr_appraisal_note  ADD CONSTRAINT "hr_appraisal_note_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE hr_contract DROP CONSTRAINT "hr_contract_company_id_fkey";""",
    """ALTER TABLE hr_contract  ADD CONSTRAINT "hr_contract_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE hr_department DROP CONSTRAINT "hr_department_company_id_fkey";""",
    """ALTER TABLE hr_department  ADD CONSTRAINT "hr_department_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_company_id_fkey";""",
    """ALTER TABLE hr_employee  ADD CONSTRAINT "hr_employee_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE hr_expense DROP CONSTRAINT "hr_expense_company_id_fkey";""",
    """ALTER TABLE hr_expense ADD  CONSTRAINT "hr_expense_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE hr_job DROP CONSTRAINT "hr_job_company_id_fkey";""",
    """ALTER TABLE hr_job  ADD CONSTRAINT "hr_job_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE hr_payslip DROP CONSTRAINT "hr_payslip_company_id_fkey";""",
    """ALTER TABLE hr_payslip  ADD CONSTRAINT "hr_payslip_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE hr_payroll_note DROP CONSTRAINT "hr_payroll_note_company_id_fkey";""",
    """ALTER TABLE hr_payroll_note ADD  CONSTRAINT "hr_payroll_note_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE hr_payslip_run DROP CONSTRAINT "hr_payslip_run_company_id_fkey";""",
    """ALTER TABLE hr_payslip_run ADD  CONSTRAINT "hr_payslip_run_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE ir_attachment DROP CONSTRAINT "ir_attachment_company_id_fkey";""",
    """ALTER TABLE ir_attachment  ADD  CONSTRAINT "ir_attachment_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE ir_default DROP CONSTRAINT "ir_default_company_id_fkey";""",
    """ALTER TABLE ir_default  ADD CONSTRAINT "ir_default_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

    """ALTER TABLE ir_sequence DROP CONSTRAINT "ir_sequence_company_id_fkey";""",
    """ALTER TABLE ir_sequence  ADD CONSTRAINT "ir_sequence_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE l10n_mx_edi_employer_registration DROP CONSTRAINT "l10n_mx_edi_employer_registration_company_id_fkey";""",
    """ALTER TABLE l10n_mx_edi_employer_registration  ADD CONSTRAINT "l10n_mx_edi_employer_registration_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE mail_message DROP CONSTRAINT "mail_message_record_company_id_fkey";""",
    """ALTER TABLE mail_message ADD  CONSTRAINT "mail_message_record_company_id_fkey" FOREIGN KEY ("record_company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE mrp_production DROP CONSTRAINT "mrp_production_company_id_fkey";""",
    """ALTER TABLE mrp_production ADD  CONSTRAINT "mrp_production_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE mrp_workcenter DROP CONSTRAINT "mrp_workcenter_company_id_fkey";""",
    """ALTER TABLE mrp_workcenter ADD  CONSTRAINT "mrp_workcenter_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE onboarding_progress DROP CONSTRAINT "onboarding_progress_company_id_fkey";""",
    """ALTER TABLE onboarding_progress  ADD CONSTRAINT "onboarding_progress_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

    """ALTER TABLE purchase_order DROP CONSTRAINT "purchase_order_company_id_fkey";""",
    """ALTER TABLE purchase_order  ADD  CONSTRAINT "purchase_order_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE purchase_order_line DROP CONSTRAINT "purchase_order_line_company_id_fkey";""",
    """ALTER TABLE purchase_order_line  ADD  CONSTRAINT "purchase_order_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE payslip_tags_table DROP CONSTRAINT "payslip_tags_table_res_company_id_fkey";""",
    """ALTER TABLE payslip_tags_table ADD  CONSTRAINT "payslip_tags_table_res_company_id_fkey" FOREIGN KEY ("res_company_id") REFERENCES "public"."res_company" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

    """ALTER TABLE pos_config DROP CONSTRAINT "pos_config_company_id_fkey";""",
    """ALTER TABLE pos_config ADD  CONSTRAINT "pos_config_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE pos_order DROP CONSTRAINT "pos_order_company_id_fkey";""",
    """ALTER TABLE pos_order ADD  CONSTRAINT "pos_order_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE pos_order_line DROP CONSTRAINT "pos_order_line_company_id_fkey";""",
    """ALTER TABLE pos_order_line ADD  CONSTRAINT "pos_order_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE pos_payment DROP CONSTRAINT "pos_payment_company_id_fkey";""",
    """ALTER TABLE pos_payment ADD  CONSTRAINT "pos_payment_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE pos_payment_method DROP CONSTRAINT "pos_payment_method_company_id_fkey";""",
    """ALTER TABLE pos_payment_method ADD  CONSTRAINT "pos_payment_method_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE product_pricelist DROP CONSTRAINT "product_pricelist_company_id_fkey";""",
    """ALTER TABLE product_pricelist ADD  CONSTRAINT "product_pricelist_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE product_supplierinfo DROP CONSTRAINT "product_supplierinfo_company_id_fkey";""",
    """ALTER TABLE product_supplierinfo ADD  CONSTRAINT "product_supplierinfo_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE project_task DROP CONSTRAINT "project_task_company_id_fkey";""",
    """ALTER TABLE project_task ADD  CONSTRAINT "project_task_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE res_company_users_rel DROP CONSTRAINT "res_company_users_rel_cid_fkey";""",
    """ALTER TABLE res_company_users_rel  ADD CONSTRAINT "res_company_users_rel_cid_fkey" FOREIGN KEY ("cid") REFERENCES "public"."res_company" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

    """ALTER TABLE res_currency_rate DROP CONSTRAINT "res_currency_rate_company_id_fkey";""",
    """ALTER TABLE res_currency_rate  ADD CONSTRAINT "res_currency_rate_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE res_users DROP CONSTRAINT "res_users_company_id_fkey";""",
    """ALTER TABLE res_users ADD  CONSTRAINT "res_users_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE resource_calendar DROP CONSTRAINT "resource_calendar_company_id_fkey";""",
    """ALTER TABLE resource_calendar  ADD CONSTRAINT "resource_calendar_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
    """ALTER TABLE resource_resource DROP CONSTRAINT "resource_resource_company_id_fkey";""",
    """ALTER TABLE resource_resource  ADD CONSTRAINT "resource_resource_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE room_office DROP CONSTRAINT "room_office_company_id_fkey";""",
    """ALTER TABLE room_office ADD  CONSTRAINT "room_office_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE room_room DROP CONSTRAINT "room_room_company_id_fkey";""",
    """ALTER TABLE room_room ADD  CONSTRAINT "room_room_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_company_id_fkey";""",
    """ALTER TABLE sale_order  ADD  CONSTRAINT "sale_order_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE sale_order_line DROP CONSTRAINT "sale_order_line_company_id_fkey";""",
    """ALTER TABLE sale_order_line  ADD  CONSTRAINT "sale_order_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE stock_location DROP CONSTRAINT "stock_location_company_id_fkey";""",
    """ALTER TABLE stock_location  ADD CONSTRAINT "stock_location_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE stock_lot DROP CONSTRAINT "stock_lot_company_id_fkey";""",
    """ALTER TABLE stock_lot ADD  CONSTRAINT "stock_lot_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_company_id_fkey";""",
    """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE stock_move_line DROP CONSTRAINT "stock_move_line_company_id_fkey";""",
    """ALTER TABLE stock_move_line ADD  CONSTRAINT "stock_move_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE stock_picking DROP CONSTRAINT "stock_picking_company_id_fkey";""",
    """ALTER TABLE stock_picking ADD  CONSTRAINT "stock_picking_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
    """ALTER TABLE stock_picking_type DROP CONSTRAINT "stock_picking_type_company_id_fkey";""",
    """ALTER TABLE stock_picking_type ADD  CONSTRAINT "stock_picking_type_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE stock_quant DROP CONSTRAINT "stock_quant_company_id_fkey";""",
    """ALTER TABLE stock_quant ADD  CONSTRAINT "stock_quant_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE stock_route DROP CONSTRAINT "stock_route_company_id_fkey";""",
    """ALTER TABLE stock_route  ADD CONSTRAINT "stock_route_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE stock_rule DROP CONSTRAINT "stock_rule_company_id_fkey";""",
    """ALTER TABLE stock_rule  ADD CONSTRAINT "stock_rule_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_company_id_fkey";""",
    """ALTER TABLE stock_warehouse  ADD CONSTRAINT "stock_warehouse_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE stock_warehouse_orderpoint DROP CONSTRAINT "stock_warehouse_orderpoint_company_id_fkey";""",
    """ALTER TABLE stock_warehouse_orderpoint ADD  CONSTRAINT "stock_warehouse_orderpoint_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

    """ALTER TABLE website DROP CONSTRAINT "website_company_id_fkey";""",
    """ALTER TABLE website ADD  CONSTRAINT "website_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

]
for q in queries:
  env.cr.execute(q)
 
new = [
    (7,8),

]
for q in new:
  env.cr.execute("""UPDATE res_company SET id=%s WHERE id=%s""" % (q[0],q[1]))
