"""Inherit res.partner to add signup token fields."""
from odoo import fields, models


class ResPartner(models.Model):
    """Inherit res.partner to add signup token fields."""

    _inherit = "res.partner"

    signup_token = fields.Char(
        copy=False,
        groups="base.group_erp_manager,	nybble_user_management.group_user_management",
        compute="_compute_token",
        inverse="_inverse_token",
    )
    signup_type = fields.Char(
        string="Signup Token Type",
        copy=False,
        groups="base.group_erp_manager,	nybble_user_management.group_user_management",
    )
    signup_expiration = fields.Datetime(
        copy=False,
        groups="base.group_erp_manager,	nybble_user_management.group_user_management",
    )
