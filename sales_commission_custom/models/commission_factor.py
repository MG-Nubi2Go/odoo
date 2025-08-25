"""Commission Factor Model - Configuration for commission calculations based on markup percentages."""

import logging

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class CommissionFactor(models.Model):
    """
    Configuration model for commission factors based on markup percentages.

    This model stores the relationship between markup percentages and their
    corresponding commission factors used in sales commission calculations.
    """

    _name = "sales.commission.factor"
    _description = "Commission Factor Configuration"
    _order = "markup_percentage ASC"
    _rec_name = "display_name"

    markup_percentage = fields.Integer(
        string="Markup Percentage",
        required=True,
        help="Rounded markup percentage (e.g., 15 for 15%)",
    )
    commission_factor = fields.Float(
        string="Commission Factor",
        required=True,
        digits=(16, 6),
        help="Factor to multiply with markup to calculate commission (e.g., 0.004)",
    )
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    active = fields.Boolean(string="Active", default=True)

    @api.depends("markup_percentage", "commission_factor")
    def _compute_display_name(self) -> None:
        """
        Compute a readable display name for the record.

        Creates a display name in the format "Markup X% → Factor Y"
        based on the markup percentage and commission factor values.
        """
        for record in self:
            record.display_name = f"Markup {record.markup_percentage}% → Factor {record.commission_factor}"

    @api.constrains("markup_percentage")
    def _check_markup_percentage(self) -> None:
        """
        Validate markup percentage values.

        Ensures markup percentage is within valid range (0-1000%).

        Raises
        ------
        ValidationError
            If markup percentage is negative or exceeds 1000%.

        """
        for record in self:
            if record.markup_percentage < 0:
                raise ValidationError(_("Markup percentage cannot be negative"))
            if record.markup_percentage > 1000:
                raise ValidationError(_("Markup percentage cannot exceed 1000%"))

    @api.constrains("commission_factor")
    def _check_commission_factor(self) -> None:
        """
        Validate commission factor values.

        Ensures commission factor is within valid range (0-1).

        Raises
        ------
        ValidationError
            If commission factor is negative or exceeds 1.0.

        """
        for record in self:
            if record.commission_factor < 0:
                raise ValidationError(_("Commission factor cannot be negative"))
            if record.commission_factor > 1:
                raise ValidationError(_("Commission factor cannot exceed 1.0"))

    @api.constrains("markup_percentage")
    def _check_unique_markup_percentage(self) -> None:
        """
        Ensure each markup percentage is unique.

        Validates that no duplicate markup percentages exist in active records.

        Raises
        ------
        ValidationError
            If markup percentage already exists in another active record.

        """
        for record in self:
            existing = self.search(
                [
                    ("markup_percentage", "=", record.markup_percentage),
                    ("id", "!=", record.id),
                    ("active", "=", True),
                ]
            )
            if existing:
                raise ValidationError(
                    _("Markup percentage %s%% already exists")
                    % record.markup_percentage
                )

    @api.model
    def get_commission_factor(self, markup_percentage: float) -> float:
        """
        Get commission factor for a given markup percentage.

        Logic:
        1. Try to find exact match first
        2. If markup is below minimum table value, use minimum factor
        3. If markup is above maximum table value, use maximum factor
        4. If no factors configured, return 0.0

        Args
        ----
        markup_percentage : float
            The markup percentage (rounded)

        Returns
        -------
        float
            Commission factor for the given markup percentage

        Raises
        ------
        None
            This method does not raise exceptions, returns 0.0 for edge cases

        """
        rounded_markup = round(markup_percentage)

        # Get all active factors ordered by markup_percentage
        all_factors = self.search(
            [("active", "=", True)], order="markup_percentage ASC"
        )

        if not all_factors:
            _logger.warning("No commission factors configured")
            return 0.0

        # Try to find exact match first
        exact_match = all_factors.filtered(
            lambda f: f.markup_percentage == rounded_markup
        )
        if exact_match:
            return exact_match.commission_factor

        # Get min and max values from the table
        min_factor_record = all_factors[0]  # First record (lowest markup)
        max_factor_record = all_factors[-1]  # Last record (highest markup)

        # If markup is below minimum, use minimum factor
        if rounded_markup < min_factor_record.markup_percentage:
            _logger.info(
                f"Markup {rounded_markup}% is below minimum {min_factor_record.markup_percentage}%, using minimum factor {min_factor_record.commission_factor}"
            )
            return min_factor_record.commission_factor

        # If markup is above maximum, use maximum factor
        if rounded_markup > max_factor_record.markup_percentage:
            _logger.info(
                f"Markup {rounded_markup}% is above maximum {max_factor_record.markup_percentage}%, using maximum factor {max_factor_record.commission_factor}"
            )
            return max_factor_record.commission_factor

        # If markup is within range but no exact match found
        _logger.warning(
            f"No commission factor found for markup {rounded_markup}% (within configured range)"
        )
        return 0.0
