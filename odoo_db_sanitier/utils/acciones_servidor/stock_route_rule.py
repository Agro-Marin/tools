queries = """
  ALTER TABLE pos_config DROP CONSTRAINT "pos_config_route_id_fkey";
  ALTER TABLE pos_config ADD  CONSTRAINT "pos_config_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "public"."stock_route" ("id") ON DELETE SET NULL ON UPDATE CASCADE;

  ALTER TABLE stock_move DROP CONSTRAINT "stock_move_rule_id_fkey";
  ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_rule_id_fkey" FOREIGN KEY ("rule_id") REFERENCES "public"."stock_rule" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;

  ALTER TABLE sale_order DROP CONSTRAINT "sale_order_route_id_fkey";
  ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "public"."stock_route" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;
  ALTER TABLE sale_order_line DROP CONSTRAINT "sale_order_line_route_id_fkey";
  ALTER TABLE sale_order_line ADD  CONSTRAINT "sale_order_line_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "public"."stock_route" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;

  ALTER TABLE stock_route_warehouse DROP CONSTRAINT "stock_route_warehouse_route_id_fkey";
  ALTER TABLE stock_route_warehouse ADD  CONSTRAINT "stock_route_warehouse_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "public"."stock_route" ("id") ON DELETE CASCADE ON UPDATE CASCADE;
  ALTER TABLE stock_route_product DROP CONSTRAINT "stock_route_product_route_id_fkey";
  ALTER TABLE stock_route_product ADD  CONSTRAINT "stock_route_product_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "public"."stock_route" ("id") ON DELETE CASCADE ON UPDATE CASCADE;
  ALTER TABLE stock_route_move DROP CONSTRAINT "stock_route_move_route_id_fkey";
  ALTER TABLE stock_route_move ADD  CONSTRAINT "stock_route_move_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "public"."stock_route" ("id") ON DELETE CASCADE ON UPDATE CASCADE;
  ALTER TABLE stock_route_picking_type DROP CONSTRAINT "stock_route_picking_type_route_id_fkey";
  ALTER TABLE stock_route_picking_type ADD  CONSTRAINT "stock_route_picking_type_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "public"."stock_route" ("id") ON DELETE CASCADE ON UPDATE CASCADE;

  ALTER TABLE stock_rule DROP CONSTRAINT "stock_rule_route_id_fkey";
  ALTER TABLE stock_rule ADD  CONSTRAINT "stock_rule_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "public"."stock_route" ("id") ON DELETE SET NULL ON UPDATE CASCADE;

  ALTER TABLE stock_warehouse_orderpoint DROP CONSTRAINT "stock_warehouse_orderpoint_route_id_fkey";
  ALTER TABLE stock_warehouse_orderpoint ADD  CONSTRAINT "stock_warehouse_orderpoint_route_id_fkey" FOREIGN KEY ("route_id") REFERENCES "public"."stock_route" ("id") ON DELETE SET NULL ON UPDATE CASCADE;

  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_crossdock_route_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_crossdock_route_id_fkey" FOREIGN KEY ("crossdock_route_id") REFERENCES "public"."stock_route" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_delivery_route_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_delivery_route_id_fkey" FOREIGN KEY ("delivery_route_id") REFERENCES "public"."stock_route" ("id") ON DELETE SET NULL ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_pbm_route_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_pbm_route_id_fkey" FOREIGN KEY ("pbm_route_id") REFERENCES "public"."stock_route" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_reception_route_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_reception_route_id_fkey" FOREIGN KEY ("reception_route_id") REFERENCES "public"."stock_route" ("id") ON DELETE SET NULL ON UPDATE CASCADE;

  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_crossdock_route_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_crossdock_route_id_fkey" FOREIGN KEY ("crossdock_route_id") REFERENCES "public"."stock_route" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_delivery_route_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_delivery_route_id_fkey" FOREIGN KEY ("delivery_route_id") REFERENCES "public"."stock_route" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_mto_pull_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_mto_pull_id_fkey" FOREIGN KEY ("mto_pull_id") REFERENCES "public"."stock_rule" ("id") ON DELETE SET NULL ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_manufacture_pull_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_manufacture_pull_id_fkey" FOREIGN KEY ("manufacture_pull_id") REFERENCES "public"."stock_rule" ("id") ON DELETE SET NULL ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_manufacture_mto_pull_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_manufacture_mto_pull_id_fkey" FOREIGN KEY ("manufacture_mto_pull_id") REFERENCES "public"."stock_rule" ("id") ON DELETE SET NULL ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_pbm_mto_pull_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_pbm_mto_pull_id_fkey" FOREIGN KEY ("pbm_mto_pull_id") REFERENCES "public"."stock_rule" ("id") ON DELETE SET NULL ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_pbm_route_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_pbm_route_id_fkey" FOREIGN KEY ("pbm_route_id") REFERENCES "public"."stock_route" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_reception_route_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_reception_route_id_fkey" FOREIGN KEY ("reception_route_id") REFERENCES "public"."stock_route" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_sam_rule_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_sam_rule_id_fkey" FOREIGN KEY ("sam_rule_id") REFERENCES "public"."stock_rule" ("id") ON DELETE SET NULL ON UPDATE CASCADE;
  ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_buy_pull_id_fkey";
  ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_buy_pull_id_fkey" FOREIGN KEY ("buy_pull_id") REFERENCES "public"."stock_rule" ("id") ON DELETE SET NULL ON UPDATE CASCADE;
 """
