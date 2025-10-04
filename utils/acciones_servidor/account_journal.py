queries = [
  """ALTER TABLE account_account_account_journal_rel DROP CONSTRAINT "account_account_account_journal_rel_account_journal_id_fkey";""",
  """ALTER TABLE account_account_account_journal_rel  ADD CONSTRAINT "account_account_account_journal_rel_account_journal_id_fkey" FOREIGN KEY ("account_journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_analytic_line DROP CONSTRAINT "account_analytic_line_journal_id_fkey";""",
  """ALTER TABLE account_analytic_line  ADD CONSTRAINT "account_analytic_line_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_asset DROP CONSTRAINT "account_asset_journal_id_fkey";""",
  """ALTER TABLE account_asset  ADD CONSTRAINT "account_asset_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_bank_statement DROP CONSTRAINT "account_bank_statement_journal_id_fkey";""",
  """ALTER TABLE account_bank_statement  ADD CONSTRAINT "account_bank_statement_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_bank_statement_line DROP CONSTRAINT "account_bank_statement_line_journal_id_fkey";""",
  """ALTER TABLE account_bank_statement_line  ADD CONSTRAINT "account_bank_statement_line_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_journal_account_journal_group_rel DROP CONSTRAINT "account_journal_account_journal_group_r_account_journal_id_fkey";""",
  """ALTER TABLE account_journal_account_journal_group_rel ADD  CONSTRAINT "account_journal_account_journal_group_r_account_journal_id_fkey" FOREIGN KEY ("account_journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE account_journal_account_journal_group_rel DROP CONSTRAINT "account_journal_account_journal_g_account_journal_group_id_fkey";""",
  """ALTER TABLE account_journal_account_journal_group_rel ADD  CONSTRAINT "account_journal_account_journal_g_account_journal_group_id_fkey" FOREIGN KEY ("account_journal_group_id") REFERENCES "public"."account_journal_group" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_journal_account_reconcile_model_rel DROP CONSTRAINT "account_journal_account_reconcile_model_account_journal_id_fkey";""",
  """ALTER TABLE account_journal_account_reconcile_model_rel ADD  CONSTRAINT "account_journal_account_reconcile_model_account_journal_id_fkey" FOREIGN KEY ("account_journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_move DROP CONSTRAINT "account_move_journal_id_fkey";""",
  """ALTER TABLE account_move  ADD CONSTRAINT "account_move_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_journal_id_fkey";""",
  """ALTER TABLE account_move_line  ADD CONSTRAINT "account_move_line_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_payment DROP CONSTRAINT "account_payment_payment_method_line_id_fkey";""",
  """ALTER TABLE account_payment ADD  CONSTRAINT "account_payment_payment_method_line_id_fkey" FOREIGN KEY ("payment_method_line_id") REFERENCES "public"."account_payment_method_line" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_payment DROP CONSTRAINT "account_payment_journal_id_fkey";""",
  """ALTER TABLE account_payment ADD  CONSTRAINT "account_payment_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_payment_method_line DROP CONSTRAINT "account_payment_method_line_journal_id_fkey";""",
  """ALTER TABLE account_payment_method_line  ADD CONSTRAINT "account_payment_method_line_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE journal_account_control_rel DROP CONSTRAINT "journal_account_control_rel_journal_id_fkey";""",
  """ALTER TABLE journal_account_control_rel  ADD CONSTRAINT "journal_account_control_rel_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",


  """ALTER TABLE pos_config DROP CONSTRAINT "pos_config_invoice_journal_id_fkey";""",
  """ALTER TABLE pos_config  ADD CONSTRAINT "pos_config_invoice_journal_id_fkey" FOREIGN KEY ("invoice_journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE pos_config DROP CONSTRAINT "pos_config_journal_id_fkey";""",
  """ALTER TABLE pos_config  ADD CONSTRAINT "pos_config_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE pos_order DROP CONSTRAINT "pos_order_sale_journal_fkey";""",
  """ALTER TABLE pos_order  ADD CONSTRAINT "pos_order_sale_journal_fkey" FOREIGN KEY ("sale_journal") REFERENCES "public"."account_journal" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE pos_payment_method DROP CONSTRAINT "pos_payment_method_journal_id_fkey";""",
  """ALTER TABLE pos_payment_method  ADD CONSTRAINT "pos_payment_method_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE pos_session DROP CONSTRAINT "pos_session_cash_journal_id_fkey";""",
  """ALTER TABLE pos_session  ADD CONSTRAINT "pos_session_cash_journal_id_fkey" FOREIGN KEY ("cash_journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE res_company DROP CONSTRAINT "res_company_account_tax_periodicity_journal_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_account_tax_periodicity_journal_id_fkey" FOREIGN KEY ("account_tax_periodicity_journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_currency_exchange_journal_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_currency_exchange_journal_id_fkey" FOREIGN KEY ("currency_exchange_journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_pos_cash_transfer_journal_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_pos_cash_transfer_journal_id_fkey" FOREIGN KEY ("pos_cash_transfer_journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_tax_cash_basis_journal_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_tax_cash_basis_journal_id_fkey" FOREIGN KEY ("tax_cash_basis_journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_journal_id_fkey";""",
  """ALTER TABLE sale_order  ADD CONSTRAINT "sale_order_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE hr_expense_sheet DROP CONSTRAINT "hr_expense_sheet_journal_id_fkey";""",
  """ALTER TABLE hr_expense_sheet  ADD CONSTRAINT "hr_expense_sheet_journal_id_fkey" FOREIGN KEY ("journal_id") REFERENCES "public"."account_journal" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """DELETE FROM account_payment_register""",
  """DELETE FROM ir_model_data WHERE module='__export__' AND model='account.journal'""",
  """DELETE FROM ir_model_data WHERE model='account.journal' AND res_id>1000""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='account.journal'""",

]