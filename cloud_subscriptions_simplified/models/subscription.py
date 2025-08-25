from odoo import api, fields, models

class ResPartner(models.Model):
    _inherit = "res.partner"
    show_rebates_on_pdf = fields.Boolean(
        string="Mostrar rebates en PDF",
        help="Tildar para partners reseller; el PDF mostrará líneas marcadas como rebate."
    )

class ProductTemplate(models.Model):
    _inherit = "product.template"
    x_is_rebate = fields.Boolean(string="Es producto Rebate")

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # Config VM
    vcpus = fields.Integer(string="vCPU", default=2)
    ram_gb = fields.Integer(string="RAM (GB)", default=4)
    disk_gb = fields.Integer(string="Disco (GB)", default=50)
    backup_extra_points = fields.Integer(string="Backup extra (pts)", default=0)

    vm_size_label = fields.Char(string="Tamaño VM (S/M/L)",
                                compute="_compute_vm_size_label", store=True)

    # Prorrateo
    x_proration_policy = fields.Selection([
        ('none', 'Sin prorrateo'),
        ('first', 'Prorratear primer mes'),
        ('upsell', 'Prorratear upsells'),
        ('both', 'Prorratear 1er mes y upsells'),
    ], default='both', string="Política de prorrateo")

    # Rebate / reseller
    reseller_partner_id = fields.Many2one('res.partner', string="Reseller (opcional)")
    reseller_rebate_pct = fields.Float(string="% Rebate reseller", digits=(16, 2), default=0.0,
                                       help="Ej: 10.0 = 10% del monto mensual.")

    @api.depends('vcpus', 'ram_gb')
    def _compute_vm_size_label(self):
        for s in self:
            if s.vcpus <= 2 and s.ram_gb <= 4:
                base = "small"
            elif s.vcpus <= 4 and s.ram_gb <= 8:
                base = "medium"
            else:
                base = "large"
            s.vm_size_label = f"{base}-{s.vcpus}"

    # Stubs para que los botones no rompan (los implementamos luego)
    def action_prorate_first_period(self):
        return True

    def action_liquidate_rebate(self):
        return True
