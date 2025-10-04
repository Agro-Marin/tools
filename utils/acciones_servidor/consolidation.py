query = [

  """ALTER TABLE account_account_consolidation_account_rel DROP CONSTRAINT "account_account_consolidation_acc_consolidation_account_id_fkey";""",
  """ALTER TABLE account_account_consolidation_account_rel ADD  CONSTRAINT "account_account_consolidation_acc_consolidation_account_id_fkey" FOREIGN KEY ("consolidation_account_id") REFERENCES "public"."consolidation_account" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE consolidation_account DROP CONSTRAINT "consolidation_account_chart_id_fkey";""",
  """ALTER TABLE consolidation_account ADD  CONSTRAINT "consolidation_account_chart_id_fkey" FOREIGN KEY ("chart_id") REFERENCES "public"."consolidation_chart" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE consolidation_account DROP CONSTRAINT "consolidation_account_group_id_fkey";""",
  """ALTER TABLE consolidation_account ADD  CONSTRAINT "consolidation_account_group_id_fkey" FOREIGN KEY ("group_id") REFERENCES "public"."consolidation_group" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE consolidation_chart_res_company_rel DROP CONSTRAINT "consolidation_chart_res_company_rel_consolidation_chart_id_fkey";""",
  """ALTER TABLE consolidation_chart_res_company_rel ADD  CONSTRAINT "consolidation_chart_res_company_rel_consolidation_chart_id_fkey" FOREIGN KEY ("consolidation_chart_id") REFERENCES "public"."consolidation_chart" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE consolidation_company_period DROP CONSTRAINT "consolidation_company_period_period_id_fkey";""",
  """ALTER TABLE consolidation_company_period ADD  CONSTRAINT "consolidation_company_period_period_id_fkey" FOREIGN KEY ("period_id") REFERENCES "public"."consolidation_period" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE consolidation_group DROP CONSTRAINT "consolidation_group_chart_id_fkey";""",
  """ALTER TABLE consolidation_group ADD  CONSTRAINT "consolidation_group_chart_id_fkey" FOREIGN KEY ("chart_id") REFERENCES "public"."consolidation_chart" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE consolidation_group DROP CONSTRAINT "consolidation_group_parent_id_fkey";""",
  """ALTER TABLE consolidation_group ADD  CONSTRAINT "consolidation_group_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "public"."consolidation_group" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE consolidation_journal DROP CONSTRAINT "consolidation_journal_chart_id_fkey";""",
  """ALTER TABLE consolidation_journal ADD  CONSTRAINT "consolidation_journal_chart_id_fkey" FOREIGN KEY ("chart_id") REFERENCES "public"."consolidation_chart" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE consolidation_journal DROP CONSTRAINT "consolidation_journal_period_id_fkey";""",
  """ALTER TABLE consolidation_journal ADD  CONSTRAINT "consolidation_journal_period_id_fkey" FOREIGN KEY ("period_id") REFERENCES "public"."consolidation_period" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE consolidation_journal_line DROP CONSTRAINT "consolidation_journal_line_group_id_fkey";""",
  """ALTER TABLE consolidation_journal_line ADD  CONSTRAINT "consolidation_journal_line_group_id_fkey" FOREIGN KEY ("group_id") REFERENCES "public"."consolidation_group" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE consolidation_journal_line DROP CONSTRAINT "consolidation_journal_line_account_id_fkey";""",
  """ALTER TABLE consolidation_journal_line ADD  CONSTRAINT "consolidation_journal_line_account_id_fkey" FOREIGN KEY ("account_id") REFERENCES "public"."consolidation_account" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE consolidation_journal_line DROP CONSTRAINT "consolidation_journal_line_period_id_fkey";""",
  """ALTER TABLE consolidation_journal_line ADD  CONSTRAINT "consolidation_journal_line_period_id_fkey" FOREIGN KEY ("period_id") REFERENCES "public"."consolidation_period" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE consolidation_period DROP CONSTRAINT "consolidation_period_chart_id_fkey";""",
  """ALTER TABLE consolidation_period ADD  CONSTRAINT "consolidation_period_chart_id_fkey" FOREIGN KEY ("chart_id") REFERENCES "public"."consolidation_chart" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
]
for q in query:
  env.cr.execute(q)
