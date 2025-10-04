queries = [

  """ALTER TABLE pos_category_product_template_rel DROP CONSTRAINT "pos_category_product_template_rel_pos_category_id_fkey";""",
  """ALTER TABLE pos_category_product_template_rel ADD  CONSTRAINT "pos_category_product_template_rel_pos_category_id_fkey" FOREIGN KEY ("pos_category_id") REFERENCES "public"."pos_category" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE pos_category_pos_config_rel DROP CONSTRAINT "pos_category_pos_config_rel_pos_category_id_fkey";""",
  """ALTER TABLE pos_category_pos_config_rel ADD  CONSTRAINT "pos_category_pos_config_rel_pos_category_id_fkey" FOREIGN KEY ("pos_category_id") REFERENCES "public"."pos_category" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """DELETE FROM ir_model_data WHERE module='__export__';""",
  """DELETE FROM ir_model_data WHERE module='__export__' AND model='pos.category';""",
  """DELETE FROM ir_model_data WHERE model='pos.category' AND res_id>1;""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='pos.category';""",

]
for q in queries:
  env.cr.execute(q)

env.cr.execute("""UPDATE pos_category SET id=id+99 WHERE id>1""")

env.cr.execute("""SELECT MAX(id) FROM pos_category""")
max = env.cr.fetchall()
env.cr.execute("""SELECT setval('"public"."pos_category_id_seq"', %s, true);""" % max[0][0])
model = "pos.category"
records = env[model].sudo().search(
    [("id", ">=", 100)], order="id ASC"
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "pos_category_%s" % r.id
        
        env["ir.model.data"].create(
            {
                "module": "marin",
                "model": model,
                "name": name,
                "res_id": r.id,
                "noupdate": True,
            }
        )
