#from xmlrpc.client import MAXINT

bsl = self.env['account.bank.statement.line'].sudo().search([('id', '>=', 1)])
count = 0
for st_line in bsl:
    test = f'{st_line.date.strftime("%Y%m%d")}' f'{MAXINT - st_line.sequence:0>10}' f'{st_line.id:0>10}'
    st_line.write({'internal_index': str(test)})
    count += 1
result = count