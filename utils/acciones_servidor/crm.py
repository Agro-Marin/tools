lista = [

  """ALTER TABLE account_move DROP CONSTRAINT "account_move_team_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_team_id_fkey" FOREIGN KEY ("team_id") REFERENCES "public"."crm_team" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE sale_order DROP CONSTRAINT "sale_order_team_id_fkey";""",
  """ALTER TABLE sale_order ADD  CONSTRAINT "sale_order_team_id_fkey" FOREIGN KEY ("team_id") REFERENCES "public"."crm_team" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
 
  """ALTER TABLE res_partner DROP CONSTRAINT "res_partner_team_id_fkey";""",
  """ALTER TABLE res_partner ADD  CONSTRAINT "res_partner_team_id_fkey" FOREIGN KEY ("team_id") REFERENCES "public"."crm_team" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE pos_config DROP CONSTRAINT "pos_config_crm_team_id_fkey";""",
  """ALTER TABLE pos_config ADD  CONSTRAINT "pos_config_crm_team_id_fkey" FOREIGN KEY ("crm_team_id") REFERENCES "public"."crm_team" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE pos_order DROP CONSTRAINT "pos_order_crm_team_id_fkey";""",
  """ALTER TABLE pos_order ADD  CONSTRAINT "pos_order_crm_team_id_fkey" FOREIGN KEY ("crm_team_id") REFERENCES "public"."crm_team" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE res_users DROP CONSTRAINT "res_users_sale_team_id_fkey";""",
  """ALTER TABLE res_users ADD  CONSTRAINT "res_users_sale_team_id_fkey" FOREIGN KEY ("sale_team_id") REFERENCES "public"."crm_team" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE team_favorite_user_rel DROP CONSTRAINT "team_favorite_user_rel_team_id_fkey";""",
  """ALTER TABLE team_favorite_user_rel ADD  CONSTRAINT "team_favorite_user_rel_team_id_fkey" FOREIGN KEY ("team_id") REFERENCES "public"."crm_team" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """DELETE FROM ir_model_data WHERE module='marin' AND model='crm.team'""",

]

env.cr.execute("""SELECT MAX(id) FROM crm_team""")
max = env.cr.fetchall()
env.cr.execute("""SELECT setval('"public"."crm_team_id_seq"', %s, true);""" % max[0][0])


