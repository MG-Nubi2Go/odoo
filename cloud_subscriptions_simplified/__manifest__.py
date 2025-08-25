{
    "name": "Cloud Subscriptions Simplified",
    "version": "18.0.1.0.0",
    "summary": "VM por componentes, prorrateo simple y rebates visibles/ocultos",
    "license": "LGPL-3",
    "depends": ["sale_management", "account"],
    "data": [
        "security/ir.model.access.csv",
        "views/vm_configurator_wizard_views.xml",  # acción & vista del wizard (primero)
        "views/sale_order_inherit_views.xml",      # botón que llama al wizard (después)
    ],
    "installable": True,
    "application": False,
}

