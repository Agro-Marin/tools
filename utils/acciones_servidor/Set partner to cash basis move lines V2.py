apr_obj = env['account.partial.reconcile']
exempt = env["account.tax"].browse(559)
zero = env["account.tax"].browse(552)
conf_param = env["ir.config_parameter"]
latest_id = conf_param.get_param("xiuman.latest_cash_basis_move", 0)
moves = env['account.move'].search([('partner_id', '=', 2424), ('invoice_date', '>=', '2022-01-01'), ('invoice_date', '<', '2023-01-01'), ('move_type','=','in_invoice'), ('journal_id','=',556), ("id", ">", latest_id)], limit=200, order="id ASC")
for move in moves:
    try:
        apr_ids = [apr['partial_id'] for apr in move._get_all_reconciled_invoice_partials()]
        to_reconcile = {}
        for apr_id in apr_ids:
            apr = apr_obj.browse(apr_id)
            to_reconcile[apr_id] = (apr.credit_move_id | apr.debit_move_id)
        move.button_draft()
        for line in move.line_ids.filtered(lambda l: l.display_type == 'product'):
            original_taxes = line.tax_ids
            if not original_taxes:
                original_taxes = zero
            line.update({"tax_ids": False})
            line.update({"tax_ids": original_taxes})
        move.action_post()
        for apr_id in apr_ids:
            to_reconcile[apr_id].reconcile()
    except Exception as err:
        env.cr.rollback()
        log("Error during fix of move %s: %s\n%s" % (move.id, move.name, err))
    finally:
        conf_param.set_param("xiuman.latest_cash_basis_move", move.id)
        env.cr.commit()