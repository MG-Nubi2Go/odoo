{
    "name": "Sales commissions based on markup",
    "version": "18.0.1.0.0",
    "category": "Sales",
    "summary": "Custom sales commission calculation based on markup",
    "description": """
        Custom Sales Commission Module
        ==============================

        This module provides a custom way to calculate sales commissions based on markup.

        Features:
        ---------
        * Calculate commissions based on markup: ((purchase_price / price_unit) - 1) × -100
        * Configurable commission factors table based on rounded markup percentage
        * Independent vendor field per sale order line
        * Real-time commission calculation using computed fields
        * Vendor assignment only in 'draft' and 'sent' sale order states
        * Commission factors editable only by system administrators
        * Total cost and markup summary at order level
        * Enhanced commission calculation with edge case handling
    """,
    "author": "Nybble Group",
    "website": "https://www.nybblegroup.com",
    "maintainer": "fernando.iocca@nybblegroup.com",
    "license": "LGPL-3",
    "depends": ["sale", "sale_margin"],
    "data": [
        "security/ir.model.access.csv",
        "data/commission_factor_data.xml",
        "views/commission_factor_views.xml",
        "views/sale_order_views.xml",
    ],
    "installable": True,
    "auto_install": False,
    "application": False,
}
