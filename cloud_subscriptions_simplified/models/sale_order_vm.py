from odoo import api, fields, models

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Nombre comercial de la VM (editable)
    flavor = fields.Char(string="Flavor")

    # Componentes de la VM
    vcpus = fields.Integer(string="vCPU")
    ram_gb = fields.Integer(string="RAM (GB)")
    disk_gb = fields.Integer(string="Disco (GB)")
    backup_extra_points = fields.Integer(string="Backup extra (pts)")

    # Utilidad: construir el prefijo ncs.g- y etiqueta S/M/L# a partir de vCPU/RAM
    @api.depends("vcpus", "ram_gb")
    def _compute_default_flavor(self):
        for order in self:
            if not order.vcpus or not order.ram_gb:
                continue
            tier = ""
            idx = 1
            v, r = order.vcpus, order.ram_gb
            # Tabla simple como la imagen de referencia
            table = [
                ("small1", 1, 2),
                ("small2", 1, 4),
                ("small3", 2, 4),
                ("medium1", 2, 6),
                ("medium2", 2, 8),
                ("medium3", 4, 8),
                ("medium4", 4, 12),
                ("large1", 4, 16),
                ("large2", 6, 12),
                ("large3", 6, 16),
                ("large4", 8, 16),
                ("large5", 8, 24),
            ]
            # Busca la mejor coincidencia exacta
            for name, tv, tr in table:
                if v == tv and r == tr:
                    tier = name
                    break
            if not tier:
                # fallback: reglas
                if v <= 2 and r <= 4:
                    tier = f"small{max(v,1)}"
                elif v <= 6 and r <= 8:
                    tier = f"medium{max(v//2,1)}"
                else:
                    tier = f"large{max(v//2,1)}"
            # No pisa si el usuario ya lo escribió
            if not order.flavor:
                order.flavor = f"ncs.g-{tier}"

