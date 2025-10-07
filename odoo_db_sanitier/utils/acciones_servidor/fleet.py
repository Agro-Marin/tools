lista = [

  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_vehicle_id_fkey";""",
  """ALTER TABLE account_move_line ADD  CONSTRAINT "account_move_line_vehicle_id_fkey" FOREIGN KEY ("vehicle_id") REFERENCES "public"."fleet_vehicle" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_analytic_distribution_model DROP CONSTRAINT "account_analytic_distribution_model_vehicle_id_fkey";""",
  """ALTER TABLE account_analytic_distribution_model ADD  CONSTRAINT "account_analytic_distribution_model_vehicle_id_fkey" FOREIGN KEY ("vehicle_id") REFERENCES "public"."fleet_vehicle" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE account_analytic_line DROP CONSTRAINT "account_analytic_line_vehicle_id_fkey";""",
  """ALTER TABLE account_analytic_line ADD  CONSTRAINT "account_analytic_line_vehicle_id_fkey" FOREIGN KEY ("vehicle_id") REFERENCES "public"."fleet_vehicle" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE fleet_vehicle_model DROP CONSTRAINT "fleet_vehicle_model_brand_id_fkey";""",
  """ALTER TABLE fleet_vehicle_model ADD  CONSTRAINT "fleet_vehicle_model_brand_id_fkey" FOREIGN KEY ("brand_id") REFERENCES "public"."fleet_vehicle_model_brand" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE fleet_vehicle DROP CONSTRAINT "fleet_vehicle_brand_id_fkey";""",
  """ALTER TABLE fleet_vehicle ADD  CONSTRAINT "fleet_vehicle_brand_id_fkey" FOREIGN KEY ("brand_id") REFERENCES "public"."fleet_vehicle_model_brand" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE fleet_vehicle DROP CONSTRAINT "fleet_vehicle_model_id_fkey";""",
  """ALTER TABLE fleet_vehicle ADD  CONSTRAINT "fleet_vehicle_model_id_fkey" FOREIGN KEY ("model_id") REFERENCES "public"."fleet_vehicle_model" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",


  """DELETE FROM ir_model_data WHERE module='__export__'""",
  """DELETE FROM ir_model_data WHERE module='marin' AND model='fleet.vehicle'""",

]
for query in lista:
  env.cr.execute(query)


model = "fleet.vehicle"
records = env[model].sudo().search([("active", "in", (False, True))], order="id ASC")
for r in records:
    name = "vehicle_%s" % r.id
 
    env["ir.model.data"].create(
        {
            "module": "marin",
            "model": model,
            "name": name,
            "res_id": r.id,
            "noupdate": True,
        }
    )
env.cr.execute("""SELECT MAX(id) FROM fleet_vehicle""")
max = env.cr.fetchall()
env.cr.execute("""SELECT setval('"public"."fleet_vehicle_id_seq"', %s, true);""" % max[0][0])
