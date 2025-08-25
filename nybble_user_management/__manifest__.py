{
    "name": "Gestión de Usuarios",
    "summary": "Permite la gestión de usuarios con un grupo de permisos adicional",
    "version": "18.0.1.0.0",
    "category": "Administration",
    "author": "Nybble Group",
    "website": "https://www.nybblegroup.com",
    "depends": ["base", "mail"],
    "data": [
        "security/user_group_views.xml",
        "security/ir.model.access.csv",
        "views/user_management_menus.xml",
        "views/res_user_views.xml",
    ],
    "assets": {},
    "application": True,
    "license": "LGPL-3",
}
