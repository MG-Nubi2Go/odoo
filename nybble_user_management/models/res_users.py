"""Módulo que modifica la vista de grupos de usuario, excluyendo la categoría 'Administration'."""
from lxml import etree

from odoo import api, models


class GroupsView(models.Model):
    """Modelo que modifica la vista de grupos de usuario, excluyendo la categoría 'Administration'."""

    _inherit = "res.groups"

    @api.model
    def _update_user_groups_view(self):
        """Modifica la vista de grupos de usuario, excluyendo la categoría 'Administration'."""

        # Llamamos al método original
        res = super(GroupsView, self)._update_user_groups_view()

        # Obtener la vista generada
        view = self.env.ref("base.user_groups_view", raise_if_not_found=False)
        if not view:
            return

        # Parseamos la vista actual en XML
        arch = etree.fromstring(view.arch)

        # Buscamos y eliminamos el <group> que contiene "Administration"
        for group in arch.xpath("//group[field[@name='sel_groups_2_4']]"):
            group.set("groups", "base.group_system")

        # Guardamos la vista modificada
        view.arch = etree.tostring(arch, encoding="unicode", pretty_print=True)

        return res
