# -*- coding: utf-8 -*-

from odoo import models, fields, api


class TrecxRealTime(models.Model):
    _name = 'trecx_realtime'
    _description = '3cx Realtime'

    stato = fields.Char("Stato")
    chiamante = fields.Char("Chiamante")
    chiamato = fields.Char("Chiamato")
    durata = fields.Char("Durata")
    checksum = fields.Char("checksum")