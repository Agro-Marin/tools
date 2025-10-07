query = [
    """
        DELETE FROM stock_quant WHERE id IN (SELECT q.id FROM stock_quant q
        LEFT JOIN product_template t ON q.product_id=t.id
        WHERE q.lot_id IS NULL AND t.tracking='lot' AND quantity IS NULL) AND lot_id IS NULL
    """,

    """UPDATE stock_quant
    SET expiration_date=lot.expiration_date
    FROM stock_lot lot
    WHERE stock_quant.lot_id=lot.id;""",
    
    """UPDATE stock_quant
    SET removal_date=lot.expiration_date
    FROM stock_lot lot
    WHERE stock_quant.lot_id=lot.id;
    """,
]
query = [
    """DELETE FROM stock_inventory_adjustment_name_stock_quant_rel;""",
    """DELETE FROM stock_quant WHERE location_id IN (4,5,14,15,20,21,33,34,46,47);""",
    """DELETE FROM stock_quant WHERE quantity=0 OR quantity IS NULL;""",
    """DELETE FROM stock_quant WHERE product_id=1765;""",
]
for q in query:
  env.cr.execute(q)

