"""Módulo de pruebas unitarias para la modificación de la vista de grupos de usuario."""
from lxml import etree

from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase


class TestResGroupsCustom(TransactionCase):
    """Pruebas unitarias para la modificación de la vista de grupos de usuario."""

    def setUp(self):
        """Configuración inicial para las pruebas."""
        super().setUp()

        # Referencias a modelos y usuarios
        self.Groups = self.env["res.groups"]
        self.View = self.env.ref("base.user_groups_view")

        # Obtener el usuario root (el usuario con acceso total)
        self.admin_user = self.env.ref(
            "base.user_root"
        )  # Usuario con permisos de superadministrador
        self.regular_user = self.env.ref("base.group_user")  # Usuario interno básico

        # Crear un usuario sin permisos administrativos
        self.non_admin_user = (
            self.env["res.users"]
            .sudo()
            .create(
                {
                    "name": "Test User",
                    "login": "testuser",
                    "password": "testpassword",
                    "groups_id": [
                        (6, 0, [self.regular_user.id])
                    ],  # Usuario sin permisos de admin
                    "company_id": self.env.company.id,
                    "company_ids": [(6, 0, [self.env.company.id])],
                }
            )
        )

    def test_admin_can_update_groups_view(self):
        """Verifica que un usuario administrador puede modificar la vista de grupos."""
        self.Groups.with_user(self.admin_user.sudo())._update_user_groups_view()
        updated_view = self.View.read(["arch"])[0]["arch"]

        # Verificar que la vista contiene la restricción correcta para los grupos
        self.assertIn(
            "base.group_system",
            updated_view,
            "El grupo de administración debe estar presente.",
        )

    def test_non_admin_user_cannot_update_groups_view(self):
        """Verifica que un usuario sin permisos no puede modificar la vista de grupos."""
        with self.assertRaises(AccessError):
            self.Groups.with_user(self.non_admin_user)._update_user_groups_view()

    def test_admin_group_restriction_applied(self):
        """Verifica que la vista de grupos excluye correctamente el grupo de administración para usuarios no admin."""
        self.Groups.with_user(self.admin_user.sudo())._update_user_groups_view()
        updated_view = etree.fromstring(self.View.arch)

        # Verificamos que el atributo 'groups' está correctamente aplicado
        for group in updated_view.xpath("//group[field[@name='sel_groups_2_4']]"):
            self.assertEqual(
                group.get("groups"),
                "base.group_system",
                "La vista no está restringida correctamente.",
            )
