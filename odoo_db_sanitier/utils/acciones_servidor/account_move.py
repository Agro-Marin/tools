queries = [
  """ALTER TABLE account_bank_statement_line DROP CONSTRAINT "account_bank_statement_line_move_id_fkey";""",
  """ALTER TABLE account_bank_statement_line ADD  CONSTRAINT "account_bank_statement_line_move_id_fkey" FOREIGN KEY ("move_id") REFERENCES "public"."account_move" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_full_reconcile DROP CONSTRAINT "account_full_reconcile_exchange_move_id_fkey";""",
  """ALTER TABLE account_full_reconcile ADD  CONSTRAINT "account_full_reconcile_exchange_move_id_fkey" FOREIGN KEY ("exchange_move_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_move DROP CONSTRAINT "account_move_auto_post_origin_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_auto_post_origin_id_fkey" FOREIGN KEY ("auto_post_origin_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_move DROP CONSTRAINT "account_move_reversed_entry_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_reversed_entry_id_fkey" FOREIGN KEY ("reversed_entry_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_move DROP CONSTRAINT "account_move_tax_cash_basis_origin_move_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_tax_cash_basis_origin_move_id_fkey" FOREIGN KEY ("tax_cash_basis_origin_move_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE account_move DROP CONSTRAINT "account_move_tax_cash_basis_rec_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_tax_cash_basis_rec_id_fkey" FOREIGN KEY ("tax_cash_basis_rec_id") REFERENCES "public"."account_partial_reconcile" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_move_id_fkey";""",
  """ALTER TABLE account_move_line ADD  CONSTRAINT "account_move_line_move_id_fkey" FOREIGN KEY ("move_id") REFERENCES "public"."account_move" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_move_purchase_order_rel DROP CONSTRAINT "account_move_purchase_order_rel_account_move_id_fkey";""",
  """ALTER TABLE account_move_purchase_order_rel ADD  CONSTRAINT "account_move_purchase_order_rel_account_move_id_fkey" FOREIGN KEY ("account_move_id") REFERENCES "public"."account_move" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_move__account_payment DROP CONSTRAINT "account_move__account_payment_invoice_id_fkey";""",
  """ALTER TABLE account_move__account_payment ADD  CONSTRAINT "account_move__account_payment_invoice_id_fkey" FOREIGN KEY ("invoice_id") REFERENCES "public"."account_move" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE account_payment DROP CONSTRAINT "account_payment_move_id_fkey";""",
  """ALTER TABLE account_payment ADD  CONSTRAINT "account_payment_move_id_fkey" FOREIGN KEY ("move_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE approval_product_line DROP CONSTRAINT "approval_product_line_account_move_id_fkey";""",
  """ALTER TABLE approval_product_line ADD  CONSTRAINT "approval_product_line_account_move_id_fkey" FOREIGN KEY ("account_move_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE hr_payslip DROP CONSTRAINT "hr_payslip_move_id_fkey";""",
  """ALTER TABLE hr_payslip ADD  CONSTRAINT "hr_payslip_move_id_fkey" FOREIGN KEY ("move_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE l10n_mx_edi_document DROP CONSTRAINT "l10n_mx_edi_document_move_id_fkey";""",
  """ALTER TABLE l10n_mx_edi_document ADD  CONSTRAINT "l10n_mx_edi_document_move_id_fkey" FOREIGN KEY ("move_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
  """ALTER TABLE l10n_mx_edi_invoice_document_ids_rel DROP CONSTRAINT "l10n_mx_edi_invoice_document_ids_rel_invoice_id_fkey";""",
  """ALTER TABLE l10n_mx_edi_invoice_document_ids_rel ADD  CONSTRAINT "l10n_mx_edi_invoice_document_ids_rel_invoice_id_fkey" FOREIGN KEY ("invoice_id") REFERENCES "public"."account_move" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

  """ALTER TABLE pos_order DROP CONSTRAINT "pos_order_account_move_fkey";""",
  """ALTER TABLE pos_order ADD  CONSTRAINT "pos_order_account_move_fkey" FOREIGN KEY ("account_move") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE pos_payment DROP CONSTRAINT "pos_payment_account_move_id_fkey";""",
  """ALTER TABLE pos_payment ADD  CONSTRAINT "pos_payment_account_move_id_fkey" FOREIGN KEY ("account_move_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE pos_session DROP CONSTRAINT "pos_session_move_id_fkey";""",
  """ALTER TABLE pos_session ADD  CONSTRAINT "pos_session_move_id_fkey" FOREIGN KEY ("move_id") REFERENCES "public"."account_move" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",
]
for q in queries:
  env.cr.execute(q)

env.cr.execute("""
SELECT mov.id, mov.name, mov.partner_id, mov.invoice_partner_display_name, mov."date", mov.payment_reference, mov.ref
FROM account_move mov
LEFT JOIN account_journal j ON mov.journal_id=j.id
ORDER BY mov.date, mov.company_id, array_position(ARRAY['purchase', 'sale', 'bank', 'cash', 'general'], j.type), array_position(ARRAY['PF', 'PX', 'PEX', 'PN', 'PNX', 'CF', 'CX', 'CN', 'CNX', 'NOM01', 'NOM02', 'TPV00', 'TPV01', 'TPV02', 'CBMX1', 'EXC01','CABA1', 'CLL01', 'CLL02', 'INC01','INC02','MSC01','MSC02'], j.code), j.code, mov.commercial_partner_id, mov.payment_reference, mov.id
""")
records = env.cr.fetchall()

start = 1001
for i in records:
  env.cr.execute("""UPDATE account_move SET id=%s WHERE id=%s;""" % (start, i[0]))
  start += 1