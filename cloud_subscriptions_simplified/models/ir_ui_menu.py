from odoo import models, api

MODULE_PREFIX = "cloud_subscriptions_simplified."

class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    def load_menus(self, debug=False):
        """Filtra, del árbol de menús, los pertenecientes a este módulo
        cuando la compañía activa no coincide con el parámetro configurado.
        Estrategia robusta:
          - Obtenemos TODOS los ids de menús de este módulo via ir.model.data
          - Llamamos al super para construir el árbol (dict con children)
          - Recortamos recursivamente los nodos cuyo id esté en ese set
            si la compañía activa != parámetro 'cloud.nubi2go_company_name'
        """
        menus = super().load_menus(debug=debug)
        # nombre de compañía permitido
        target_name = self.env['ir.config_parameter'].sudo().get_param(
            'cloud.nubi2go_company_name', 'Nubi2go'
        )
        if self.env.company.name == target_name:
            return menus  # no filtramos si coincide

        # ids de menús de este módulo (por xml_id)
        imd = self.env['ir.model.data'].sudo(False).search([
            ('model', '=', 'ir.ui.menu'),
            ('module', '=', MODULE_PREFIX.rstrip('.').split('.')[0])
        ])
        module_menu_ids = set(imd.mapped('res_id'))

        def prune(node):
            """node: dict con keys 'id', 'children'... devolver True si se queda"""
            if node.get('id') in module_menu_ids:
                return False  # ocultar
            kids = node.get('children') or []
            kept = []
            for child in kids:
                if prune(child):
                    kept.append(child)
            node['children'] = kept
            return True

        # Estructura devuelta por load_menus es un dict con raíz(es)
        # Puede venir como {'children': [...], 'id': x, ...} o lista en ciertas vistas.
        if isinstance(menus, dict) and 'children' in menus:
            menus['children'] = [n for n in menus['children'] if prune(n)]
        elif isinstance(menus, list):
            menus = [n for n in menus if prune(n)]
        return menus
