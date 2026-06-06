"""Log Mean Divisia Index (LMDI) primitives.

LMDI is the standard, exact method for additively decomposing the change in a
quantity that is a product of factors. For a target ``C = x_1 * x_2 * ... * x_n``
the change between a start and end period is split as::

    delta_C = sum_i  L(C_end, C_start) * ln(x_i_end / x_i_start)

where ``L`` is the logarithmic mean. The factor contributions sum *exactly* to
``delta_C`` (up to floating-point error), which makes the decomposition
auditable -- a core principle of this project.

This module is intentionally free of pandas so the maths can be unit-tested in
isolation.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field


def logarithmic_mean(a: float, b: float) -> float:
    """Return the logarithmic mean of two positive numbers.

    ``L(a, b) = (a - b) / (ln a - ln b)`` with ``L(a, a) = a``. Non-positive
    inputs return ``0.0`` so callers degrade gracefully on missing/zero data.
    """
    if a <= 0.0 or b <= 0.0:
        return 0.0
    if a == b:
        return a
    return (a - b) / (math.log(a) - math.log(b))


def log_ratio(numerator: float, denominator: float) -> float:
    """Return ``ln(numerator / denominator)`` or ``0.0`` if either is non-positive."""
    if numerator <= 0.0 or denominator <= 0.0:
        return 0.0
    return math.log(numerator / denominator)


@dataclass(frozen=True)
class Decomposition:
    """An additive decomposition of the change in one target quantity."""

    country: str
    start_year: int
    end_year: int
    target: str
    start_value: float
    end_value: float
    contributions: dict[str, float] = field(default_factory=dict)

    @property
    def delta(self) -> float:
        """Total change in the target between the two years."""
        return self.end_value - self.start_value

    @property
    def residual(self) -> float:
        """Difference between the actual change and the summed contributions.

        For an exact LMDI decomposition this is ~0 (floating-point error only).
        """
        return self.delta - sum(self.contributions.values())
