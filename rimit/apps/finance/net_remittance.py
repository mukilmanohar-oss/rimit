"""Net Remittance Model calculation helpers.

This module implements the platform-wide commission math:

Given:
  - total_fee (₹)
  - university_share_percent (% of total_fee)
  - sub_center_commission_percent (% of gross pool)

Where:
  university_share = total_fee * university_share_percent
  gross_pool      = total_fee - university_share
  sub_center_commission = gross_pool * sub_center_commission_percent
  rimit_commission      = gross_pool - sub_center_commission
  net_payable           = total_fee - sub_center_commission

Invariant:
  net_payable == university_share + rimit_commission

All monetary outputs are rounded to 2 decimal places.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP


TWOPLACES = Decimal('0.01')
HUNDRED = Decimal('100')


def _to_decimal(v) -> Decimal:
    if isinstance(v, Decimal):
        return v
    # str() preserves ints/floats reasonably for our test/dev usage.
    return Decimal(str(v))


def _q(amount: Decimal) -> Decimal:
    return amount.quantize(TWOPLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class NetRemittanceBreakdown:
    total_fee: Decimal
    university_share_percent: Decimal
    university_share: Decimal
    gross_pool: Decimal
    sub_center_commission_percent: Decimal
    sub_center_commission: Decimal
    rimit_commission: Decimal
    net_payable: Decimal


class NetRemittanceError(ValueError):
    """Raised when invalid parameters lead to an impossible payout split."""


def calculate_net_remittance(
    *,
    total_fee,
    university_share_percent,
    sub_center_commission_percent,
) -> NetRemittanceBreakdown:
    """Compute the Net Remittance breakdown with strict validation."""

    total_fee_d = _q(_to_decimal(total_fee))
    uni_pct = _to_decimal(university_share_percent)
    sc_pct = _to_decimal(sub_center_commission_percent)

    if total_fee_d < 0:
        raise NetRemittanceError('total_fee must be >= 0')
    if uni_pct < 0 or uni_pct > 100:
        raise NetRemittanceError('university_share_percent must be between 0 and 100')
    if sc_pct < 0 or sc_pct > 100:
        raise NetRemittanceError('sub_center_commission_percent must be between 0 and 100')

    university_share = _q((total_fee_d * uni_pct) / HUNDRED)
    gross_pool = _q(total_fee_d - university_share)
    if gross_pool < 0:
        # Can happen only with extreme rounding edge-cases; still protect.
        raise NetRemittanceError('gross_pool is negative; check university_share_percent')

    sub_center_commission = _q((gross_pool * sc_pct) / HUNDRED)
    if sub_center_commission < 0:
        raise NetRemittanceError('sub_center_commission is negative; check sub_center_commission_percent')

    rimit_commission = _q(gross_pool - sub_center_commission)
    if rimit_commission < 0:
        raise NetRemittanceError('rimit_commission is negative; sub_center_commission_percent too high')

    net_payable = _q(total_fee_d - sub_center_commission)

    # Final invariant check (should always hold with the above arithmetic).
    if net_payable != _q(university_share + rimit_commission):
        raise NetRemittanceError('Invariant failed: net_payable != university_share + rimit_commission')

    return NetRemittanceBreakdown(
        total_fee=total_fee_d,
        university_share_percent=uni_pct,
        university_share=university_share,
        gross_pool=gross_pool,
        sub_center_commission_percent=sc_pct,
        sub_center_commission=sub_center_commission,
        rimit_commission=rimit_commission,
        net_payable=net_payable,
    )
