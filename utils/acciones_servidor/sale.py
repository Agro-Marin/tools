query = [
  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_sale_order_template_id_fkey";""",
  """ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_sale_order_template_id_fkey" FOREIGN KEY ("sale_order_template_id") REFERENCES "public"."sale_order_template" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order_template_line DROP CONSTRAINT "sale_order_template_line_sale_order_template_id_fkey";""",
  """ALTER TABLE sale_order_template_line ADD  CONSTRAINT "sale_order_template_line_sale_order_template_id_fkey" FOREIGN KEY ("sale_order_template_id") REFERENCES "public"."sale_order_template" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
]

env.cr.execute("""
UPDATE
  sale_order_line
 SET
  product_uom_qty=round(product_uom_qty, 6),
  price_unit=round(price_unit, 6),
  technical_price_unit=round(technical_price_unit, 6),
  price_tax=round(price_tax, 6),
  discount=round(discount, 6),
  price_subtotal=round(price_subtotal, 2),
  price_total=round(price_total, 2),
  price_unit_discounted_taxexc=round(price_unit_discounted_taxexc, 6),
  price_unit_discounted_taxinc=round(price_unit_discounted_taxinc, 6),
  qty_invoiced=round(qty_invoiced, 6),
  qty_to_invoice=round(qty_to_invoice, 6),
  qty_transfered=round(qty_transfered, 6),
  purchase_price=round(purchase_price, 6),
  margin=round(margin, 6),
  margin_percent=round(margin_percent, 6),
  amount_invoiced_taxexc=round(amount_invoiced_taxexc, 2),
  amount_to_invoice_taxexc=round(amount_to_invoice_taxexc, 2)
;""")