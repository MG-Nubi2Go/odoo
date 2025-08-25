"""Sale Order Line Extensions - Markup calculations and commission tracking."""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SaleOrderLine(models.Model):
    """
    Extended Sale Order Line model with markup calculations and commission tracking.

    Adds functionality to calculate markup percentages, commission factors,
    and commission amounts based on purchase prices and configured factors.
    """

    _inherit = "sale.order.line"

    # Independent vendor field for commission tracking - allows selection of any partner
    product_vendor_id = fields.Many2one(
        "res.partner",
        string="Product Vendor",
        help="Vendor for commission calculation purposes (independent from product vendor)",
    )

    # Computed fields for markup and commission
    markup_percentage = fields.Float(
        string="Markup %",
        compute="_compute_markup_percentage",
        store=True,
        digits=(16, 0),
        help="Markup percentage (rounded): ((purchase_price / price_unit) - 1) × -100",
    )

    markup_amount = fields.Monetary(
        string="Markup Amount",
        compute="_compute_markup_amount",
        store=True,
        help="Absolute markup amount per unit",
    )

    commission_factor = fields.Float(
        string="Commission Factor",
        compute="_compute_commission_factor",
        store=True,
        digits=(16, 6),
        help="Commission factor based on rounded markup percentage",
    )

    commission_amount = fields.Monetary(
        string="Commission Amount",
        compute="_compute_commission_amount",
        store=True,
        help="Total commission amount for this line",
    )

    # Helper fields for UI
    can_edit_product_vendor = fields.Boolean(
        string="Can Edit Product Vendor",
        compute="_compute_can_edit_product_vendor",
        help="Determines if product vendor can be edited based on order state",
    )

    commission_payment_status = fields.Selection(
        [
            ("pending", "Pending Payment"),
            ("paid", "Paid"),
        ],
        string="Commission Payment Status",
        default="pending",
        required=True,
        help="Status of the commission payment for this line.",
        copy=False,
    )

    @api.depends("purchase_price", "price_unit")
    def _compute_markup_percentage(self) -> None:
        """
        Calculate markup percentage using formula: ((purchase_price / price_unit) - 1) × -100.

        Uses purchase_price field from sale_margin module and rounds the result.
        Handles division by zero gracefully by setting markup to 0.0.
        """
        for line in self:
            if line.price_unit and line.purchase_price:
                try:
                    # Formula: ((purchase_price / sale_price) - 1) × -100
                    markup = ((line.purchase_price / line.price_unit) - 1) * -100
                    line.markup_percentage = round(markup)
                except ZeroDivisionError:
                    line.markup_percentage = 0.0
                    _logger.warning(
                        f"Division by zero in markup calculation for line {line.id}"
                    )
            else:
                line.markup_percentage = 0.0

    @api.depends("purchase_price", "price_unit")
    def _compute_markup_amount(self) -> None:
        """
        Calculate absolute markup amount per unit.

        Uses purchase_price field from sale_margin module.
        Calculates the difference between sale price and purchase price.
        """
        for line in self:
            if line.price_unit and line.purchase_price:
                line.markup_amount = line.price_unit - line.purchase_price
            else:
                line.markup_amount = 0.0

    @api.depends("markup_percentage")
    def _compute_commission_factor(self) -> None:
        """
        Get commission factor from configuration based on rounded markup percentage.

        Retrieves the appropriate commission factor from the sales.commission.factor
        model based on the calculated markup percentage.
        """
        for line in self:
            if line.markup_percentage:
                factor_model = self.env["sales.commission.factor"]
                line.commission_factor = factor_model.get_commission_factor(
                    line.markup_percentage
                )
            else:
                line.commission_factor = 0.0

    @api.depends("price_subtotal", "commission_factor")
    def _compute_commission_amount(self) -> None:
        """
        Calculate total commission amount for the line based on price_subtotal.

        Commission is calculated as: price_subtotal × commission_factor.
        """
        for line in self:
            if line.price_subtotal and line.commission_factor:
                # Commission = price_subtotal × commission_factor
                line.commission_amount = line.price_subtotal * line.commission_factor
            else:
                line.commission_amount = 0.0

    @api.depends("order_id.state")
    def _compute_can_edit_product_vendor(self) -> None:
        """
        Determine if product vendor can be edited based on order state.

        Product vendor can only be edited when order is in 'draft' or 'sent' states.
        """
        for line in self:
            line.can_edit_product_vendor = line.order_id.state in ["draft", "sent"]

    def write(self, vals: dict) -> bool:
        """
        Override write to control when product vendor can be modified.

        Args
        ----
        vals : dict
            Dictionary of field values to update

        Returns
        -------
        bool
            True if write operation was successful

        Raises
        ------
        ValidationError
            If attempting to modify product_vendor_id in invalid order state

        """
        if "product_vendor_id" in vals:
            for line in self:
                if not line.can_edit_product_vendor:
                    raise ValidationError(
                        _(
                            "Product vendor can only be modified in 'Draft' or 'Quotation Sent' states"
                        )
                    )
        return super().write(vals)

    def toggle_commission_payment_status(self) -> None:
        """
        Toggle the commission payment status between 'pending' and 'paid'.

        Switches the commission_payment_status field from 'pending' to 'paid' or vice versa.

        Returns
        -------
        None
            This method does not return any value.

        """
        for line in self:
            line.commission_payment_status = (
                "paid" if line.commission_payment_status == "pending" else "pending"
            )


class SaleOrder(models.Model):
    """
    Extended Sale Order model with cost and markup summary calculations.

    Provides order-level summaries of costs, markups, and commission amounts
    calculated from all order lines.
    """

    _inherit = "sale.order"

    # Cost and markup summary fields
    total_cost_amount = fields.Monetary(
        string="Total Cost",
        compute="_compute_total_cost_amount",
        store=True,
        help="Total cost amount for all order lines (sum of purchase_price × quantity)",
    )

    total_markup_amount = fields.Monetary(
        string="Total Markup",
        compute="_compute_total_markup_amount",
        store=True,
        help="Total markup amount (amount_untaxed - total_cost_amount)",
    )

    total_markup_percentage = fields.Float(
        string="Total Markup %",
        compute="_compute_total_markup_percentage",
        store=True,
        digits=(16, 0),
        help="Total markup percentage (rounded) calculated between total cost and amount without taxes",
    )

    # Commission summary field
    total_commission_amount = fields.Monetary(
        string="Total Commission",
        compute="_compute_total_commission_amount",
        store=True,
        help="Total commission amount for all order lines",
    )

    # Commission factor for the entire order
    total_commission_factor = fields.Float(
        string="Total Commission Factor",
        compute="_compute_total_commission_factor",
        store=True,
        digits=(16, 6),
        help="Weighted average commission factor for the entire order",
    )

    @api.depends("order_line.purchase_price", "order_line.product_uom_qty")
    def _compute_total_cost_amount(self) -> None:
        """
        Calculate total cost amount for the entire order.

        Sums up the product of purchase_price × quantity for all order lines.
        """
        for order in self:
            total_cost = 0.0
            for line in order.order_line:
                if line.purchase_price and line.product_uom_qty:
                    total_cost += line.purchase_price * line.product_uom_qty
            order.total_cost_amount = total_cost

    @api.depends("amount_untaxed", "total_cost_amount")
    def _compute_total_markup_amount(self) -> None:
        """
        Calculate total markup amount (amount without taxes - cost amount).

        Represents the total profit margin before taxes for the entire order.
        """
        for order in self:
            order.total_markup_amount = order.amount_untaxed - order.total_cost_amount

    @api.depends("total_cost_amount", "amount_untaxed")
    def _compute_total_markup_percentage(self) -> None:
        """
        Calculate total markup percentage between total cost and amount without taxes (rounded).

        Uses formula: ((total_cost / amount_untaxed) - 1) × -100
        Handles division by zero gracefully by setting percentage to 0.0.
        """
        for order in self:
            if order.amount_untaxed and order.total_cost_amount:
                try:
                    # Formula: ((total_cost / amount_untaxed) - 1) × -100
                    markup_pct = (
                        (order.total_cost_amount / order.amount_untaxed) - 1
                    ) * -100
                    order.total_markup_percentage = round(markup_pct)
                except ZeroDivisionError:
                    order.total_markup_percentage = 0.0
                    _logger.warning(
                        f"Division by zero in total markup calculation for order {order.id}"
                    )
            else:
                order.total_markup_percentage = 0.0

    @api.depends("order_line.commission_factor", "order_line.price_subtotal")
    def _compute_total_commission_factor(self) -> None:
        """
        Calculate weighted average commission factor for the entire order.

        Computes a weighted average based on each line's price_subtotal and commission_factor.
        Formula: Σ(price_subtotal × commission_factor) / Σ(price_subtotal)
        """
        for order in self:
            if order.amount_untaxed and order.order_line:
                total_weighted_factor = 0.0
                total_subtotal = 0.0

                for line in order.order_line:
                    if line.price_subtotal and line.commission_factor:
                        total_weighted_factor += (
                            line.price_subtotal * line.commission_factor
                        )
                        total_subtotal += line.price_subtotal

                if total_subtotal > 0:
                    order.total_commission_factor = (
                        total_weighted_factor / total_subtotal
                    )
                else:
                    order.total_commission_factor = 0.0
            else:
                order.total_commission_factor = 0.0

    @api.depends("amount_untaxed", "total_commission_factor")
    def _compute_total_commission_amount(self) -> None:
        """
        Calculate total commission amount as product of order total and commission factor.

        Total commission = amount_untaxed × total_commission_factor
        """
        for order in self:
            if order.amount_untaxed and order.total_commission_factor:
                order.total_commission_amount = (
                    order.amount_untaxed * order.total_commission_factor
                )
            else:
                order.total_commission_amount = 0.0
