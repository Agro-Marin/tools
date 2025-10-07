queries = [
    """ALTER TABLE res_partner_res_partner_category_rel DROP CONSTRAINT "res_partner_res_partner_category_rel_category_id_fkey";""",
    """ALTER TABLE res_partner_res_partner_category_rel ADD  CONSTRAINT "res_partner_res_partner_category_rel_category_id_fkey" FOREIGN KEY ("category_id") REFERENCES "public"."res_partner_category" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
]

# Comentarios: UPDATE statements para ir_model_data (no ejecutados en este archivo)
# UPDATE ir_model_data SET name='partner_category_supplier_core' WHERE module='marin' AND model='res.partner.category' AND res_id IN (SELECT id FROM res_partner_category WHERE name->>'en_US'='Supplier - Core business');
# UPDATE ir_model_data SET name='partner_category_supplier_general' WHERE module='marin' AND model='res.partner.category' AND res_id IN (SELECT id FROM res_partner_category WHERE name->>'en_US'='Supplier - General');
# UPDATE ir_model_data SET name='partner_category_supplier_xiuman' WHERE module='marin' AND model='res.partner.category' AND res_id IN (SELECT id FROM res_partner_category WHERE name->>'en_US'='Supplier - Xiuman');
# UPDATE ir_model_data SET name='partner_category_supplier_operations' WHERE module='marin' AND model='res.partner.category' AND res_id IN (SELECT id FROM res_partner_category WHERE name->>'en_US'='Supplier - Operations');
# UPDATE ir_model_data SET name='partner_category_supplier_it' WHERE module='marin' AND model='res.partner.category' AND res_id IN (SELECT id FROM res_partner_category WHERE name->>'en_US'='Supplier - IT');
# UPDATE ir_model_data SET name='partner_category_supplier_management' WHERE module='marin' AND model='res.partner.category' AND res_id IN (SELECT id FROM res_partner_category WHERE name->>'en_US'='Supplier - Management');
# UPDATE ir_model_data SET name='partner_category_high_risk' WHERE module='marin' AND model='res.partner.category' AND res_id IN (SELECT id FROM res_partner_category WHERE name->>'en_US'='High Risk');
