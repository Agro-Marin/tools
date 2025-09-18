from odoo import fields, models


class TestModel(models.Model):
    _name = "test.model"

    name = fields.Char("Name")

    def action_test(self):
        pass
