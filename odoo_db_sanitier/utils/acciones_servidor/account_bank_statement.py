queries = [
    """ALTER TABLE account_bank_statement_line DROP CONSTRAINT "account_bank_statement_line_statement_id_fkey";""",
    """ALTER TABLE account_bank_statement_line ADD  CONSTRAINT "account_bank_statement_line_statement_id_fkey" FOREIGN KEY ("statement_id") REFERENCES "public"."account_bank_statement" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

    """ALTER TABLE account_move_line DROP CONSTRAINT "account_move_line_statement_id_fkey";""",
    """ALTER TABLE account_move_line ADD  CONSTRAINT "account_move_line_statement_id_fkey" FOREIGN KEY ("statement_id") REFERENCES "public"."account_bank_statement" ("id") ON DELETE SET NULL ON UPDATE CASCADE;""",

]
for q in queries:
  env.cr.execute(q)

env.cr.execute("""UPDATE account_bank_statement SET id=id+1000000""")
query = """SELECT id,name FROM account_bank_statement ORDER BY name,company_id,journal_id"""
env.cr.execute(query)
records = env.cr.fetchall()
start = 1
for i in records:
  query = """UPDATE account_bank_statement SET id=%s WHERE id=%s;""" % (start, i[0])
  env.cr.execute(query)
  start += 1