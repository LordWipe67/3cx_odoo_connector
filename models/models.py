# -*- coding: utf-8 -*-

from odoo import models, fields, api


class Trecxcrm(models.Model):
    _name = 'trecxcrm'
    _description = 'trecxcrm'

    telefono = fields.Char("Risposta Da")
    name = fields.Char("Nome CLiente")
    cognome = fields.Char("Cognome Cliente")
    operatore = fields.Char("Chiamata Da")
    create_date = fields.Datetime("Data")
    data_inizio = fields.Char("Data Inizio")
    data_fine = fields.Char("Data Fine")
    token_call = fields.Char("Token")
    indirizzo_url = fields.Char("URL")
    gestito = fields.Boolean("Gestito")
    note = fields.Text("Note")

# @api.model
# def update_trecxcrm_tree_view(self):
#     view_id = self.env.ref('trecxcrm.trecxcrm_tree_view').id
#     view_pool = self.env['ir.ui.view']
#     view = view_pool.browse(view_id)
#     view.write({'arch': view.arch})
#     return True
#
# # schedulazione dell'aggiornamento della vista ogni 10 secondi
# @api.model
# def schedule_update_trecxcrm_tree_view(self):
#     self.env['ir.cron'].sudo().create(
#         name='Update trecxcrm tree view',
#         user_id=self.env.uid,
#         model='trecxcrm',
#         function='update_trecxcrm_tree_view',
#         interval_number=10,
#         interval_type='seconds',
#         numbercall=-1,
#         doall=True)
#     return True
# Valore non presente nel database

    # @api.depends('value')
    # def _value_pc(self):
    #     for record in self:
    #         record.value2 = float(record.value) / 100
