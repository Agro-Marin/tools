queries = [

  """ALTER TABLE account_analytic_account DROP CONSTRAINT "account_analytic_account_partner_id_fkey";""",
  """ALTER TABLE account_analytic_account ADD  CONSTRAINT "account_analytic_account_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_analytic_line DROP CONSTRAINT "account_analytic_line_partner_id_fkey";""",
  """ALTER TABLE account_analytic_line  ADD CONSTRAINT "account_analytic_line_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_bank_statement_line DROP CONSTRAINT "account_bank_statement_line_partner_id_fkey";""",
  """ALTER TABLE account_bank_statement_line ADD  CONSTRAINT "account_bank_statement_line_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  
  """ALTER TABLE account_move DROP CONSTRAINT "account_move_partner_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_move DROP CONSTRAINT "account_move_commercial_partner_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_commercial_partner_id_fkey" FOREIGN KEY ("commercial_partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_move DROP CONSTRAINT "account_move_partner_shipping_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_partner_shipping_id_fkey" FOREIGN KEY ("partner_shipping_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_move DROP CONSTRAINT "account_move_partner_bank_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_partner_bank_id_fkey" FOREIGN KEY ("partner_bank_id") REFERENCES "public"."res_partner_bank" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_partner_id_fkey";""",
  """ALTER TABLE account_move_line  ADD CONSTRAINT "account_move_line_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_payment DROP CONSTRAINT "account_payment_partner_id_fkey";""",
  """ALTER TABLE account_payment ADD  CONSTRAINT "account_payment_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE account_payment DROP CONSTRAINT "account_payment_partner_bank_id_fkey";""",
  """ALTER TABLE account_payment ADD  CONSTRAINT "account_payment_partner_bank_id_fkey" FOREIGN KEY ("partner_bank_id") REFERENCES "public"."res_partner_bank" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE account_reconcile_model_res_partner_rel DROP CONSTRAINT "account_reconcile_model_res_partner_rel_res_partner_id_fkey";""",
  """ALTER TABLE account_reconcile_model_res_partner_rel  ADD CONSTRAINT "account_reconcile_model_res_partner_rel_res_partner_id_fkey" FOREIGN KEY ("res_partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE account_reconcile_model_partner_mapping DROP CONSTRAINT "account_reconcile_model_partner_mapping_partner_id_fkey";""",
  """ALTER TABLE account_reconcile_model_partner_mapping ADD  CONSTRAINT "account_reconcile_model_partner_mapping_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE approval_request DROP CONSTRAINT "approval_request_partner_id_fkey";""",
  """ALTER TABLE approval_request ADD  CONSTRAINT "approval_request_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE approval_product_line DROP CONSTRAINT "approval_product_line_partner_id_fkey";""",
  """ALTER TABLE approval_product_line ADD  CONSTRAINT "approval_product_line_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE calendar_attendee DROP CONSTRAINT "calendar_attendee_partner_id_fkey";""",
  """ALTER TABLE calendar_attendee  ADD CONSTRAINT "calendar_attendee_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE calendar_event_res_partner_rel DROP CONSTRAINT "calendar_event_res_partner_rel_res_partner_id_fkey";""",
  """ALTER TABLE calendar_event_res_partner_rel  ADD CONSTRAINT "calendar_event_res_partner_rel_res_partner_id_fkey" FOREIGN KEY ("res_partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",


  """ALTER TABLE discuss_channel_member DROP CONSTRAINT "discuss_channel_member_partner_id_fkey";""",
  """ALTER TABLE discuss_channel_member ADD  CONSTRAINT "discuss_channel_member_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE documents_document DROP CONSTRAINT "documents_document_issued_by_fkey";""",
  """ALTER TABLE documents_document ADD  CONSTRAINT "documents_document_issued_by_fkey" FOREIGN KEY ("issued_by") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE documents_document DROP CONSTRAINT "documents_document_partner_id_fkey";""",
  """ALTER TABLE documents_document ADD  CONSTRAINT "documents_document_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE documents_access DROP CONSTRAINT "documents_access_partner_id_fkey";""",
  """ALTER TABLE documents_access ADD  CONSTRAINT "documents_access_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE fleet_vehicle_log DROP CONSTRAINT "fleet_vehicle_log_vendor_id_fkey";""",
  """ALTER TABLE fleet_vehicle_log ADD  CONSTRAINT "fleet_vehicle_log_vendor_id_fkey" FOREIGN KEY ("vendor_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE gps_geofence DROP CONSTRAINT "gps_geofence_partner_id_fkey";""",
  """ALTER TABLE gps_geofence ADD  CONSTRAINT "gps_geofence_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_address_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_address_id_fkey" FOREIGN KEY ("address_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_work_contact_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_work_contact_id_fkey" FOREIGN KEY ("work_contact_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE hr_employee DROP CONSTRAINT "hr_employee_bank_account_id_fkey";""",
  """ALTER TABLE hr_employee ADD  CONSTRAINT "hr_employee_bank_account_id_fkey" FOREIGN KEY ("bank_account_id") REFERENCES "public"."res_partner_bank" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE hr_job DROP CONSTRAINT "hr_job_address_id_fkey";""",
  """ALTER TABLE hr_job ADD  CONSTRAINT "hr_job_address_id_fkey" FOREIGN KEY ("address_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE knowledge_article_member DROP CONSTRAINT "knowledge_article_member_partner_id_fkey";""",
  """ALTER TABLE knowledge_article_member  ADD CONSTRAINT "knowledge_article_member_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",


  """ALTER TABLE mail_followers DROP CONSTRAINT "mail_followers_partner_id_fkey";""",
  """ALTER TABLE mail_followers  ADD CONSTRAINT "mail_followers_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE mail_mail_res_partner_rel DROP CONSTRAINT "mail_mail_res_partner_rel_res_partner_id_fkey";""",
  """ALTER TABLE mail_mail_res_partner_rel  ADD CONSTRAINT "mail_mail_res_partner_rel_res_partner_id_fkey" FOREIGN KEY ("res_partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE mail_message DROP CONSTRAINT "mail_message_author_id_fkey";""",
  """ALTER TABLE mail_message  ADD CONSTRAINT "mail_message_author_id_fkey" FOREIGN KEY ("author_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE mail_message_res_partner_rel DROP CONSTRAINT "mail_message_res_partner_rel_res_partner_id_fkey";""",
  """ALTER TABLE mail_message_res_partner_rel  ADD CONSTRAINT "mail_message_res_partner_rel_res_partner_id_fkey" FOREIGN KEY ("res_partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE mail_notification DROP CONSTRAINT "mail_notification_res_partner_id_fkey";""",
  """ALTER TABLE mail_notification  ADD CONSTRAINT "mail_notification_res_partner_id_fkey" FOREIGN KEY ("res_partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE mail_notification DROP CONSTRAINT "mail_notification_author_id_fkey";""",
  """ALTER TABLE mail_notification  ADD CONSTRAINT "mail_notification_author_id_fkey" FOREIGN KEY ("author_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE pos_order DROP CONSTRAINT "pos_order_partner_id_fkey";""",
  """ALTER TABLE pos_order ADD  CONSTRAINT "pos_order_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE procurement_group DROP CONSTRAINT "procurement_group_partner_id_fkey";""",
  """ALTER TABLE procurement_group ADD  CONSTRAINT "procurement_group_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE product_supplierinfo DROP CONSTRAINT "product_supplierinfo_partner_id_fkey";""",
  """ALTER TABLE product_supplierinfo ADD  CONSTRAINT "product_supplierinfo_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE product_product DROP CONSTRAINT "product_product_manufacturer_id_fkey";""",
  """ALTER TABLE product_product ADD  CONSTRAINT "product_product_manufacturer_id_fkey" FOREIGN KEY ("manufacturer_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE product_template DROP CONSTRAINT "product_template_manufacturer_id_fkey";""",
  """ALTER TABLE product_template ADD  CONSTRAINT "product_template_manufacturer_id_fkey" FOREIGN KEY ("manufacturer_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE project_project DROP CONSTRAINT "project_project_partner_id_fkey";""",
  """ALTER TABLE project_project  ADD CONSTRAINT "project_project_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE project_task DROP CONSTRAINT "project_task_partner_id_fkey";""",
  """ALTER TABLE project_task ADD  CONSTRAINT "project_task_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE purchase_order DROP CONSTRAINT "purchase_order_dest_address_id_fkey";""",
  """ALTER TABLE purchase_order ADD  CONSTRAINT "purchase_order_dest_address_id_fkey" FOREIGN KEY ("dest_address_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE purchase_order DROP CONSTRAINT "purchase_order_partner_id_fkey";""",
  """ALTER TABLE purchase_order ADD  CONSTRAINT "purchase_order_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE purchase_order_line DROP CONSTRAINT "purchase_order_line_partner_id_fkey";""",
  """ALTER TABLE purchase_order_line ADD  CONSTRAINT "purchase_order_line_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",


  """ALTER TABLE res_company DROP CONSTRAINT "res_company_partner_id_fkey";""",
  """ALTER TABLE res_company ADD  CONSTRAINT "res_company_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",


  """ALTER TABLE res_partner DROP CONSTRAINT "res_partner_commercial_partner_id_fkey";""",
  """ALTER TABLE res_partner  ADD CONSTRAINT "res_partner_commercial_partner_id_fkey" FOREIGN KEY ("commercial_partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE res_partner DROP CONSTRAINT "res_partner_parent_id_fkey";""",
  """ALTER TABLE res_partner  ADD CONSTRAINT "res_partner_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE res_partner_bank DROP CONSTRAINT "res_partner_bank_partner_id_fkey";""",
  """ALTER TABLE res_partner_bank ADD  CONSTRAINT "res_partner_bank_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE res_partner_category DROP CONSTRAINT "res_partner_category_parent_id_fkey";""",
  """ALTER TABLE res_partner_category ADD  CONSTRAINT "res_partner_category_parent_id_fkey" FOREIGN KEY ("parent_id") REFERENCES "public"."res_partner_category" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE res_partner_res_partner_category_rel DROP CONSTRAINT "res_partner_res_partner_category_rel_category_id_fkey";""",
  """ALTER TABLE res_partner_res_partner_category_rel ADD  CONSTRAINT "res_partner_res_partner_category_rel_category_id_fkey" FOREIGN KEY ("category_id") REFERENCES "public"."res_partner_category" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE res_partner_res_partner_category_rel DROP CONSTRAINT "res_partner_res_partner_category_rel_partner_id_fkey";""",
  """ALTER TABLE res_partner_res_partner_category_rel ADD  CONSTRAINT "res_partner_res_partner_category_rel_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",


  """ALTER TABLE res_users DROP CONSTRAINT "res_users_partner_id_fkey";""",
  """ALTER TABLE res_users ADD CONSTRAINT "res_users_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",


  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_commercial_partner_id_fkey";""",
  """ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_commercial_partner_id_fkey" FOREIGN KEY ("commercial_partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_partner_id_fkey";""",
  """ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_partner_invoice_id_fkey";""",
  """ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_partner_invoice_id_fkey" FOREIGN KEY ("partner_invoice_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",
  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_partner_shipping_id_fkey";""",
  """ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_partner_shipping_id_fkey" FOREIGN KEY ("partner_shipping_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order_line DROP CONSTRAINT "sale_order_line_partner_id_fkey";""",
  """ALTER TABLE sale_order_line ADD  CONSTRAINT "sale_order_line_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE slide_slide_partner DROP CONSTRAINT "slide_slide_partner_partner_id_fkey";""",
  """ALTER TABLE slide_slide_partner ADD  CONSTRAINT "slide_slide_partner_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",


  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_partner_id_fkey";""",
  """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_move DROP CONSTRAINT "stock_move_restrict_partner_id_fkey";""",
  """ALTER TABLE stock_move ADD  CONSTRAINT "stock_move_restrict_partner_id_fkey" FOREIGN KEY ("restrict_partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_picking DROP CONSTRAINT "stock_picking_owner_id_fkey";""",
  """ALTER TABLE stock_picking ADD  CONSTRAINT "stock_picking_owner_id_fkey" FOREIGN KEY ("owner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_picking DROP CONSTRAINT "stock_picking_partner_id_fkey";""",
  """ALTER TABLE stock_picking ADD  CONSTRAINT "stock_picking_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_rule DROP CONSTRAINT "stock_rule_partner_address_id_fkey";""",
  """ALTER TABLE stock_rule ADD CONSTRAINT "stock_rule_partner_address_id_fkey" FOREIGN KEY ("partner_address_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_warehouse DROP CONSTRAINT "stock_warehouse_partner_id_fkey";""",
  """ALTER TABLE stock_warehouse ADD  CONSTRAINT "stock_warehouse_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE stock_warehouse_orderpoint DROP CONSTRAINT "stock_warehouse_orderpoint_product_supplier_id_fkey";""",
  """ALTER TABLE stock_warehouse_orderpoint ADD  CONSTRAINT "stock_warehouse_orderpoint_product_supplier_id_fkey" FOREIGN KEY ("product_supplier_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE stock_warehouse_orderpoint DROP CONSTRAINT "stock_warehouse_orderpoint_product_supplier_id_fkey";""",
  """ALTER TABLE stock_warehouse_orderpoint ADD  CONSTRAINT "stock_warehouse_orderpoint_product_supplier_id_fkey" FOREIGN KEY ("product_supplier_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE syngenta_commercial_agreement DROP CONSTRAINT "syngenta_commercial_agreement_partner_id_fkey";""",
  """ALTER TABLE syngenta_commercial_agreement ADD  CONSTRAINT "syngenta_commercial_agreement_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE survey_user_input DROP CONSTRAINT "survey_user_input_partner_id_fkey";""",
  """ALTER TABLE survey_user_input ADD  CONSTRAINT "survey_user_input_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE telegram_chat DROP CONSTRAINT "telegram_chat_partner_id_fkey";""",
  """ALTER TABLE telegram_chat ADD  CONSTRAINT "telegram_chat_partner_id_fkey" FOREIGN KEY ("partner_id") REFERENCES "public"."res_partner" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """DELETE FROM account_move_send_wizard_res_partner_rel""",
  """DELETE FROM account_payment_register""",
  """DELETE FROM authorize_debt_wizard""",
  """DELETE FROM base_partner_merge_automatic_wizard""",
  """DELETE FROM base_partner_merge_automatic_wizard;""",
  """DELETE FROM mail_compose_message""",
  """DELETE FROM mail_message_reaction;""",
  """DELETE FROM mail_message_res_partner_starred_rel;""",
  """DELETE FROM mail_push_device;""",
  """DELETE FROM res_users_settings_volumes;""",
  """DELETE FROM slide_channel_partner;""",

  """DELETE FROM website_visitor""",
  """DELETE FROM ir_model_data WHERE module='__export__';""",
  """DELETE FROM ir_model_data WHERE module='__export__' AND model='res.partner';""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='res.partner' AND res_id>=5000;""",
  """DELETE FROM ir_model_data WHERE module='marin_data' AND model='res.partner' AND res_id>=5000;""",
  
]
for q in queries:
  env.cr.execute(q)


start = 8590
env.cr.execute("""SELECT id, name FROM res_partner WHERE id>=%s ORDER BY id""" % start)
partners = env.cr.fetchall()
#raise UserError(str(partners))
for p in partners:
  env.cr.execute("""UPDATE res_partner SET id=%s WHERE id=%s""" % (start, p[0]))
  start += 1
env.cr.execute("""SELECT MAX(id) FROM res_partner""")
max = env.cr.fetchall()
env.cr.execute("""SELECT setval('"public"."res_partner_id_seq"', %s, true);""" % max[0][0])
model = "res.partner"
records = env[model].sudo().search(
    [("active", "in", [True, False]), ("id", ">=", 5000)], order="id ASC"
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "partner_%s" % r.id

        env["ir.model.data"].create(
            {
                "module": "marin_data",
                "model": model,
                "name": name,
                "res_id": r.id,
                "noupdate": True,
            }
        )