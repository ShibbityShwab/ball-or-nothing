"""Deterministic, seedable RNG.

The game's outcomes must be reproducible from a simulation number alone: the Stake
Math SDK re-runs a simulation from the same seed until it satisfies its pre-assigned
distribution criteria, and the RGS verifies books by regenerating them. Python's
`random` would work, but its Mersenne Twister is slow and its reproducibility is a
CPython implementation detail. SplitMix64 is 6 lines, fast, and stable forever.

Not for cryptographic use. Slot outcomes are pre-computed and audited, not secret.
"""

from __future__ import annotations

_MASK64 = (1 << 64) - 1
_GOLDEN_GAMMA = 0x9E3779B97F4A7C15


class SplitMix64:
    """A small, fast, fully deterministic 64-bit PRNG."""

    __slots__ = ("_state",)

    def __init__(self, seed: int) -> None:
        self._state = seed & _MASK64

    def next_u64(self) -> int:
        self._state = (self._state + _GOLDEN_GAMMA) & _MASK64
        z = self._state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _MASK64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _MASK64
        return z ^ (z >> 31)

    def random(self) -> float:
        """Uniform float in [0, 1). 53 bits of entropy, like IEEE doubles carry."""
        return (self.next_u64() >> 11) * (1.0 / (1 << 53))

    def weighted_choice(self, weights: dict) -> str:
        """Pick a key with probability proportional to its weight.

        Weights must be non-negative integers. Raises on an all-zero weight table so a
        misconfigured reel fails loudly instead of silently returning the first key.
        """
        total = 0
        for weight in weights.values():
            if weight < 0:
                raise ValueError(f"negative weight in {weights!r}")
            total += weight
        if total <= 0:
            raise ValueError(f"all weights are zero in {weights!r}")

        roll = self.next_u64() % total
        for key, weight in weights.items():
            if roll < weight:
                return key
            roll -= weight
        raise AssertionError("unreachable: weighted_choice escaped its own total")
