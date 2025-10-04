queries = [
  """ALTER TABLE mrp_bom_line DROP CONSTRAINT "mrp_bom_line_bom_id_fkey";""",
  """ALTER TABLE mrp_bom_line ADD  CONSTRAINT "mrp_bom_line_bom_id_fkey" FOREIGN KEY ("bom_id") REFERENCES "public"."mrp_bom" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE mrp_production DROP CONSTRAINT "mrp_production_bom_id_fkey";""",
  """ALTER TABLE mrp_production ADD  CONSTRAINT "mrp_production_bom_id_fkey" FOREIGN KEY ("bom_id") REFERENCES "public"."mrp_bom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_bom_line_id_fkey";""",
  """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_bom_line_id_fkey" FOREIGN KEY ("bom_line_id") REFERENCES "public"."mrp_bom_line" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """DELETE FROM ir_model_data WHERE module='__export__' AND model='mrp.bom'""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='mrp.bom'""",
  """DELETE FROM ir_model_data WHERE module='__export__' AND model='mrp.bom.line'""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='mrp.bom.line'""",

]
for q in queries:
  env.cr.execute(q)

env.cr.execute("""UPDATE mrp_bom SET sequence=10""")
env.cr.execute("""UPDATE mrp_bom SET id=id+10000""")
env.cr.execute("""SELECT id, code FROM mrp_bom WHERE id>=1000 ORDER BY company_id, product_tmpl_id, code""")
records = env.cr.fetchall()

start = 1001
for i in records:
  q = """UPDATE mrp_bom SET id=%s WHERE id=%s;""" % (start, i[0])
  env.cr.execute(q)
  start += 1
model = "mrp.bom"
records = env[model].sudo().search([("id", ">", "1000")], order="id ASC")
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
       
        name = "mrp_bom_%s" % r.id
        
        env["ir.model.data"].create(
            {
                "module": "marin",
                "model": model,
                "name": name,
                "res_id": r.id,
                "noupdate": True,
            }
        )

env.cr.execute("""UPDATE mrp_bom_line SET id=id+10000""")
env.cr.execute("""SELECT id FROM mrp_bom_line WHERE id>=1000 ORDER BY bom_id,sequence,id""")
records = env.cr.fetchall()

start = 1001
for i in records:
  q = """UPDATE mrp_bom_line SET id=%s WHERE id=%s;""" % (start, i[0])
  env.cr.execute(q)
  start += 1
model = "mrp.bom.line"
records = env[model].sudo().search([("id", ">", "1000")], order="id ASC")
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
      
        name = "mrp_bom_line_%s" % r.id
     
        env["ir.model.data"].create(
            {
                "module": "marin",
                "model": model,
                "name": name,
                "res_id": r.id,
                "noupdate": True,
            }
        )