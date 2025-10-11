queries = [
  """ALTER TABLE project_task DROP CONSTRAINT "project_task_project_id_fkey";""",
  """ALTER TABLE project_task ADD  CONSTRAINT "project_task_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."project_project" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE project_task DROP CONSTRAINT "project_task_stage_id_fkey";""",
  """ALTER TABLE project_task ADD  CONSTRAINT "project_task_stage_id_fkey" FOREIGN KEY ("stage_id") REFERENCES "public"."project_task_type" ("id") ON DELETE RESTRICT ON UPDATE CASCADE;""",

  """ALTER TABLE project_task_type_rel DROP CONSTRAINT "project_task_type_rel_project_id_fkey";""",
  """ALTER TABLE project_task_type_rel ADD  CONSTRAINT "project_task_type_rel_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."project_project" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",
  """ALTER TABLE project_task_type_rel DROP CONSTRAINT "project_task_type_rel_type_id_fkey";""",
  """ALTER TABLE project_task_type_rel ADD  CONSTRAINT "project_task_type_rel_type_id_fkey" FOREIGN KEY ("type_id") REFERENCES "public"."project_task_type" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE project_favorite_user_rel DROP CONSTRAINT "project_favorite_user_rel_project_id_fkey";""",
  """ALTER TABLE project_favorite_user_rel ADD  CONSTRAINT "project_favorite_user_rel_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."project_project" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE project_milestone DROP CONSTRAINT "project_milestone_project_id_fkey";""",
  """ALTER TABLE project_milestone ADD  CONSTRAINT "project_milestone_project_id_fkey" FOREIGN KEY ("project_id") REFERENCES "public"."project_project" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE project_project_project_tags_rel DROP CONSTRAINT "project_project_project_tags_rel_project_project_id_fkey";""",
  """ALTER TABLE project_project_project_tags_rel ADD  CONSTRAINT "project_project_project_tags_rel_project_project_id_fkey" FOREIGN KEY ("project_project_id") REFERENCES "public"."project_project" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """DELETE FROM project_update;""",
  """DELETE FROM ir_model_data WHERE model='project.project';""",
]
for q in queries:
  env.cr.execute(q)


fix_id = 14
env.cr.execute("""SELECT id,"name" FROM project_project WHERE id>=%s ORDER BY id""" % fix_id)
records = env.cr.fetchall()
#raise UserError(str(categories))
start = fix_id
for r in records:
  q = """UPDATE project_project SET id=%s WHERE id=%s""" % (start, r[0])
  #raise UserError(q)
  env.cr.execute(q)
  start += 1
env.cr.execute("""SELECT MAX(id) FROM project_project""")
max = env.cr.fetchall()
env.cr.execute("""SELECT setval('"public"."project_project_id_seq"', %s, true);""" % max[0][0])
model = "project.project"
records = env[model].sudo().search(
    [("active", "in", [True, False]), ("id", ">=", 1)], order="id ASC"
)
for r in records:
    exist = env["ir.model.data"].sudo().search([("model", "=", model), ("res_id", "=", r.id)])
    if not exist:
        name = "project_%s" % r.id
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