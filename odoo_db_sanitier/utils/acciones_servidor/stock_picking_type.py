query = [

  """ALTER TABLE mrp_bom DROP CONSTRAINT "mrp_bom_picking_type_id_fkey";""",
  """ALTER TABLE mrp_bom ADD  CONSTRAINT "mrp_bom_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE mrp_production DROP CONSTRAINT "mrp_production_picking_type_id_fkey";""",
  """ALTER TABLE mrp_production ADD  CONSTRAINT "mrp_production_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE purchase_order DROP CONSTRAINT "purchase_order_picking_type_id_fkey";""",
  """ALTER TABLE purchase_order ADD  CONSTRAINT "purchase_order_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE pos_config DROP CONSTRAINT "pos_config_picking_type_id_fkey";""",
  """ALTER TABLE pos_config ADD  CONSTRAINT "pos_config_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE quality_point_stock_picking_type_rel DROP CONSTRAINT "quality_point_stock_picking_type_rel_stock_picking_type_id_fkey";""",
  """ALTER TABLE quality_point_stock_picking_type_rel ADD  CONSTRAINT "quality_point_stock_picking_type_rel_stock_picking_type_id_fkey" FOREIGN KEY ("stock_picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_picking_type_id_fkey";""",
  """ALTER TABLE stock_move  ADD CONSTRAINT "stock_move_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_picking DROP CONSTRAINT "stock_picking_picking_type_id_fkey";""",
  """ALTER TABLE stock_picking ADD  CONSTRAINT "stock_picking_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE stock_picking_type_res_users_can_access_rel DROP CONSTRAINT "stock_picking_type_res_users_can_access_re_picking_type_id_fkey";""",
  """ALTER TABLE stock_picking_type_res_users_can_access_rel ADD  CONSTRAINT "stock_picking_type_res_users_can_access_re_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE stock_picking_type_res_users_can_todo_rel DROP CONSTRAINT "stock_picking_type_res_users_can_todo_rel_picking_type_id_fkey";""",
  """ALTER TABLE stock_picking_type_res_users_can_todo_rel ADD  CONSTRAINT "stock_picking_type_res_users_can_todo_rel_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE stock_picking_type_res_users_can_validate_rel DROP CONSTRAINT "stock_picking_type_res_users_can_validate__picking_type_id_fkey";""",
  """ALTER TABLE stock_picking_type_res_users_can_validate_rel ADD  CONSTRAINT "stock_picking_type_res_users_can_validate__picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE stock_picking_batch DROP CONSTRAINT "stock_picking_batch_picking_type_id_fkey";""",
  """ALTER TABLE stock_picking_batch ADD  CONSTRAINT "stock_picking_batch_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_picking_type DROP CONSTRAINT "stock_picking_type_return_picking_type_id_fkey";""",
  """ALTER TABLE stock_picking_type ADD  CONSTRAINT "stock_picking_type_return_picking_type_id_fkey" FOREIGN KEY ("return_picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_rule DROP CONSTRAINT "stock_rule_picking_type_id_fkey";""",
  """ALTER TABLE stock_rule ADD  CONSTRAINT "stock_rule_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE stock_route_picking_type DROP CONSTRAINT "stock_route_picking_type_picking_type_id_fkey";""",
  """ALTER TABLE stock_route_picking_type ADD  CONSTRAINT "stock_route_picking_type_picking_type_id_fkey" FOREIGN KEY ("picking_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_in_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_in_type_id_fkey" FOREIGN KEY ("in_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_int_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_int_type_id_fkey" FOREIGN KEY ("int_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_manu_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_manu_type_id_fkey" FOREIGN KEY ("manu_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_out_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_out_type_id_fkey" FOREIGN KEY ("out_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_pack_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_pack_type_id_fkey" FOREIGN KEY ("pack_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_pbm_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_pbm_type_id_fkey" FOREIGN KEY ("pbm_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_pick_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_pick_type_id_fkey" FOREIGN KEY ("pick_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_pos_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_pos_type_id_fkey" FOREIGN KEY ("pos_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_qc_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_qc_type_id_fkey" FOREIGN KEY ("qc_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_sam_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_sam_type_id_fkey" FOREIGN KEY ("sam_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_store_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_store_type_id_fkey" FOREIGN KEY ("store_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_xdock_type_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_xdock_type_id_fkey" FOREIGN KEY ("xdock_type_id") REFERENCES "public"."stock_picking_type" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

 
]

query = [
  
    """UPDATE stock_picking_type SET sequence=100, color=10  WHERE name->>'en_US' = 'Delivery Orders'""",
    """UPDATE stock_picking_type SET sequence=150, color=10  WHERE name->>'en_US' = 'Ship orders'""",
    """UPDATE stock_picking_type SET sequence=150, color=10  WHERE name->>'en_US' = 'Ship orders 3P'""",
    """UPDATE stock_picking_type SET sequence=200, color=10  WHERE name->>'en_US' = 'PoS Orders'""",
    """UPDATE stock_picking_type SET sequence=300, color=11  WHERE name->>'en_US' ilike 'receipts'""",
    """UPDATE stock_picking_type SET sequence=350, color=5  WHERE name->>'en_US' ilike 'internal transfers'""",
    """UPDATE stock_picking_type SET sequence=400, color=5  WHERE name->>'en_US' ilike 'interwarehouse%'""",
    """UPDATE stock_picking_type SET sequence=500, color=1  WHERE name->>'en_US' ilike 'Returns from customers'""",
    """UPDATE stock_picking_type SET sequence=550, color=1  WHERE name->>'en_US' ilike 'Returns to suppliers'""",
    """UPDATE stock_picking_type SET sequence=600  WHERE name->>'en_US' ilike 'manufacturing'""",
    """UPDATE stock_picking_type SET sequence=700  WHERE name->>'en_US' ilike 'pick'""",
    """UPDATE stock_picking_type SET sequence=800  WHERE name->>'en_US' ilike 'pick components'""",
    """UPDATE stock_picking_type SET sequence=900  WHERE name->>'en_US' ilike 'pack'""",
    """UPDATE stock_picking_type SET sequence=1000 WHERE name->>'en_US' ilike 'store finished product'""",
    """UPDATE stock_picking_type SET sequence=1100 WHERE name->>'en_US' ilike 'subcontracting'""",
    """UPDATE stock_picking_type SET sequence=1200 WHERE name->>'en_US' ilike 'resupply subcontractor'""",
    """UPDATE stock_picking_type SET sequence=1300 WHERE name->>'en_US' ilike 'dropship'""",
    """UPDATE stock_picking_type SET sequence=1400 WHERE name->>'en_US' ilike 'dropship subcontractor'""",
    """UPDATE stock_picking_type SET sequence=1500 WHERE name->>'en_US' ilike 'intercompany%'""",
    """UPDATE stock_picking_type SET sequence=1600 WHERE name->>'en_US' ilike 'Quality Control'""",
    """UPDATE stock_picking_type SET sequence=1700 WHERE name->>'en_US' ilike 'Storage'""",
    """UPDATE stock_picking_type SET sequence=1800 WHERE name->>'en_US' ilike 'Cross Dock'""",
]

types = env["stock.picking.type"].sudo().search([("active", "in", (True, False)), ("id", ">=", 1000)], order='id asc')
for t in types:
    prefix = ""
    sufix = "%s/" % t.sequence_code
    if not t.warehouse_id:
        prefix = "%s/" % t.company_id.code
    else:
        prefix = "%s/" % t.warehouse_id.code
    sequence = prefix + sufix
    if t.sequence_code == 'INTWH':
        sequence = "%s/%s/%s/" % (t.warehouse_id.code, t.sequence_code, t.default_location_dest_id.warehouse_id.code)
    sequence += "%(y)s/%(month)s/"
    name = "stock.picking.type sequence %s" % t.name
    if not t.warehouse_id:
        name += " %s" % t.company_id.code
    else:
        name += " %s" % t.warehouse_id.code
    vals = {
      'name': name,
      'prefix': sequence,
      'implementation': "standard",
      'padding': 4,
      'company_id': t.company_id.id,
      'use_date_range': True,
    }
    #raise UserError(str(vals))
    t.sequence_id.update(vals)
    t.sequence_id._next()
    last_picking = env["stock.picking"].sudo().search([("picking_type_id", "=", t.id)], order='id desc', limit=1)
    if last_picking:
        number = float(last_picking.name[-4:])
    else:
        number = 1
    range = t.sequence_id.date_range_ids[0]
    #raise UserError(range.number_next)
    range.update({"number_next": number + 1})