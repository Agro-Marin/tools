lista = [

  """ALTER TABLE account_account_res_company_rel DROP CONSTRAINT "account_account_res_company_rel_res_company_id_fkey";""",
  """ALTER TABLE account_account_res_company_rel ADD  CONSTRAINT "account_account_res_company_rel_res_company_id_fkey" FOREIGN KEY ("res_company_id") REFERENCES "public"."res_company" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_fiscal_position DROP CONSTRAINT "account_fiscal_position_company_id_fkey";""",
  """ALTER TABLE account_fiscal_position ADD  CONSTRAINT "account_fiscal_position_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_fiscal_position_tax DROP CONSTRAINT "account_fiscal_position_tax_company_id_fkey";""",
  """ALTER TABLE account_fiscal_position_tax ADD  CONSTRAINT "account_fiscal_position_tax_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_journal DROP CONSTRAINT "account_journal_company_id_fkey";""",
  """ALTER TABLE account_journal ADD  CONSTRAINT "account_journal_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_journal_group DROP CONSTRAINT "account_journal_group_company_id_fkey";""",
  """ALTER TABLE account_journal_group ADD  CONSTRAINT "account_journal_group_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_move DROP CONSTRAINT "account_move_company_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_company_id_fkey";""",
  """ALTER TABLE account_move_line ADD  CONSTRAINT "account_move_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_partial_reconcile DROP CONSTRAINT "account_partial_reconcile_company_id_fkey";""",
  """ALTER TABLE account_partial_reconcile ADD  CONSTRAINT "account_partial_reconcile_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_payment DROP CONSTRAINT "account_payment_company_id_fkey";""",
  """ALTER TABLE account_payment ADD  CONSTRAINT "account_payment_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_reconcile_model DROP CONSTRAINT "account_reconcile_model_company_id_fkey";""",
  """ALTER TABLE account_reconcile_model ADD  CONSTRAINT "account_reconcile_model_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_reconcile_model_line DROP CONSTRAINT "account_reconcile_model_line_company_id_fkey";""",
  """ALTER TABLE account_reconcile_model_line ADD  CONSTRAINT "account_reconcile_model_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE account_tax DROP CONSTRAINT "account_tax_company_id_fkey";""",
  """ALTER TABLE account_tax ADD  CONSTRAINT "account_tax_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_tax_group DROP CONSTRAINT "account_tax_group_company_id_fkey";""",
  """ALTER TABLE account_tax_group ADD  CONSTRAINT "account_tax_group_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_tax_repartition_line DROP CONSTRAINT "account_tax_repartition_line_company_id_fkey";""",
  """ALTER TABLE account_tax_repartition_line ADD  CONSTRAINT "account_tax_repartition_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE ir_default DROP CONSTRAINT "ir_default_company_id_fkey";""",
  """ALTER TABLE ir_default ADD  CONSTRAINT "ir_default_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE ir_sequence DROP CONSTRAINT "ir_sequence_company_id_fkey";""",
  """ALTER TABLE ir_sequence ADD  CONSTRAINT "ir_sequence_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE pos_config DROP CONSTRAINT "pos_config_company_id_fkey";""",
  """ALTER TABLE pos_config ADD  CONSTRAINT "pos_config_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE pos_payment DROP CONSTRAINT "pos_payment_company_id_fkey";""",
  """ALTER TABLE pos_payment ADD  CONSTRAINT "pos_payment_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE pos_payment_method DROP CONSTRAINT "pos_payment_method_company_id_fkey";""",
  """ALTER TABLE pos_payment_method ADD  CONSTRAINT "pos_payment_method_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE pos_order DROP CONSTRAINT "pos_order_company_id_fkey";""",
  """ALTER TABLE pos_order ADD  CONSTRAINT "pos_order_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE pos_order_line DROP CONSTRAINT "pos_order_line_company_id_fkey";""",
  """ALTER TABLE pos_order_line ADD  CONSTRAINT "pos_order_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE resource_calendar DROP CONSTRAINT "resource_calendar_company_id_fkey";""",
  """ALTER TABLE resource_calendar ADD  CONSTRAINT "resource_calendar_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_company_id_fkey";""",
  """ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE sale_order_line DROP CONSTRAINT "sale_order_line_company_id_fkey";""",
  """ALTER TABLE sale_order_line ADD  CONSTRAINT "sale_order_line_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_location DROP CONSTRAINT "stock_location_company_id_fkey";""",
  """ALTER TABLE stock_location ADD  CONSTRAINT "stock_location_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_picking_type DROP CONSTRAINT "stock_picking_type_company_id_fkey";""",
  """ALTER TABLE stock_picking_type ADD  CONSTRAINT "stock_picking_type_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_route DROP CONSTRAINT "stock_route_company_id_fkey";""",
  """ALTER TABLE stock_route ADD  CONSTRAINT "stock_route_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_rule DROP CONSTRAINT "stock_rule_company_id_fkey";""",
  """ALTER TABLE stock_rule ADD  CONSTRAINT "stock_rule_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_company_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_company_id_fkey" FOREIGN KEY ("company_id") REFERENCES "public"."res_company" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """DELETE FROM hr_appraisal_note WHERE company_id=8;""",
  """DELETE FROM hr_payroll_note WHERE company_id=8;""",
  """DELETE FROM mail_message WHERE record_company_id=8;""",
  """DELETE FROM onboarding_progress WHERE company_id=8;""",
  """DELETE FROM payslip_tags_table WHERE res_company_id=8;""",
  """DELETE FROM product_pricelist WHERE company_id=8;""",
  """DELETE FROM product_supplierinfo WHERE company_id=8;""",
  """DELETE FROM purchase_order WHERE company_id=8;""",
  """DELETE FROM res_company_users_rel WHERE cid=8;""",
  """DELETE FROM stock_move WHERE company_id=8;""",
  """DELETE FROM stock_picking WHERE company_id=8;""",
  """UPDATE res_company SET id=7 WHERE id=8;""",

]
for cosa in lista:
  env.cr.execute(cosa)