"""Tokyo Stock Exchange daily price-limit (制限値幅) calculator.

Japanese cash equities have a hard daily price band centered on the
broker-supplied `当日基準値` (basis price). The band width follows a fixed
tier table maintained by the JPX (Tokyo Stock Exchange).

Reference: https://www.jpx.co.jp/equities/trading/domestic/03.html

Marketspeed2 RSS exposes the basis price via `=RssMarket(symbol, "当日基準値")`
but does NOT expose the band edges directly — they must be derived from the
table below. Output matches the limit pair Marketspeed2 shows in its
confirmation dialog.
"""

from __future__ import annotations

from typing import NamedTuple

# (upper_exclusive_basis_price, half_band) — sorted ascending by threshold.
# A basis_price < threshold is in this tier; band = ± half_band.
_TIERS: list[tuple[float, float]] = [
    (100,        30),
    (200,        50),
    (500,        80),
    (700,       100),
    (1_000,     150),
    (1_500,     300),
    (2_000,     400),
    (3_000,     500),
    (5_000,     700),
    (7_000,   1_000),
    (10_000,  1_500),
    (15_000,  3_000),
    (20_000,  4_000),
    (30_000,  5_000),
    (50_000,  7_000),
    (70_000, 10_000),
    (100_000, 15_000),
    (150_000, 30_000),
    (200_000, 40_000),
    (300_000, 50_000),
    (500_000, 70_000),
    (700_000, 100_000),
    (1_000_000, 150_000),
    (1_500_000, 300_000),
    (2_000_000, 400_000),
    (3_000_000, 500_000),
    (5_000_000, 700_000),
    (7_000_000, 1_000_000),
    (10_000_000, 1_500_000),
    (15_000_000, 3_000_000),
    (20_000_000, 4_000_000),
    (30_000_000, 5_000_000),
    (50_000_000, 7_000_000),
    # JPX extends further (up to 500M-yen basis); the 50M tier is the highest
    # we'll see for normal JP equities. Add more tiers if needed.
]


class PriceBand(NamedTuple):
    basis_price: float
    half_width: float
    upper: float
    lower: float


def band_for_basis_price(basis_price: float) -> PriceBand:
    """Return the daily price band for a given basis price.

    Raises ``ValueError`` for non-positive input.
    """
    if basis_price <= 0:
        raise ValueError(f"basis_price must be positive, got {basis_price!r}")
    half = _TIERS[-1][1]
    for threshold, hw in _TIERS:
        if basis_price < threshold:
            half = hw
            break
    return PriceBand(
        basis_price=float(basis_price),
        half_width=float(half),
        upper=float(basis_price) + float(half),
        lower=max(0.0, float(basis_price) - float(half)),
    )
