# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Crm_lead(models.Model):
    _inherit = 'crm.lead'

    numero_chiamate = fields.Integer("Numero Chiamate")
    descrizione_chiamate = fields.Char("Numero Chiamate", default="Numero Chiamate")
    ultima_chiamata = fields.Datetime("Ultima Chiamata")
    descrizione_data = fields.Char("Ultima Chiamata", default="Ultima Chiamata")

