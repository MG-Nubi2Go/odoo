"""Test Commission Calculation - Unit tests for commission calculation functionality."""

import logging

from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase

_logger = logging.getLogger(__name__)


class TestCommissionCalculation(TransactionCase):
    """Test commission calculation functionality"""

    def setUp(self):
        """
        Set up test data for commission calculation tests.

        Creates test partners, products, users, and commission factors
        needed for testing commission calculation functionality.
        """
        super().setUp()

        # Deactivate existing commission factors to avoid conflicts
        existing_factors = self.env["sales.commission.factor"].search(
            [("active", "=", True)]
        )
        existing_factors.write({"active": False})

        # Create test data
        self.partner = self.env["res.partner"].create(
            {
                "name": "Test Customer",
                "is_company": True,
            }
        )

        self.vendor = self.env["res.partner"].create(
            {
                "name": "Test Vendor",
                "is_company": True,
                "supplier_rank": 1,
            }
        )

        # Create another partner that is not a supplier
        self.regular_partner = self.env["res.partner"].create(
            {
                "name": "Regular Partner",
                "is_company": True,
                "supplier_rank": 0,
            }
        )

        self.product = self.env["product.product"].create(
            {
                "name": "Test Product",
                "type": "consu",
                "list_price": 100.0,
                "standard_price": 80.0,
            }
        )

        self.user = self.env["res.users"].create(
            {
                "name": "Test Salesperson",
                "login": "test_sales",
                "email": "test@example.com",
            }
        )

        # Create commission factors for testing edge cases with unique values
        self.commission_factor_10 = self.env["sales.commission.factor"].create(
            {
                "markup_percentage": 10,
                "commission_factor": 0.002,
            }
        )

        self.commission_factor_15 = self.env["sales.commission.factor"].create(
            {
                "markup_percentage": 15,
                "commission_factor": 0.004,
            }
        )

        self.commission_factor_20 = self.env["sales.commission.factor"].create(
            {
                "markup_percentage": 20,
                "commission_factor": 0.010,
            }
        )

        self.commission_factor_30 = self.env["sales.commission.factor"].create(
            {
                "markup_percentage": 30,
                "commission_factor": 0.015,
            }
        )

    def tearDown(self):
        """Clean up after tests"""
        super().tearDown()
        # Note: TransactionCase automatically rolls back transactions,
        # so explicit cleanup is not strictly necessary, but we can add it for clarity

    def test_commission_factor_creation(self):
        """Test commission factor model creation and validation"""
        # Arrange
        factor_data = {
            "markup_percentage": 25,
            "commission_factor": 0.012,
        }

        # Act
        factor = self.env["sales.commission.factor"].create(factor_data)

        # Assert
        self.assertEqual(factor.markup_percentage, 25)
        self.assertEqual(factor.commission_factor, 0.012)
        self.assertEqual(factor.display_name, "Markup 25% → Factor 0.012")
        self.assertTrue(factor.active)

    def test_commission_factor_get_commission_factor_exact_match(self):
        """Test the get_commission_factor method with exact match"""
        # Arrange
        factor_model = self.env["sales.commission.factor"]

        # Act & Assert - existing factor
        result = factor_model.get_commission_factor(15.0)
        self.assertEqual(result, 0.004)

        result = factor_model.get_commission_factor(20.0)
        self.assertEqual(result, 0.010)

    def test_commission_factor_get_commission_factor_below_minimum(self):
        """Test get_commission_factor when markup is below minimum configured value"""
        # Arrange
        factor_model = self.env["sales.commission.factor"]

        # Act - markup below minimum (10% is the minimum in our setup)
        result = factor_model.get_commission_factor(5.0)

        # Assert - should return the minimum factor (0.002 for 10%)
        self.assertEqual(result, 0.002)

        # Test with another value below minimum
        result = factor_model.get_commission_factor(8.0)
        self.assertEqual(result, 0.002)

    def test_commission_factor_get_commission_factor_above_maximum(self):
        """Test get_commission_factor when markup is above maximum configured value"""
        # Arrange
        factor_model = self.env["sales.commission.factor"]

        # Act - markup above maximum (30% is the maximum in our setup)
        result = factor_model.get_commission_factor(35.0)

        # Assert - should return the maximum factor (0.015 for 30%)
        self.assertEqual(result, 0.015)

        # Test with another value above maximum
        result = factor_model.get_commission_factor(50.0)
        self.assertEqual(result, 0.015)

    def test_commission_factor_get_commission_factor_within_range_no_exact_match(self):
        """Test get_commission_factor when markup is within range but no exact match"""
        # Arrange
        factor_model = self.env["sales.commission.factor"]

        # Act - markup within range but no exact match (between 15% and 20%)
        result = factor_model.get_commission_factor(17.0)

        # Assert - should return 0.0 as no exact match and within range
        self.assertEqual(result, 0.0)

    def test_commission_factor_get_commission_factor_no_factors_configured(self):
        """Test get_commission_factor when no factors are configured"""
        # Arrange
        factor_model = self.env["sales.commission.factor"]
        # Deactivate all existing factors
        all_factors = factor_model.search([("active", "=", True)])
        all_factors.write({"active": False})

        # Act
        result = factor_model.get_commission_factor(15.0)

        # Assert
        self.assertEqual(result, 0.0)

    def test_commission_factor_get_commission_factor_rounding(self):
        """Test that markup percentage is properly rounded"""
        # Arrange
        factor_model = self.env["sales.commission.factor"]

        # Act & Assert - should round to nearest integer
        result = factor_model.get_commission_factor(
            14.4
        )  # Should round to 14 (within range but no exact factor)
        self.assertEqual(
            result, 0.0
        )  # Should return 0.0 as no exact match within range

        result = factor_model.get_commission_factor(14.6)  # Should round to 15
        self.assertEqual(result, 0.004)  # Should use exact match for 15%

    def test_sale_order_line_markup_calculation_rounded(self):
        """Test markup percentage calculation is rounded to integer"""
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
                "purchase_price": 80.0,  # Using sale_margin field
            }
        )

        # Assert
        # Formula: ((purchase_price / price_unit) - 1) × -100 = 20%
        # Should be rounded to integer
        self.assertEqual(order_line.markup_percentage, 20.0)

    def test_sale_order_line_markup_calculation_with_rounding(self):
        """Test markup percentage calculation with decimal that needs rounding"""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act - Create line that results in decimal markup percentage
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 83.33,  # Results in ~16.67% markup, should round to 17%
            }
        )

        # Assert
        # Formula: ((83.33 / 100) - 1) × -100 = 16.67% → rounds to 17%
        self.assertEqual(order_line.markup_percentage, 17.0)

    def test_sale_order_line_commission_amount_calculation(self):
        """Test commission amount calculation in sale order lines based on price_subtotal"""
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
        # Commission = price_subtotal × commission_factor
        # price_subtotal = price_unit × quantity = 100.0 × 2 = 200.0
        # Commission = 200.0 × 0.010 = 2.0
        expected_commission = 200.0 * 0.010
        self.assertEqual(order_line.commission_amount, expected_commission)

    def test_sale_order_total_cost_amount_calculation(self):
        """Test total cost amount calculation at order level"""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act - Create multiple lines with different costs
        line1 = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 100.0,
                "purchase_price": 80.0,  # total_cost = 80 × 2 = 160
            }
        )

        line2 = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 50.0,
                "purchase_price": 40.0,  # total_cost = 40 × 1 = 40
            }
        )

        # Assert
        # total_cost_amount = 160 + 40 = 200
        expected_total_cost = 160.0 + 40.0
        self.assertEqual(sale_order.total_cost_amount, expected_total_cost)

    def test_sale_order_total_markup_amount_calculation(self):
        """Test total markup amount calculation at order level using amount_untaxed"""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act
        line1 = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 100.0,
                "purchase_price": 80.0,  # cost = 160, subtotal = 200
            }
        )

        line2 = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 50.0,
                "purchase_price": 40.0,  # cost = 40, subtotal = 50
            }
        )

        # Assert
        # total_cost_amount = 200, amount_untaxed = 250
        # total_markup_amount = amount_untaxed - total_cost_amount = 250 - 200 = 50
        expected_markup_amount = (
            sale_order.amount_untaxed - sale_order.total_cost_amount
        )
        self.assertEqual(sale_order.total_markup_amount, expected_markup_amount)
        self.assertEqual(sale_order.total_markup_amount, 50.0)

    def test_sale_order_total_markup_percentage_calculation_rounded(self):
        """Test total markup percentage calculation is rounded to integer"""
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
        # Formula: ((total_cost / amount_untaxed) - 1) × -100
        # ((80 / 100) - 1) × -100 = 20% (should be rounded to integer)
        self.assertEqual(sale_order.total_markup_percentage, 20.0)

    def test_sale_order_total_markup_percentage_with_rounding(self):
        """Test total markup percentage calculation with decimal that needs rounding"""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act - Create scenario that results in decimal markup percentage
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 83.33,  # Results in ~16.67% markup, should round to 17%
            }
        )

        # Assert
        # Formula: ((83.33 / 100) - 1) × -100 = 16.67% → rounds to 17%
        self.assertEqual(sale_order.total_markup_percentage, 17.0)

    def test_sale_order_line_commission_calculation_edge_cases(self):
        """Test commission calculation with edge cases (below min, above max) based on price_subtotal"""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Test case 1: Markup below minimum (should use minimum factor)
        order_line_low = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 95.0,  # 5% markup (below min 10%), should use 0.002 factor
            }
        )

        # Assert: 5% markup should use minimum factor (0.002)
        # Commission = price_subtotal × commission_factor = 100.0 × 0.002 = 0.2
        expected_commission_low = 100.0 * 0.002
        self.assertEqual(order_line_low.commission_amount, expected_commission_low)
        self.assertEqual(
            order_line_low.markup_percentage, 5.0
        )  # Should be rounded to 5

        # Test case 2: Markup above maximum (should use maximum factor)
        order_line_high = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 60.0,  # 40% markup (above max 30%), should use 0.015 factor
            }
        )

        # Assert: 40% markup should use maximum factor (0.015)
        # Commission = price_subtotal × commission_factor = 100.0 × 0.015 = 1.5
        expected_commission_high = 100.0 * 0.015
        self.assertEqual(order_line_high.commission_amount, expected_commission_high)
        self.assertEqual(
            order_line_high.markup_percentage, 40.0
        )  # Should be rounded to 40

    def test_sale_order_line_commission_with_multiple_quantities(self):
        """Test commission calculation with multiple quantities"""
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
                "purchase_price": 80.0,  # 20% markup, factor 0.010
            }
        )

        # Assert
        # Commission = price_subtotal × commission_factor
        # price_subtotal = price_unit × quantity = 100.0 × 5 = 500.0
        # Commission = 500.0 × 0.010 = 5.0
        expected_commission = 500.0 * 0.010
        self.assertEqual(order_line.commission_amount, expected_commission)
        self.assertEqual(order_line.price_subtotal, 500.0)

    def test_sale_order_complex_cost_markup_scenario(self):
        """Test a complex scenario with multiple lines and different markups using amount_untaxed"""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act - Create lines with different markups and quantities
        line1 = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 100.0,
                "purchase_price": 80.0,  # 20% markup, cost=160, subtotal=200
            }
        )

        line2 = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 150.0,
                "purchase_price": 120.0,  # 20% markup, cost=120, subtotal=150
            }
        )

        line3 = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 3,
                "price_unit": 50.0,
                "purchase_price": 45.0,  # 10% markup, cost=135, subtotal=150
            }
        )

        # Assert totals
        expected_total_cost = 160.0 + 120.0 + 135.0  # 415
        expected_total_sale_untaxed = 200.0 + 150.0 + 150.0  # 500
        expected_total_markup = expected_total_sale_untaxed - expected_total_cost  # 85
        # expected_markup_pct = ((415 / 500) - 1) × -100 = 17% (rounded)
        expected_markup_pct = 17.0

        self.assertEqual(sale_order.total_cost_amount, expected_total_cost)
        self.assertEqual(sale_order.amount_untaxed, expected_total_sale_untaxed)
        self.assertEqual(sale_order.total_markup_amount, expected_total_markup)
        self.assertEqual(sale_order.total_markup_percentage, expected_markup_pct)

    def test_product_vendor_allows_any_partner_selection(self):
        """Test that product_vendor_id allows selection of any partner"""
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
            }
        )

        # Act & Assert - Can assign supplier partner
        order_line.product_vendor_id = self.vendor.id
        self.assertEqual(order_line.product_vendor_id, self.vendor)

        # Act & Assert - Can assign regular partner (not supplier)
        order_line.product_vendor_id = self.regular_partner.id
        self.assertEqual(order_line.product_vendor_id, self.regular_partner)

        # Act & Assert - Can assign customer partner
        order_line.product_vendor_id = self.partner.id
        self.assertEqual(order_line.product_vendor_id, self.partner)

    def test_product_vendor_manual_assignment_only(self):
        """Test that product_vendor_id is only assigned manually (not automatically)"""
        # Arrange
        sale_order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act - Create order line with product
        order_line = self.env["sale.order.line"].create(
            {
                "order_id": sale_order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
            }
        )

        # Assert - product_vendor_id should be empty (not automatically set)
        self.assertFalse(order_line.product_vendor_id)

    def test_sale_order_line_vendor_assignment_blocked_confirmed_state(self):
        """Test that product vendor cannot be modified in confirmed state"""
        # Arrange
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "product_vendor_id": self.vendor.id,
            }
        )

        # Act - confirm the order
        order.action_confirm()

        # Assert - should not be able to modify product_vendor_id
        with self.assertRaises(ValidationError):
            line.write({"product_vendor_id": self.regular_partner.id})

    def test_sale_order_total_commission_amount_calculation(self):
        """Test total commission amount calculation as product of order total and commission factor"""
        # Arrange
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Create lines with different markup percentages to get different commission factors
        line1 = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 2,
                "price_unit": 100.0,
                "purchase_price": 80.0,  # 20% markup
            }
        )

        line2 = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 85.0,  # 15% markup
            }
        )

        # Act - trigger computation
        order._compute_total_commission_amount()

        # Assert
        # Expected calculation:
        # - Line 1: 2 units * 100 = 200 subtotal, 20% markup → factor 0.010, commission = 200 * 0.010 = 2.0
        # - Line 2: 1 unit * 100 = 100 subtotal, 15% markup → factor 0.004, commission = 100 * 0.004 = 0.4
        # - Total order amount: 300
        # - Weighted average factor = (200 * 0.010 + 100 * 0.004) / 300 = (2.0 + 0.4) / 300 = 0.008
        # - Total commission = 300 * 0.008 = 2.4

        expected_commission = 2.4
        self.assertEqual(order.total_commission_amount, expected_commission)

        # Verify the commission factor calculation
        expected_factor = (200 * 0.010 + 100 * 0.004) / 300  # 0.008
        self.assertEqual(order.total_commission_factor, expected_factor)

    def test_sale_order_total_commission_amount_with_zero_markup(self):
        """Test total commission amount when markup is zero"""
        # Arrange
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Create line with zero markup (purchase_price = price_unit)
        line = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 100.0,  # 0% markup
            }
        )

        # Act - trigger computation
        order._compute_total_commission_amount()

        # Assert - commission should be zero when markup is zero
        self.assertEqual(order.total_commission_amount, 0.0)

    def test_sale_order_total_commission_amount_empty_order(self):
        """Test total commission amount for empty order"""
        # Arrange
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Act - trigger computation
        order._compute_total_commission_amount()

        # Assert - commission should be zero for empty order
        self.assertEqual(order.total_commission_amount, 0.0)

    def test_sale_order_total_commission_factor_calculation(self):
        """Test total commission factor calculation as weighted average"""
        # Arrange
        order = self.env["sale.order"].create(
            {
                "partner_id": self.partner.id,
                "user_id": self.user.id,
            }
        )

        # Create lines with different subtotals and commission factors
        line1 = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 3,
                "price_unit": 100.0,
                "purchase_price": 80.0,  # 20% markup → factor 0.010
            }
        )

        line2 = self.env["sale.order.line"].create(
            {
                "order_id": order.id,
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
                "purchase_price": 85.0,  # 15% markup → factor 0.004
            }
        )

        # Act - trigger computation
        order._compute_total_commission_factor()

        # Assert
        # Line 1: 300 subtotal, factor 0.010
        # Line 2: 100 subtotal, factor 0.004
        # Weighted average = (300 * 0.010 + 100 * 0.004) / 400 = (3.0 + 0.4) / 400 = 0.0085
        expected_factor = (300 * 0.010 + 100 * 0.004) / 400
        self.assertEqual(order.total_commission_factor, expected_factor)
