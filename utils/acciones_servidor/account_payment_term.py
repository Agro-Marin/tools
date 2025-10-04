queries = [
  """ALTER TABLE account_move DROP CONSTRAINT "account_move_invoice_payment_term_id_fkey";""",
  """ALTER TABLE account_move ADD  CONSTRAINT "account_move_invoice_payment_term_id_fkey" FOREIGN KEY ("invoice_payment_term_id") REFERENCES "public"."account_payment_term" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

  """ALTER TABLE account_payment_term_line DROP CONSTRAINT "account_payment_term_line_payment_id_fkey";""",
  """ALTER TABLE account_payment_term_line ADD  CONSTRAINT "account_payment_term_line_payment_id_fkey" FOREIGN KEY ("payment_id") REFERENCES "public"."account_payment_term" ("id") ON DELETE CASCADE ON UPDATE CASCADE;""",

]
for q in queries:
  env.cr.execute(q)

env.cr.execute("""UPDATE account_payment_term SET id=id+100000 WHERE id>153""")
env.cr.execute("""SELECT id,name FROM account_payment_term WHERE id>100000 ORDER BY id""")
journals = env.cr.fetchall()

start = 154
for i in journals:
  env.cr.execute("""UPDATE account_payment_term SET id=%s WHERE id=%s;""" % (start, i[0]))
  start += 1
