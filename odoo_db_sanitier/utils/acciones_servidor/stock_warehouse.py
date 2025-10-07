query = [

  """ALTER TABLE pos_config DROP CONSTRAINT "pos_config_warehouse_id_fkey";""",
  """ALTER TABLE pos_config ADD  CONSTRAINT "pos_config_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_warehouse_id_fkey";""",
  """ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE sale_order_line DROP CONSTRAINT "sale_order_line_warehouse_id_fkey";""",
  """ALTER TABLE sale_order_line ADD  CONSTRAINT "sale_order_line_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_location DROP CONSTRAINT "stock_location_warehouse_id_fkey";""",
  """ALTER TABLE stock_location ADD  CONSTRAINT "stock_location_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_warehouse_id_fkey";""",
  """ALTER TABLE stock_move  ADD CONSTRAINT "stock_move_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_picking_type DROP CONSTRAINT "stock_picking_type_warehouse_id_fkey";""",
  """ALTER TABLE stock_picking_type ADD  CONSTRAINT "stock_picking_type_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE stock_quant DROP CONSTRAINT "stock_quant_warehouse_id_fkey";""",
  """ALTER TABLE stock_quant  ADD CONSTRAINT "stock_quant_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_route DROP CONSTRAINT "stock_route_supplied_wh_id_fkey";""",
  """ALTER TABLE stock_route ADD  CONSTRAINT "stock_route_supplied_wh_id_fkey" FOREIGN KEY ("supplied_wh_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_route DROP CONSTRAINT "stock_route_supplier_wh_id_fkey";""",
  """ALTER TABLE stock_route ADD  CONSTRAINT "stock_route_supplier_wh_id_fkey" FOREIGN KEY ("supplier_wh_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_route_warehouse DROP CONSTRAINT "stock_route_warehouse_warehouse_id_fkey";""",
  """ALTER TABLE stock_route_warehouse ADD  CONSTRAINT "stock_route_warehouse_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE stock_rule DROP CONSTRAINT "stock_rule_warehouse_id_fkey";""",
  """ALTER TABLE stock_rule ADD  CONSTRAINT "stock_rule_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_rule DROP CONSTRAINT "stock_rule_propagate_warehouse_id_fkey";""",
  """ALTER TABLE stock_rule ADD  CONSTRAINT "stock_rule_propagate_warehouse_id_fkey" FOREIGN KEY ("propagate_warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_warehouse_orderpoint DROP CONSTRAINT "stock_warehouse_orderpoint_warehouse_id_fkey";""",
  """ALTER TABLE stock_warehouse_orderpoint ADD  CONSTRAINT "stock_warehouse_orderpoint_warehouse_id_fkey" FOREIGN KEY ("warehouse_id") REFERENCES "public"."stock_warehouse" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """DELETE FROM ir_model_data WHERE module='marin' AND model='stock.warehouse'""",
  """DELETE FROM ir_model_data WHERE module='__export__' AND model='stock.warehouse'""",

]
for q in query:
  env.cr.execute(q)


query = """SELECT id,name FROM stock_warehouse WHERE id>=7 AND id<=8 ORDER BY id"""
env.cr.execute(query)
records = env.cr.fetchall()
#raise UserError(str(records))
start = 7
for r in records:
  q = """UPDATE stock_warehouse SET id=%s WHERE id=%s""" % (start, r[0])
  #raise UserError(q)
  env.cr.execute(q)
  start += 1

model = "stock.warehouse"
records = env[model].sudo().search(
    [("active", "in", [True, False])], order="id ASC"
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "warehouse_%s" % r.id
        #raise UserError(name)
        env["ir.model.data"].create(
            {
                "module": "marin",
                "model": model,
                "name": name,
                "res_id": r.id,
                "noupdate": True,
            }
        )