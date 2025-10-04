query = [

  """ALTER TABLE account_analytic_line DROP CONSTRAINT "account_analytic_line_product_id_fkey";""",
  """ALTER TABLE account_analytic_line ADD  CONSTRAINT "account_analytic_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_analytic_distribution_model DROP CONSTRAINT "account_analytic_distribution_model_product_id_fkey";""",
  """ALTER TABLE account_analytic_distribution_model ADD  CONSTRAINT "account_analytic_distribution_model_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_product_id_fkey";""",
  """ALTER TABLE account_move_line ADD  CONSTRAINT "account_move_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_move_template_line DROP CONSTRAINT "account_move_template_line_product_id_fkey";""",
  """ALTER TABLE account_move_template_line ADD  CONSTRAINT "account_move_template_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_move_template_line DROP CONSTRAINT "account_move_template_line_product_category_id_fkey";""",
  """ALTER TABLE account_move_template_line ADD  CONSTRAINT "account_move_template_line_product_category_id_fkey" FOREIGN KEY ("product_category_id") REFERENCES "public"."product_category" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE approval_product_line DROP CONSTRAINT "approval_product_line_product_id_fkey";""",
  """ALTER TABLE approval_product_line ADD  CONSTRAINT "approval_product_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE mrp_bom DROP CONSTRAINT "mrp_bom_product_tmpl_id_fkey";""",
  """ALTER TABLE mrp_bom ADD  CONSTRAINT "mrp_bom_product_tmpl_id_fkey" FOREIGN KEY ("product_tmpl_id") REFERENCES "public"."product_template" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_bom DROP CONSTRAINT "mrp_bom_product_id_fkey";""",
  """ALTER TABLE mrp_bom ADD  CONSTRAINT "mrp_bom_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_bom_byproduct DROP CONSTRAINT "mrp_bom_byproduct_product_id_fkey";""",
  """ALTER TABLE mrp_bom_byproduct ADD  CONSTRAINT "mrp_bom_byproduct_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_bom_line DROP CONSTRAINT "mrp_bom_line_product_tmpl_id_fkey";""",
  """ALTER TABLE mrp_bom_line ADD  CONSTRAINT "mrp_bom_line_product_tmpl_id_fkey" FOREIGN KEY ("product_tmpl_id") REFERENCES "public"."product_template" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_bom_line DROP CONSTRAINT "mrp_bom_line_product_id_fkey";""",
  """ALTER TABLE mrp_bom_line ADD  CONSTRAINT "mrp_bom_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_production DROP CONSTRAINT "mrp_production_product_id_fkey";""",
  """ALTER TABLE mrp_production ADD  CONSTRAINT "mrp_production_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_unbuild DROP CONSTRAINT "mrp_unbuild_product_id_fkey";""",
  """ALTER TABLE mrp_unbuild ADD  CONSTRAINT "mrp_unbuild_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE mrp_workcenter_capacity DROP CONSTRAINT "mrp_workcenter_capacity_product_id_fkey";""",
  """ALTER TABLE mrp_workcenter_capacity ADD  CONSTRAINT "mrp_workcenter_capacity_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE pos_category_product_template_rel DROP CONSTRAINT "pos_category_product_template_rel_product_template_id_fkey";""",
  """ALTER TABLE pos_category_product_template_rel ADD  CONSTRAINT "pos_category_product_template_rel_product_template_id_fkey" FOREIGN KEY ("product_template_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE pos_order_line DROP CONSTRAINT "pos_order_line_product_id_fkey";""",
  """ALTER TABLE pos_order_line ADD  CONSTRAINT "pos_order_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE pos_preparation_display_orderline DROP CONSTRAINT "pos_preparation_display_orderline_product_id_fkey";""",
  """ALTER TABLE pos_preparation_display_orderline ADD  CONSTRAINT "pos_preparation_display_orderline_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE product_alternative_rel DROP CONSTRAINT "product_alternative_rel_src_id_fkey";""",
  """ALTER TABLE product_alternative_rel ADD  CONSTRAINT "product_alternative_rel_src_id_fkey" FOREIGN KEY ("src_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE product_alternative_rel DROP CONSTRAINT "product_alternative_rel_dest_id_fkey";""",
  """ALTER TABLE product_alternative_rel ADD  CONSTRAINT "product_alternative_rel_dest_id_fkey" FOREIGN KEY ("dest_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE product_asset_log DROP CONSTRAINT "product_asset_log_product_id_fkey";""",
  """ALTER TABLE product_asset_log ADD  CONSTRAINT "product_asset_log_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE product_asset_log DROP CONSTRAINT "product_asset_log_product_category_id_fkey";""",
  """ALTER TABLE product_asset_log ADD  CONSTRAINT "product_asset_log_product_category_id_fkey" FOREIGN KEY ("product_category_id") REFERENCES "public"."product_category" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE product_category DROP CONSTRAINT "product_category_parent_id_fkey";""",
  """ALTER TABLE product_category ADD  CONSTRAINT "product_category_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "public"."product_category" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE product_category DROP CONSTRAINT "product_category_root_categ_id_fkey";""",
  """ALTER TABLE product_category ADD  CONSTRAINT "product_category_root_categ_id_fkey" FOREIGN KEY ("root_categ_id") REFERENCES "public"."product_category" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE product_optional_rel DROP CONSTRAINT "product_optional_rel_src_id_fkey";""",
  """ALTER TABLE product_optional_rel ADD  CONSTRAINT "product_optional_rel_src_id_fkey" FOREIGN KEY ("src_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE product_optional_rel DROP CONSTRAINT "product_optional_rel_dest_id_fkey";""",
  """ALTER TABLE product_optional_rel ADD  CONSTRAINT "product_optional_rel_dest_id_fkey" FOREIGN KEY ("dest_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE product_product DROP CONSTRAINT "product_product_product_tmpl_id_fkey";""",
  """ALTER TABLE product_product ADD  CONSTRAINT "product_product_product_tmpl_id_fkey" FOREIGN KEY ("product_tmpl_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE product_public_category_product_template_rel DROP CONSTRAINT "product_public_category_product_templa_product_template_id_fkey";""",
  """ALTER TABLE product_public_category_product_template_rel ADD  CONSTRAINT "product_public_category_product_templa_product_template_id_fkey" FOREIGN KEY ("product_template_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE product_supplierinfo DROP CONSTRAINT "product_supplierinfo_product_tmpl_id_fkey";""",
  """ALTER TABLE product_supplierinfo ADD  CONSTRAINT "product_supplierinfo_product_tmpl_id_fkey" FOREIGN KEY ("product_tmpl_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE product_supplierinfo DROP CONSTRAINT "product_supplierinfo_product_id_fkey";""",
  """ALTER TABLE product_supplierinfo ADD  CONSTRAINT "product_supplierinfo_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE product_supplier_taxes_rel DROP CONSTRAINT "product_supplier_taxes_rel_prod_id_fkey";""",
  """ALTER TABLE product_supplier_taxes_rel ADD  CONSTRAINT "product_supplier_taxes_rel_prod_id_fkey" FOREIGN KEY ("prod_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE product_tag_product_template_rel DROP CONSTRAINT "product_tag_product_template_rel_product_tag_id_fkey";""",
  """ALTER TABLE product_tag_product_template_rel ADD  CONSTRAINT "product_tag_product_template_rel_product_tag_id_fkey" FOREIGN KEY ("product_tag_id") REFERENCES "public"."product_tag" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE product_tag_product_template_rel DROP CONSTRAINT "product_tag_product_template_rel_product_template_id_fkey";""",
  """ALTER TABLE product_tag_product_template_rel ADD  CONSTRAINT "product_tag_product_template_rel_product_template_id_fkey" FOREIGN KEY ("product_template_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE product_taxes_rel DROP CONSTRAINT "product_taxes_rel_prod_id_fkey";""",
  """ALTER TABLE product_taxes_rel ADD  CONSTRAINT "product_taxes_rel_prod_id_fkey" FOREIGN KEY ("prod_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE product_template DROP CONSTRAINT "product_template_categ_id_fkey";""",
  """ALTER TABLE product_template ADD  CONSTRAINT "product_template_categ_id_fkey" FOREIGN KEY ("categ_id") REFERENCES "public"."product_category" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE purchase_order_line DROP CONSTRAINT "purchase_order_line_product_id_fkey";""",
  """ALTER TABLE purchase_order_line ADD  CONSTRAINT "purchase_order_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order_line DROP CONSTRAINT "sale_order_line_product_id_fkey";""",
  """ALTER TABLE sale_order_line ADD  CONSTRAINT "sale_order_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order_template_line DROP CONSTRAINT "sale_order_template_line_product_id_fkey";""",
  """ALTER TABLE sale_order_template_line ADD  CONSTRAINT "sale_order_template_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_lot DROP CONSTRAINT "stock_lot_product_id_fkey";""",
  """ALTER TABLE stock_lot ADD  CONSTRAINT "stock_lot_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_product_id_fkey";""",
  """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE stock_move_line DROP CONSTRAINT "stock_move_line_product_id_fkey";""",
  """ALTER TABLE stock_move_line ADD  CONSTRAINT "stock_move_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE stock_quant DROP CONSTRAINT "stock_quant_product_id_fkey";""",
  """ALTER TABLE stock_quant ADD  CONSTRAINT "stock_quant_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE stock_quant DROP CONSTRAINT "stock_quant_product_categ_id_fkey";""",
  """ALTER TABLE stock_quant ADD  CONSTRAINT "stock_quant_product_categ_id_fkey" FOREIGN KEY ("product_categ_id") REFERENCES "public"."product_category" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_route_product DROP CONSTRAINT "stock_route_product_product_id_fkey";""",
  """ALTER TABLE stock_route_product ADD  CONSTRAINT "stock_route_product_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE stock_warehouse_orderpoint DROP CONSTRAINT "stock_warehouse_orderpoint_product_id_fkey";""",
  """ALTER TABLE stock_warehouse_orderpoint ADD  CONSTRAINT "stock_warehouse_orderpoint_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  #Pricelist
  """ALTER TABLE product_pricelist_item DROP CONSTRAINT "product_pricelist_item_pricelist_id_fkey";""",
  """ALTER TABLE product_pricelist_item ADD  CONSTRAINT "product_pricelist_item_pricelist_id_fkey" FOREIGN KEY ("pricelist_id") REFERENCES "public"."product_pricelist" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE pos_config DROP CONSTRAINT "pos_config_pricelist_id_fkey";""",
  """ALTER TABLE pos_config ADD  CONSTRAINT "pos_config_pricelist_id_fkey" FOREIGN KEY ("pricelist_id") REFERENCES "public"."product_pricelist" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE pos_config_product_pricelist_rel DROP CONSTRAINT "pos_config_product_pricelist_rel_product_pricelist_id_fkey";""",
  """ALTER TABLE pos_config_product_pricelist_rel ADD  CONSTRAINT "pos_config_product_pricelist_rel_product_pricelist_id_fkey" FOREIGN KEY ("product_pricelist_id") REFERENCES "public"."product_pricelist" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE pos_order DROP CONSTRAINT "pos_order_pricelist_id_fkey";""",
  """ALTER TABLE pos_order ADD  CONSTRAINT "pos_order_pricelist_id_fkey" FOREIGN KEY ("pricelist_id") REFERENCES "public"."product_pricelist" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_pricelist_id_fkey";""",
  """ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_pricelist_id_fkey" FOREIGN KEY ("pricelist_id") REFERENCES "public"."product_pricelist" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE syngenta_sale_report_line DROP CONSTRAINT "syngenta_sale_report_line_product_id_fkey";""",
  """ALTER TABLE syngenta_sale_report_line ADD  CONSTRAINT "syngenta_sale_report_line_product_id_fkey" FOREIGN KEY ("product_id") REFERENCES "public"."product_product" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """DELETE FROM website_track""",
  """DELETE FROM stock_valuation_layer""",
  """DELETE FROM stock_return_picking_line""",

  """DELETE FROM ir_model_data WHERE module='__export__' AND model='product.template';""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='product.template' AND res_id>1000;""",
  """DELETE FROM ir_model_data WHERE module='marin_data' AND model='product.template' AND res_id>1000;""",
  """DELETE FROM ir_model_data WHERE module='__export__' AND model='product.product';""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='product.product' AND res_id>1000;""",
  """DELETE FROM ir_model_data WHERE module='marin_data' AND model='product.product' AND res_id>1000;""",

]
for q in query:
  env.cr.execute(q)


fix_id = 2453
env.cr.execute("""SELECT id,"name" FROM product_template WHERE id>=%s ORDER BY id""" % fix_id)
records = env.cr.fetchall()
#raise UserError(str(records))
start = fix_id
for r in records:
  q = """UPDATE product_template SET id=%s WHERE id=%s""" % (start, r[0])
  #raise UserError(q)
  env.cr.execute(q)
  start += 1
env.cr.execute("""SELECT id,product_tmpl_id FROM product_product WHERE id>=%s ORDER BY id""" % fix_id)
records = env.cr.fetchall()
#raise UserError(str(categories))
for r in records:
  q = """UPDATE product_product SET id=%s WHERE id=%s""" % (r[1], r[0])
  #raise UserError(q)
  env.cr.execute(q)
model = "product.template"
records = env[model].sudo().search(
    [("active", "in", (False, True)), ("id", ">=", 1000)], order="id ASC"
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "product_template_%s" % r.id
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
model = "product.product"
records = env[model].sudo().search(
        [("active", "in", (False, True)), ("id",">=",1000)], order="id ASC"
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "product_product_%s" % r.id
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
env.cr.execute("""SELECT MAX(id) FROM product_template""")
max = env.cr.fetchall()
env.cr.execute("""SELECT setval('"public"."product_template_id_seq"', %s, true);""" % max[0][0])
env.cr.execute("""SELECT MAX(id) FROM product_product""")
max = env.cr.fetchall()
env.cr.execute("""SELECT setval('"public"."product_product_id_seq"', %s, true);""" % max[0][0])