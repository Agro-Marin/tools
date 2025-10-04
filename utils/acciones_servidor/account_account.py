queries = [
  """ALTER TABLE account_account_account_asset_rel DROP CONSTRAINT "account_account_account_asset_rel_account_account_id_fkey";""",
  """ALTER TABLE account_account_account_asset_rel ADD  CONSTRAINT "account_account_account_asset_rel_account_account_id_fkey" FOREIGN KEY ("account_account_id") REFERENCES "public"."account_account" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_account_account_journal_rel DROP CONSTRAINT "account_account_account_journal_rel_account_account_id_fkey";""",
  """ALTER TABLE account_account_account_journal_rel  ADD CONSTRAINT "account_account_account_journal_rel_account_account_id_fkey" FOREIGN KEY ("account_account_id") REFERENCES "public"."account_account" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_account_account_tag DROP CONSTRAINT "account_account_account_tag_account_account_id_fkey";""",
  """ALTER TABLE account_account_account_tag ADD  CONSTRAINT "account_account_account_tag_account_account_id_fkey" FOREIGN KEY ("account_account_id") REFERENCES "public"."account_account" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_account_res_company_rel DROP CONSTRAINT "account_account_res_company_rel_account_account_id_fkey";""",
  """ALTER TABLE account_account_res_company_rel ADD  CONSTRAINT "account_account_res_company_rel_account_account_id_fkey" FOREIGN KEY ("account_account_id") REFERENCES "public"."account_account" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_account_tag_account_move_line_rel DROP CONSTRAINT "account_account_tag_account_move_li_account_account_tag_id_fkey";""",
  """ALTER TABLE account_account_tag_account_move_line_rel ADD  CONSTRAINT "account_account_tag_account_move_li_account_account_tag_id_fkey" FOREIGN KEY ("account_account_tag_id") REFERENCES "public"."account_account_tag" ("id") ON DELETE RESTRICT ON UPDATE  CASCADE;""",
  """ALTER TABLE account_account_tag_account_tax_repartition_line_rel DROP CONSTRAINT "account_account_tag_account_tax_rep_account_account_tag_id_fkey";""",
  """ALTER TABLE account_account_tag_account_tax_repartition_line_rel ADD  CONSTRAINT "account_account_tag_account_tax_rep_account_account_tag_id_fkey" FOREIGN KEY ("account_account_tag_id") REFERENCES "public"."account_account_tag" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_analytic_line DROP CONSTRAINT "account_analytic_line_account_id_fkey";""",
  """ALTER TABLE account_analytic_line  ADD CONSTRAINT "account_analytic_line_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account_analytic_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_analytic_line DROP CONSTRAINT "account_analytic_line_general_account_id_fkey";""",
  """ALTER TABLE account_analytic_line  ADD CONSTRAINT "account_analytic_line_general_account_id_fkey" FOREIGN KEY ("general_account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_asset DROP CONSTRAINT "account_asset_account_asset_id_fkey";""",
  """ALTER TABLE account_asset  ADD CONSTRAINT "account_asset_account_asset_id_fkey" FOREIGN KEY ("account_asset_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_asset DROP CONSTRAINT "account_asset_account_depreciation_expense_id_fkey";""",
  """ALTER TABLE account_asset  ADD CONSTRAINT "account_asset_account_depreciation_expense_id_fkey" FOREIGN KEY ("account_depreciation_expense_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_asset DROP CONSTRAINT "account_asset_account_depreciation_id_fkey";""",
  """ALTER TABLE account_asset  ADD CONSTRAINT "account_asset_account_depreciation_id_fkey" FOREIGN KEY ("account_depreciation_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_journal DROP CONSTRAINT "account_journal_default_account_id_fkey";""",
  """ALTER TABLE account_journal  ADD CONSTRAINT "account_journal_default_account_id_fkey" FOREIGN KEY ("default_account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_journal DROP CONSTRAINT "account_journal_default_payable_account_id_fkey";""",
  """ALTER TABLE account_journal  ADD CONSTRAINT "account_journal_default_payable_account_id_fkey" FOREIGN KEY ("default_payable_account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_journal DROP CONSTRAINT "account_journal_default_receivable_account_id_fkey";""",
  """ALTER TABLE account_journal  ADD CONSTRAINT "account_journal_default_receivable_account_id_fkey" FOREIGN KEY ("default_receivable_account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_journal DROP CONSTRAINT "account_journal_default_refund_account_id_fkey";""",
  """ALTER TABLE account_journal  ADD CONSTRAINT "account_journal_default_refund_account_id_fkey" FOREIGN KEY ("default_refund_account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_journal DROP CONSTRAINT "account_journal_loss_account_id_fkey";""",
  """ALTER TABLE account_journal  ADD CONSTRAINT "account_journal_loss_account_id_fkey" FOREIGN KEY ("loss_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_journal DROP CONSTRAINT "account_journal_profit_account_id_fkey";""",
  """ALTER TABLE account_journal  ADD CONSTRAINT "account_journal_profit_account_id_fkey" FOREIGN KEY ("profit_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_journal DROP CONSTRAINT "account_journal_suspense_account_id_fkey";""",
  """ALTER TABLE account_journal  ADD CONSTRAINT "account_journal_suspense_account_id_fkey" FOREIGN KEY ("suspense_account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_journal_account_account_control_rel DROP CONSTRAINT "account_journal_account_account_control_rel_account_id_fkey";""",
  """ALTER TABLE account_journal_account_account_control_rel ADD  CONSTRAINT "account_journal_account_account_control_rel_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account_account" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_account_id_fkey";""",
  """ALTER TABLE account_move_line  ADD CONSTRAINT "account_move_line_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",


  """ALTER TABLE account_payment DROP CONSTRAINT "account_payment_destination_account_id_fkey";""",
  """ALTER TABLE account_payment  ADD CONSTRAINT "account_payment_destination_account_id_fkey" FOREIGN KEY ("destination_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_payment DROP CONSTRAINT "account_payment_outstanding_account_id_fkey";""",
  """ALTER TABLE account_payment  ADD CONSTRAINT "account_payment_outstanding_account_id_fkey" FOREIGN KEY ("outstanding_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_payment_method_line DROP CONSTRAINT "account_payment_method_line_payment_account_id_fkey";""",
  """ALTER TABLE account_payment_method_line  ADD CONSTRAINT "account_payment_method_line_payment_account_id_fkey" FOREIGN KEY ("payment_account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_reconcile_model_line DROP CONSTRAINT "account_reconcile_model_line_account_id_fkey";""",
  """ALTER TABLE account_reconcile_model_line  ADD CONSTRAINT "account_reconcile_model_line_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account_account" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_report_budget_item DROP CONSTRAINT "account_report_budget_item_account_id_fkey";""",
  """ALTER TABLE account_report_budget_item  ADD CONSTRAINT "account_report_budget_item_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_tax DROP CONSTRAINT "account_tax_cash_basis_transition_account_id_fkey";""",
  """ALTER TABLE account_tax  ADD CONSTRAINT "account_tax_cash_basis_transition_account_id_fkey" FOREIGN KEY ("cash_basis_transition_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_tax_group DROP CONSTRAINT "account_tax_group_tax_payable_account_id_fkey";""",
  """ALTER TABLE account_tax_group  ADD CONSTRAINT "account_tax_group_tax_payable_account_id_fkey" FOREIGN KEY ("tax_payable_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_tax_group DROP CONSTRAINT "account_tax_group_tax_receivable_account_id_fkey";""",
  """ALTER TABLE account_tax_group  ADD CONSTRAINT "account_tax_group_tax_receivable_account_id_fkey" FOREIGN KEY ("tax_receivable_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_tax_repartition_line DROP CONSTRAINT "account_tax_repartition_line_account_id_fkey";""",
  """ALTER TABLE account_tax_repartition_line  ADD CONSTRAINT "account_tax_repartition_line_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE hr_expense DROP CONSTRAINT "hr_expense_account_id_fkey";""",
  """ALTER TABLE hr_expense  ADD CONSTRAINT "hr_expense_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE pos_payment_method DROP CONSTRAINT "pos_payment_method_receivable_account_id_fkey";""",
  """ALTER TABLE pos_payment_method  ADD CONSTRAINT "pos_payment_method_receivable_account_id_fkey" FOREIGN KEY ("receivable_account_id") REFERENCES "public"."account_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",


  """ALTER TABLE res_company DROP CONSTRAINT "res_company_account_cash_basis_base_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_account_cash_basis_base_account_id_fkey" FOREIGN KEY ("account_cash_basis_base_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_account_default_pos_receivable_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_account_default_pos_receivable_account_id_fkey" FOREIGN KEY ("account_default_pos_receivable_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_account_journal_early_pay_discount_gain_accoun_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_account_journal_early_pay_discount_gain_accoun_fkey" FOREIGN KEY ("account_journal_early_pay_discount_gain_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_account_journal_early_pay_discount_loss_accoun_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_account_journal_early_pay_discount_loss_accoun_fkey" FOREIGN KEY ("account_journal_early_pay_discount_loss_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_account_journal_suspense_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_account_journal_suspense_account_id_fkey" FOREIGN KEY ("account_journal_suspense_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_default_cash_difference_expense_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_default_cash_difference_expense_account_id_fkey" FOREIGN KEY ("default_cash_difference_expense_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_default_cash_difference_income_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_default_cash_difference_income_account_id_fkey" FOREIGN KEY ("default_cash_difference_income_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_expense_accrual_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_expense_accrual_account_id_fkey" FOREIGN KEY ("expense_accrual_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_expense_currency_exchange_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_expense_currency_exchange_account_id_fkey" FOREIGN KEY ("expense_currency_exchange_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_gain_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_gain_account_id_fkey" FOREIGN KEY ("gain_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_income_currency_exchange_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_income_currency_exchange_account_id_fkey" FOREIGN KEY ("income_currency_exchange_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_loss_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_loss_account_id_fkey" FOREIGN KEY ("loss_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_revenue_accrual_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_revenue_accrual_account_id_fkey" FOREIGN KEY ("revenue_accrual_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_transfer_account_id_fkey";""",
  """ALTER TABLE res_company  ADD CONSTRAINT "res_company_transfer_account_id_fkey" FOREIGN KEY ("transfer_account_id") REFERENCES "public"."account_account" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """DELETE FROM account_merge_wizard;""",
  """DELETE FROM ir_model_data WHERE module='__export__' AND model='account.account'""",
  """DELETE FROM ir_model_data WHERE model='account.account' AND res_id>1000""",
  """DELETE FROM ir_model_data WHERE module='marin_data' AND model='account.account'""",

]
for q in queries:
  env.cr.execute(q)



model = "account.account"
records = env[model].sudo().search(
    [("id", ">", "1000")],
    order="id ASC"
)

for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        lmmr = env["res.company"].browse(2)
        tjgl = env["res.company"].browse(3)
        lmmg = env["res.company"].browse(4)
        xm = env["res.company"].browse(7)
        stored_code = r.with_company(lmmr).code_store or r.with_company(lmmg).code_store or r.with_company(tjgl).code_store or r.with_company(xm).code_store
        name = "account_%s" % (stored_code.replace(".","_"))
        if len(r.company_ids) == 1:
            name += "_%s" % r.company_ids.code.lower()
        try:
            env["ir.model.data"].create(
                {
                    "module": "marin_data",
                    "model": model,
                    "name": name,
                    "res_id": r.id,
                    "noupdate": True,
                }
            )
        except:
            raise UserError(r.id)