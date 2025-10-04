queries = [
"""ALTER TABLE account_partial_reconcile DROP CONSTRAINT "account_partial_reconcile_credit_move_id_fkey";""",
"""ALTER TABLE account_partial_reconcile ADD  CONSTRAINT "account_partial_reconcile_credit_move_id_fkey" FOREIGN KEY ("credit_move_id") REFERENCES "public"."account_move_line" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
"""ALTER TABLE account_partial_reconcile DROP CONSTRAINT "account_partial_reconcile_debit_move_id_fkey";""",
"""ALTER TABLE account_partial_reconcile ADD  CONSTRAINT "account_partial_reconcile_debit_move_id_fkey" FOREIGN KEY ("debit_move_id") REFERENCES "public"."account_move_line" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

"""ALTER TABLE account_move_line_account_tax_rel DROP CONSTRAINT "account_move_line_account_tax_rel_account_move_line_id_fkey";""",
"""ALTER TABLE account_move_line_account_tax_rel ADD  CONSTRAINT "account_move_line_account_tax_rel_account_move_line_id_fkey" FOREIGN KEY ("account_move_line_id") REFERENCES "public"."account_move_line" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

"""ALTER TABLE asset_move_line_rel DROP CONSTRAINT "asset_move_line_rel_line_id_fkey";""",
"""ALTER TABLE asset_move_line_rel ADD  CONSTRAINT "asset_move_line_rel_line_id_fkey" FOREIGN KEY ("line_id") REFERENCES "public"."account_move_line" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

"""ALTER TABLE account_account_tag_account_move_line_rel DROP CONSTRAINT "account_account_tag_account_move_line_account_move_line_id_fkey";""",
"""ALTER TABLE account_account_tag_account_move_line_rel ADD  CONSTRAINT "account_account_tag_account_move_line_account_move_line_id_fkey" FOREIGN KEY ("account_move_line_id") REFERENCES "public"."account_move_line" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

"""ALTER TABLE account_analytic_line DROP CONSTRAINT "account_analytic_line_move_line_id_fkey";""",
"""ALTER TABLE account_analytic_line ADD  CONSTRAINT "account_analytic_line_move_line_id_fkey" FOREIGN KEY ("move_line_id") REFERENCES "public"."account_move_line" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

"""ALTER TABLE account_move_line_hr_payslip_line_rel DROP CONSTRAINT "account_move_line_hr_payslip_line_rel_account_move_line_id_fkey";""",
"""ALTER TABLE account_move_line_hr_payslip_line_rel ADD  CONSTRAINT "account_move_line_hr_payslip_line_rel_account_move_line_id_fkey" FOREIGN KEY ("account_move_line_id") REFERENCES "public"."account_move_line" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

"""ALTER TABLE account_move_line_sale_order_line_rel DROP CONSTRAINT "account_move_line_sale_order_line_rel_move_line_id_fkey";""",
"""ALTER TABLE account_move_line_sale_order_line_rel ADD  CONSTRAINT "account_move_line_sale_order_line_rel_move_line_id_fkey" FOREIGN KEY ("move_line_id") REFERENCES "public"."account_move_line" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

"""ALTER TABLE account_move_line_purchase_order_line_rel DROP CONSTRAINT "account_move_line_purchase_order_line_rel_move_line_id_fkey";""",
"""ALTER TABLE account_move_line_purchase_order_line_rel ADD  CONSTRAINT "account_move_line_purchase_order_line_rel_move_line_id_fkey" FOREIGN KEY ("move_line_id") REFERENCES "public"."account_move_line" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

"""ALTER TABLE fleet_vehicle_log DROP CONSTRAINT "fleet_vehicle_log_account_move_line_id_fkey";""",
"""ALTER TABLE fleet_vehicle_log ADD  CONSTRAINT "fleet_vehicle_log_account_move_line_id_fkey" FOREIGN KEY ("account_move_line_id") REFERENCES "public"."account_move_line" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
]

env.cr.execute("""
SELECT id FROM account_move_line ORDER BY move_id, array_position(ARRAY['product', 'tax', 'payment_term', 'line_note'], display_type), "sequence", id;
""")

records = env.cr.fetchall()
start = 1001
for i in records:
  env.cr.execute("""UPDATE account_move_line SET id=%s WHERE id=%s;""" % (start, i[0]))
  start += 1
