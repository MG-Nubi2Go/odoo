"""Tests for Commission Report functionality."""

import unittest.mock

from odoo.tests.common import TransactionCase


class TestCommissionReport(TransactionCase):
    """Test cases for commission report functionality."""

    def setUp(self):
        """Set up test data."""
        super().setUp()

        # Create test partner
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Customer",
            }
        )

        # Create test vendor
        self.vendor = self.env["res.partner"].create(
            {
                "name": "Test Vendor",
            }
        )

        # Create test user
        self.user = self.env["res.users"].create(
            {
                "name": "Test Salesperson",
                "login": "test_salesperson",
                "email": "test@example.com",
            }
        )

        # Create test product
        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "product",
            }
        )

        # Create commission factors
        self.env["sales.commission.factor"].create(
            [
                {"markup_percentage": 15, "commission_factor": 0.004},
                {"markup_percentage": 20, "commission_factor": 0.010},
            ]
        )

    def test_commission_report_line_fields(self):
        """Test that commission report line contains all required fields."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 100.0,
                "purchase_price": 80.0,
                "product_vendor_id": self.vendor.id,
            }
        )

        # Act
        report_line = self.env["sale.order.line"].browse(order_line.id)

        # Assert
        self.assertEqual(report_line.order_id.name, sale_order.name)
        self.assertEqual(report_line.order_id.partner_id, self.partner)
        self.assertEqual(report_line.product_vendor_id, self.vendor)
        self.assertEqual(report_line.product_id, self.product)
        self.assertEqual(report_line.product_uom_qty, 2.0)
        self.assertEqual(report_line.purchase_price, 80.0)
        self.assertEqual(report_line.price_unit, 100.0)
        self.assertEqual(report_line.markup_amount, 20.0)  # 100 - 80
        self.assertEqual(report_line.markup_percentage, 20.0)  # ((80/100) - 1) * -100
        self.assertEqual(report_line.commission_amount, 2.0)  # 200 * 0.010

    @unittest.mock.patch(
        "odoo.addons.sales_commission_custom.models.sale_order_line.SaleOrderLine._compute_commission_payment_status"
    )
    def test_commission_payment_status_default(self, mock_compute_status):
        """Test that commission payment status defaults to 'pending'."""
        # Arrange
        mock_compute_status.return_value = "pending"

        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 80.0,
            }
        )

        # Assert
        self.assertEqual(order_line.commission_payment_status, "pending")

    def test_commission_payment_status_change(self):
        """Test changing commission payment status from pending to paid."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 80.0,
            }
        )

        # Act
        order_line.commission_payment_status = "paid"

        # Assert
        self.assertEqual(order_line.commission_payment_status, "paid")

    def test_commission_report_action_domain(self):
        """Test that commission report action filters confirmed orders."""
        # Arrange
        action = self.env.ref("sales_commission_custom.action_commission_report_line")

        # Assert
        self.assertIn(("order_id.state", "in", ["sale", "done"]), action.domain)

    def test_commission_report_line_markup_calculation(self):
        """Test markup calculation in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 120.0,
                "purchase_price": 100.0,  # 20% markup
            }
        )

        # Assert
        expected_markup_amount = 20.0  # 120 - 100
        expected_markup_percentage = 20.0  # ((100/120) - 1) * -100

        self.assertEqual(order_line.markup_amount, expected_markup_amount)
        self.assertEqual(order_line.markup_percentage, expected_markup_percentage)

    def test_commission_report_line_commission_calculation(self):
        """Test commission calculation in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 3,
                "price_unit": 100.0,
                "purchase_price": 80.0,  # 20% markup, factor 0.010
            }
        )

        # Assert
        # price_subtotal = 3 * 100 = 300
        # commission = 300 * 0.010 = 3.0
        expected_commission = 300.0 * 0.010
        self.assertEqual(order_line.commission_amount, expected_commission)

    def test_commission_report_line_vendor_assignment(self):
        """Test vendor assignment in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 80.0,
                "product_vendor_id": self.vendor.id,
            }
        )

        # Assert
        self.assertEqual(order_line.product_vendor_id, self.vendor)

    def test_commission_report_line_order_reference(self):
        """Test that commission report line shows correct order reference."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 80.0,
            }
        )

        # Assert
        self.assertEqual(order_line.order_id, sale_order)
        self.assertEqual(order_line.order_id.name, sale_order.name)

    def test_commission_report_line_customer_display(self):
        """Test customer display in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 80.0,
            }
        )

        # Assert
        self.assertEqual(order_line.order_id.partner_id, self.partner)
        self.assertEqual(order_line.order_id.partner_id.name, "Test Customer")

    def test_commission_report_line_product_display(self):
        """Test product display in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 80.0,
            }
        )

        # Assert
        self.assertEqual(order_line.product_id, self.product)
        self.assertEqual(order_line.product_id.name, "Test Product")

    def test_commission_report_line_quantity_display(self):
        """Test quantity display in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 5,
                "price_unit": 100.0,
                "purchase_price": 80.0,
            }
        )

        # Assert
        self.assertEqual(order_line.product_uom_qty, 5.0)

    def test_commission_report_line_cost_display(self):
        """Test cost display in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 75.0,
            }
        )

        # Assert
        self.assertEqual(order_line.purchase_price, 75.0)

    def test_commission_report_line_sale_price_display(self):
        """Test sale price display in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 150.0,
                "purchase_price": 80.0,
            }
        )

        # Assert
        self.assertEqual(order_line.price_unit, 150.0)

    def test_commission_report_line_margin_display(self):
        """Test margin display in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 80.0,
            }
        )

        # Assert
        expected_margin = 20.0  # 100 - 80
        self.assertEqual(order_line.markup_amount, expected_margin)

    def test_commission_report_line_markup_percentage_display(self):
        """Test markup percentage display in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 80.0,  # 20% markup
            }
        )

        # Assert
        expected_markup_percentage = 20.0  # ((80/100) - 1) * -100
        self.assertEqual(order_line.markup_percentage, expected_markup_percentage)

    def test_commission_report_line_commission_display(self):
        """Test commission display in commission report lines."""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 100.0,
                "purchase_price": 80.0,  # 20% markup, factor 0.010
            }
        )

        # Assert
        # price_subtotal = 2 * 100 = 200
        # commission = 200 * 0.010 = 2.0
        expected_commission = 200.0 * 0.010
        self.assertEqual(order_line.commission_amount, expected_commission)
