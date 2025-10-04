env.cr.execute("""DELETE FROM ir_model_data WHERE module='__export__' AND model='account.analytic.distribution.model'""")
env.cr.execute("""DELETE FROM ir_model_data WHERE module='marin' AND model='account.analytic.distribution.model'""")
env.cr.execute("""UPDATE account_analytic_distribution_model SET id=id+10000""")
env.cr.execute("""SELECT id FROM account_analytic_distribution_model ORDER BY company_id, product_id, vehicle_id, account_prefix""")
records = env.cr.fetchall()
start = 1001
for r in records:
    env.cr.execute("""UPDATE account_analytic_distribution_model SET id=%s WHERE id=%s""" % (start, r[0]))
    start += 1
model = "account.analytic.distribution.model"
records = env[model].sudo().search([], order="id ASC")
for r in records:
    name = "analytic_distribution_model_%s" % r.id
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