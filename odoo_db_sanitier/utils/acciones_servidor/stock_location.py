query = [

  """ALTER TABLE purchase_order_line DROP CONSTRAINT "purchase_order_line_location_final_id_fkey";""",
  """ALTER TABLE purchase_order_line ADD  CONSTRAINT "purchase_order_line_location_final_id_fkey" FOREIGN KEY ("location_final_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE mrp_production DROP CONSTRAINT "mrp_production_location_dest_id_fkey";""",
  """ALTER TABLE mrp_production ADD  CONSTRAINT "mrp_production_location_dest_id_fkey" FOREIGN KEY ("location_dest_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_production DROP CONSTRAINT "mrp_production_location_src_id_fkey";""",
  """ALTER TABLE mrp_production ADD  CONSTRAINT "mrp_production_location_src_id_fkey" FOREIGN KEY ("location_src_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_production DROP CONSTRAINT "mrp_production_production_location_id_fkey";""",
  """ALTER TABLE mrp_production ADD  CONSTRAINT "mrp_production_production_location_id_fkey" FOREIGN KEY ("production_location_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE res_company DROP CONSTRAINT "res_company_internal_transit_location_id_fkey";""",
  """ALTER TABLE res_company ADD  CONSTRAINT "res_company_internal_transit_location_id_fkey" FOREIGN KEY ("internal_transit_location_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE res_company DROP CONSTRAINT "res_company_rental_loc_id_fkey";""",
  """ALTER TABLE res_company ADD  CONSTRAINT "res_company_rental_loc_id_fkey" FOREIGN KEY ("rental_loc_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_location DROP CONSTRAINT "stock_location_location_id_fkey";""",
  """ALTER TABLE stock_location ADD  CONSTRAINT "stock_location_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "public"."stock_location" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE stock_lot DROP CONSTRAINT "stock_lot_location_id_fkey";""",
  """ALTER TABLE stock_lot ADD  CONSTRAINT "stock_lot_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_location_dest_id_fkey";""",
  """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_location_dest_id_fkey" FOREIGN KEY ("location_dest_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_location_id_fkey";""",
  """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_location_final_id_fkey";""",
  """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_location_final_id_fkey" FOREIGN KEY ("location_final_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_move_line DROP CONSTRAINT "stock_move_line_location_dest_id_fkey";""",
  """ALTER TABLE stock_move_line ADD  CONSTRAINT "stock_move_line_location_dest_id_fkey" FOREIGN KEY ("location_dest_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_move_line DROP CONSTRAINT "stock_move_line_location_id_fkey";""",
  """ALTER TABLE stock_move_line ADD  CONSTRAINT "stock_move_line_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE stock_package_level DROP CONSTRAINT "stock_package_level_location_dest_id_fkey";""",
  """ALTER TABLE stock_package_level ADD  CONSTRAINT "stock_package_level_location_dest_id_fkey" FOREIGN KEY ("location_dest_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_picking DROP CONSTRAINT "stock_picking_location_dest_id_fkey";""",
  """ALTER TABLE stock_picking ADD  CONSTRAINT "stock_picking_location_dest_id_fkey" FOREIGN KEY ("location_dest_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_picking DROP CONSTRAINT "stock_picking_location_id_fkey";""",
  """ALTER TABLE stock_picking ADD  CONSTRAINT "stock_picking_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE stock_picking_type DROP CONSTRAINT "stock_picking_type_default_location_dest_id_fkey";""",
  """ALTER TABLE stock_picking_type ADD  CONSTRAINT "stock_picking_type_default_location_dest_id_fkey" FOREIGN KEY ("default_location_dest_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_picking_type DROP CONSTRAINT "stock_picking_type_default_location_src_id_fkey";""",
  """ALTER TABLE stock_picking_type ADD  CONSTRAINT "stock_picking_type_default_location_src_id_fkey" FOREIGN KEY ("default_location_src_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_quant DROP CONSTRAINT "stock_quant_location_id_fkey";""",
  """ALTER TABLE stock_quant ADD  CONSTRAINT "stock_quant_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE stock_rule DROP CONSTRAINT "stock_rule_location_dest_id_fkey";""",
  """ALTER TABLE stock_rule ADD  CONSTRAINT "stock_rule_location_dest_id_fkey" FOREIGN KEY ("location_dest_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_rule DROP CONSTRAINT "stock_rule_location_src_id_fkey";""",
  """ALTER TABLE stock_rule ADD  CONSTRAINT "stock_rule_location_src_id_fkey" FOREIGN KEY ("location_src_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_lot_stock_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_lot_stock_id_fkey" FOREIGN KEY ("lot_stock_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_pbm_loc_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_pbm_loc_id_fkey" FOREIGN KEY ("pbm_loc_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_sam_loc_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_sam_loc_id_fkey" FOREIGN KEY ("sam_loc_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_view_location_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_view_location_id_fkey" FOREIGN KEY ("view_location_id") REFERENCES "public"."stock_location" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_wh_input_stock_loc_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_wh_input_stock_loc_id_fkey" FOREIGN KEY ("wh_input_stock_loc_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_wh_output_stock_loc_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_wh_output_stock_loc_id_fkey" FOREIGN KEY ("wh_output_stock_loc_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_wh_pack_stock_loc_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_wh_pack_stock_loc_id_fkey" FOREIGN KEY ("wh_pack_stock_loc_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_wh_qc_stock_loc_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_wh_qc_stock_loc_id_fkey" FOREIGN KEY ("wh_qc_stock_loc_id") REFERENCES "public"."stock_location" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_warehouse_orderpoint DROP CONSTRAINT "stock_warehouse_orderpoint_location_id_fkey";""",
  """ALTER TABLE stock_warehouse_orderpoint ADD  CONSTRAINT "stock_warehouse_orderpoint_location_id_fkey" FOREIGN KEY ("location_id") REFERENCES "public"."stock_location" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """DELETE FROM ir_model_data WHERE module='__export__' AND model='stock.location'""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='stock.location'""",
 
]
for q in query:
  env.cr.execute(q)


fix_id = 5613
env.cr.execute("""SELECT id, name FROM stock_location WHERE id>=%s ORDER BY id;""" % fix_id)
records = env.cr.fetchall()
#raise UserError(str(records))
start = fix_id
for r in records:
  env.cr.execute("""UPDATE stock_location SET id=%s WHERE id=%s""" % (start, r[0]))
  start += 1
env.cr.execute("""SELECT MAX(id) FROM stock_location""")
max = env.cr.fetchall()
env.cr.execute("""SELECT setval('"public"."stock_location_id_seq"', %s, true);""" % max[0][0])
model = "stock.location"
records = env[model].sudo().search(
    [("active", "in", [True, False]), ("id", ">=", "1")], order="id ASC"
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "stock_location_%s" % r.id
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

