query = [

  """ALTER TABLE account_fiscal_position_tax DROP CONSTRAINT "account_fiscal_position_tax_tax_dest_id_fkey";""",
  """ALTER TABLE account_fiscal_position_tax ADD  CONSTRAINT "account_fiscal_position_tax_tax_dest_id_fkey" FOREIGN KEY ("tax_dest_id") REFERENCES "public"."account_tax" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_fiscal_position_tax DROP CONSTRAINT "account_fiscal_position_tax_tax_src_id_fkey";""",
  """ALTER TABLE account_fiscal_position_tax ADD  CONSTRAINT "account_fiscal_position_tax_tax_src_id_fkey" FOREIGN KEY ("tax_src_id") REFERENCES "public"."account_tax" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_tax DROP CONSTRAINT "account_tax_tax_group_id_fkey";""",
  """ALTER TABLE account_tax ADD  CONSTRAINT "account_tax_tax_group_id_fkey" FOREIGN KEY ("tax_group_id") REFERENCES "public"."account_tax_group" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_tax_purchase_order_line_rel DROP CONSTRAINT "account_tax_purchase_order_line_rel_account_tax_id_fkey";""",
  """ALTER TABLE account_tax_purchase_order_line_rel ADD  CONSTRAINT "account_tax_purchase_order_line_rel_account_tax_id_fkey" FOREIGN KEY ("account_tax_id") REFERENCES "public"."account_tax" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_tax_repartition_line DROP CONSTRAINT "account_tax_repartition_line_tax_id_fkey";""",
  """ALTER TABLE account_tax_repartition_line ADD  CONSTRAINT "account_tax_repartition_line_tax_id_fkey" FOREIGN KEY ("tax_id") REFERENCES "public"."account_tax" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_tax_sale_order_line_rel DROP CONSTRAINT "account_tax_sale_order_line_rel_account_tax_id_fkey";""",
  """ALTER TABLE account_tax_sale_order_line_rel ADD  CONSTRAINT "account_tax_sale_order_line_rel_account_tax_id_fkey" FOREIGN KEY ("account_tax_id") REFERENCES "public"."account_tax" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_tax_group_id_fkey";""",
  """ALTER TABLE account_move_line ADD  CONSTRAINT "account_move_line_tax_group_id_fkey" FOREIGN KEY ("tax_group_id") REFERENCES "public"."account_tax_group" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_tax_line_id_fkey";""",
  """ALTER TABLE account_move_line ADD  CONSTRAINT "account_move_line_tax_line_id_fkey" FOREIGN KEY ("tax_line_id") REFERENCES "public"."account_tax" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_move_line_account_tax_rel DROP CONSTRAINT "account_move_line_account_tax_rel_account_tax_id_fkey";""",
  """ALTER TABLE account_move_line_account_tax_rel ADD  CONSTRAINT "account_move_line_account_tax_rel_account_tax_id_fkey" FOREIGN KEY ("account_tax_id") REFERENCES "public"."account_tax" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_account_tag_account_tax_repartition_line_rel DROP CONSTRAINT "account_account_tag_account_t_account_tax_repartition_line_fkey";""",
  """ALTER TABLE account_account_tag_account_tax_repartition_line_rel ADD  CONSTRAINT "account_account_tag_account_t_account_tax_repartition_line_fkey" FOREIGN KEY ("account_tax_repartition_line_id") REFERENCES "public"."account_tax_repartition_line" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_tax_repartition_line_id_fkey";""",
  """ALTER TABLE account_move_line ADD  CONSTRAINT "account_move_line_tax_repartition_line_id_fkey" FOREIGN KEY ("tax_repartition_line_id") REFERENCES "public"."account_tax_repartition_line" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE product_taxes_rel DROP CONSTRAINT "product_taxes_rel_tax_id_fkey";""",
  """ALTER TABLE product_taxes_rel ADD  CONSTRAINT "product_taxes_rel_tax_id_fkey" FOREIGN KEY ("tax_id") REFERENCES "public"."account_tax" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE product_supplier_taxes_rel DROP CONSTRAINT "product_supplier_taxes_rel_tax_id_fkey";""",
  """ALTER TABLE product_supplier_taxes_rel ADD  CONSTRAINT "product_supplier_taxes_rel_tax_id_fkey" FOREIGN KEY ("tax_id") REFERENCES "public"."account_tax" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """DELETE FROM ir_model_data WHERE module='__export__'""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='account.tax.group'""",

]
for q in query:
  env.cr.execute(q)



env.cr.execute("""SELECT id, name,company_id FROM account_tax_group WHERE id>=1096 ORDER BY company_id, name->>'en_US'""")
records = env.cr.fetchall()

start = 1096
for c in records:
  q = """UPDATE account_tax_group SET id=%s WHERE id=%s""" % (start, c[0])

  env.cr.execute(q)
  start += 1
model = "account.tax.group"
records = (
    env[model]
    .sudo()
    .search([("id", ">", "1000")], order="id ASC")
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "tax_group_%s_%s_%s" % (r.id, r.name.lower().replace(" ","_").replace(".","_").replace("%",""), r.company_id.code.lower())
        
        env["ir.model.data"].create(
            {
                "module": "marin",
                "model": model,
                "name": name,
                "res_id": r.id,
                "noupdate": True,
            }
        )