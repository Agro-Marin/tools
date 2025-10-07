query = [
  """ALTER TABLE account_analytic_line DROP CONSTRAINT "account_analytic_line_product_uom_id_fkey";""",
  """ALTER TABLE account_analytic_line  ADD CONSTRAINT "account_analytic_line_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  
  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_product_uom_id_fkey";""",
  """ALTER TABLE account_move_line  ADD CONSTRAINT "account_move_line_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  
  """ALTER TABLE product_template DROP CONSTRAINT "product_template_uom_id_fkey";""",
  """ALTER TABLE product_template  ADD CONSTRAINT "product_template_uom_id_fkey" FOREIGN KEY ("uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  
  """ALTER TABLE product_supplierinfo DROP CONSTRAINT "product_supplierinfo_product_uom_id_fkey";""",
  """ALTER TABLE product_supplierinfo ADD  CONSTRAINT "product_supplierinfo_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE purchase_order_line DROP CONSTRAINT "purchase_order_line_product_uom_id_fkey";""",
  """ALTER TABLE purchase_order_line ADD  CONSTRAINT "purchase_order_line_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order_template_line DROP CONSTRAINT "sale_order_template_line_product_uom_id_fkey";""",
  """ALTER TABLE sale_order_template_line  ADD CONSTRAINT "sale_order_template_line_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order_line DROP CONSTRAINT "sale_order_line_product_uom_id_fkey";""",
  """ALTER TABLE sale_order_line ADD  CONSTRAINT "sale_order_line_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_product_uom_fkey";""",
  """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_product_uom_fkey" FOREIGN KEY ("product_uom") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_packaging_uom_id_fkey";""",
  """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_packaging_uom_id_fkey" FOREIGN KEY ("packaging_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_move_line DROP CONSTRAINT "stock_move_line_product_uom_id_fkey";""",
  """ALTER TABLE stock_move_line ADD  CONSTRAINT "stock_move_line_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE stock_picking_tracker DROP CONSTRAINT "stock_picking_tracker_fuel_efficiency_uom_id_fkey";""",
  """ALTER TABLE stock_picking_tracker ADD  CONSTRAINT "stock_picking_tracker_fuel_efficiency_uom_id_fkey" FOREIGN KEY ("fuel_efficiency_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_picking_tracker DROP CONSTRAINT "stock_picking_tracker_odometer_uom_id_fkey";""",
  """ALTER TABLE stock_picking_tracker ADD  CONSTRAINT "stock_picking_tracker_odometer_uom_id_fkey" FOREIGN KEY ("odometer_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  
  """ALTER TABLE mrp_bom_line DROP CONSTRAINT "mrp_bom_line_product_uom_id_fkey";""",
  """ALTER TABLE mrp_bom_line ADD  CONSTRAINT "mrp_bom_line_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  
  """ALTER TABLE hr_expense DROP CONSTRAINT "hr_expense_product_uom_id_fkey";""",
  """ALTER TABLE hr_expense ADD  CONSTRAINT "hr_expense_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  
  """ALTER TABLE mrp_production DROP CONSTRAINT "mrp_production_product_uom_id_fkey";""",
  """ALTER TABLE mrp_production ADD  CONSTRAINT "mrp_production_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_bom DROP CONSTRAINT "mrp_bom_product_uom_id_fkey";""",
  """ALTER TABLE mrp_bom ADD  CONSTRAINT "mrp_bom_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_workorder DROP CONSTRAINT "mrp_workorder_product_uom_id_fkey";""",
  """ALTER TABLE mrp_workorder ADD  CONSTRAINT "mrp_workorder_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_unbuild DROP CONSTRAINT "mrp_unbuild_product_uom_id_fkey";""",
  """ALTER TABLE mrp_unbuild ADD  CONSTRAINT "mrp_unbuild_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  
  """ALTER TABLE barcode_rule DROP CONSTRAINT "barcode_rule_associated_uom_id_fkey";""",
  """ALTER TABLE barcode_rule ADD  CONSTRAINT "barcode_rule_associated_uom_id_fkey" FOREIGN KEY ("associated_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  
  """ALTER TABLE approval_product_line DROP CONSTRAINT "approval_product_line_product_uom_id_fkey";""",
  """ALTER TABLE approval_product_line ADD  CONSTRAINT "approval_product_line_product_uom_id_fkey" FOREIGN KEY ("product_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  
  """ALTER TABLE fleet_vehicle DROP CONSTRAINT "fleet_vehicle_odometer_uom_id_fkey";""",
  """ALTER TABLE fleet_vehicle ADD  CONSTRAINT "fleet_vehicle_odometer_uom_id_fkey" FOREIGN KEY ("odometer_uom_id") REFERENCES "public"."uom_uom" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """DELETE FROM ir_model_data WHERE module='__export__' AND model='uom.uom';""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='uom.uom' AND res_id>=100;""",
]
for q in query:
  env.cr.execute(q)


env.cr.execute("UPDATE uom_uom SET id=id+1000 WHERE id>=100")
env.cr.execute("""SELECT id,name FROM uom_uom WHERE id>=100 ORDER BY relative_uom_id nulls first ,relative_factor, name->>'en_US';""")
records = env.cr.fetchall()
#raise UserError(str(records))
start = 101
for r in records:
  q = """UPDATE uom_uom SET id=%s WHERE id=%s""" % (start, r[0])
  #raise UserError(q)
  env.cr.execute(q)
  start += 1


model = "uom.uom"
records = env[model].sudo().search(
    [("active", "in", (False, True)), ("id",">=",100)], order="id ASC"
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "uom_%s" % r.id
        #raise UserError(name)
        env["ir.model.data"].create(
            {
                "module": "marin_data",
                "model": model,
                "name": name,
                "res_id": r.id,
                "noupdate": True,
            }
        )
