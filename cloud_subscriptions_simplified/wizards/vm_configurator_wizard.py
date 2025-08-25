from odoo import api, fields, models

# --- tu tabla FLAVOR_TABLE y suggest_flavor quedan igual ---
FLAVOR_TABLE = [
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

def suggest_flavor(vcpus: int, ram_gb: int) -> str:
    # No sugerir hasta que haya valores válidos
    if not vcpus or not ram_gb:
        return ""

    # 1) Coincidencia exacta en la tabla -> respetar nombre con numerito
    for name, tv, tr in FLAVOR_TABLE:
        if vcpus == tv and ram_gb == tr:
            return f"ncs.g-{name}"  # p.ej. ncs.g-small3

    # 2) Sin match exacto -> nomenclador nuevo sin números
    if vcpus <= 2 and ram_gb <= 4:
        return "ncs.g-small.cus"
    if vcpus <= 6 and ram_gb <= 8:
        return "ncs.g-medium.cus"
    if vcpus <= 8 and ram_gb <= 24:
        return "ncs.g-large.cus"
    return "ncs.g-xlarge"



class VmConfiguratorWizard(models.TransientModel):
    _name = "vm.configurator.wizard"
    _description = "Configurar VM (por cotización)"

    order_id = fields.Many2one("sale.order", required=True)
    vcpus = fields.Integer(string="vCPU", required=True, default=0)
    ram_gb = fields.Integer(string="RAM (GB)", required=True, default=0)
    disk_gb = fields.Integer(string="Disco (GB)", required=True, default=0)
    backup_extra_points = fields.Integer(string="Backup Recovery Points", default=5)

    # visible pero NO editable
    flavor = fields.Char(string="Flavor", readonly=True)

    @api.onchange("vcpus", "ram_gb")
    def _onchange_flavor(self):
        for w in self:
            w.flavor = suggest_flavor(w.vcpus or 0, w.ram_gb or 0)

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        # tomar la cotización actual desde el contexto si no vino en defaults
        if not vals.get("order_id"):
            active_id = self.env.context.get("active_id")
            if active_id and self.env.context.get("active_model") == "sale.order":
                vals["order_id"] = active_id
        # inicializar flavor sugerido
        v = vals.get("vcpus", 2)
        r = vals.get("ram_gb", 4)
        vals["flavor"] = suggest_flavor(v, r)
        return vals

    # ---------------- utilidades ----------------

    def _ensure_products(self):
        get = lambda n: self.env["product.product"].search([("name", "=", n)], limit=1)
        prod_cpu = get("CPU vCore")
        prod_ram = get("RAM GB")
        prod_disk = get("Disco GB")
        prod_backup = get("Backup – puntos extra") or get("Backup - puntos extra")
        if not (prod_cpu and prod_ram and prod_disk):
            raise ValueError("Faltan productos base: 'CPU vCore', 'RAM GB', 'Disco GB'.")
        return prod_cpu, prod_ram, prod_disk, prod_backup

    def _next_sequence(self, order):
        seqs = order.order_line.mapped("sequence") or [0]
        return max(seqs) + 10

    def _unique_section_title(self, order, base_title):
        """Si ya existe una sección [VM] base_title, sumar sufijo -2, -3, ..."""
        section_prefix = f"[VM] {base_title}"
        existing = order.order_line.filtered(
            lambda l: l.display_type == "line_section" and l.name.startswith(section_prefix)
        )
        if not existing:
            return base_title
        # contar existentes con ese prefijo
        count = len(existing) + 1
        return f"{base_title}-{count}"

    def _add_section(self, order, title, seq):
        return self.env["sale.order.line"].create({
            "order_id": order.id,
            "display_type": "line_section",
            "name": f"[VM] {title}",
            "sequence": seq,
        })

    # ---------------- acción principal ----------------

    def action_apply(self):
        self.ensure_one()
        order = self.order_id
        prod_cpu, prod_ram, prod_disk, prod_backup = self._ensure_products()

        # calcular SIEMPRE en servidor para evitar desfasajes de UI
        flavor = suggest_flavor(self.vcpus, self.ram_gb)
        # título único por VM en esta cotización
        title = self._unique_section_title(order, flavor)

        # (opcional) si tenés campos en el pedido para última configuración, podés guardarlos;
        # no afecta el título de la sección ni nombres de líneas
        # order.write({
        #     "vcpus": self.vcpus,
        #     "ram_gb": self.ram_gb,
        #     "disk_gb": self.disk_gb,
        #     "backup_extra_points": self.backup_extra_points,
        #     "flavor": flavor,
        # })

        # crear bloque de líneas
        seq = self._next_sequence(order)
        self._add_section(order, title, seq); seq += 1

        create = self.env["sale.order.line"].create
        create({"order_id": order.id, "product_id": prod_cpu.id,  "product_uom_qty": self.vcpus, "sequence": seq}); seq += 1
        create({"order_id": order.id, "product_id": prod_ram.id,  "product_uom_qty": self.ram_gb, "sequence": seq}); seq += 1
        create({"order_id": order.id, "product_id": prod_disk.id, "product_uom_qty": self.disk_gb, "sequence": seq}); seq += 1
        if prod_backup and self.backup_extra_points:
            create({"order_id": order.id, "product_id": prod_backup.id, "product_uom_qty": self.backup_extra_points, "sequence": seq})

        return {"type": "ir.actions.act_window_close"}

