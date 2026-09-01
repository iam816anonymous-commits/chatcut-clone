"""Canonical TimelineTime abstraction using integer microseconds."""

import math
from typing import Self


class TimelineTime:
    """Canonical internal time representation backed strictly by 64-bit integer microseconds.

    1 second = 1,000,000 microseconds.
    """

    MICROSECONDS_PER_SECOND = 1_000_000

    __slots__ = ("_us",)

    def __init__(self, microseconds: int = 0) -> None:
        if not isinstance(microseconds, int):
            raise TypeError(f"Microseconds must be an integer, got {type(microseconds).__name__}")
        self._us = microseconds

    @property
    def microseconds(self) -> int:
        return self._us

    @property
    def seconds(self) -> float:
        return self._us / self.MICROSECONDS_PER_SECOND

    @classmethod
    def from_seconds(cls, seconds: float | int) -> Self:
        """Construct TimelineTime from floating point or integer seconds."""
        if not isinstance(seconds, (int, float)):
            raise TypeError(f"Seconds must be int or float, got {type(seconds).__name__}")
        us = round(seconds * cls.MICROSECONDS_PER_SECOND)
        return cls(us)

    @classmethod
    def from_frames(cls, frame_index: int, fps: float) -> Self:
        """Construct TimelineTime from frame index and frame rate."""
        if fps <= 0:
            raise ValueError(f"FPS must be positive, got {fps}")
        us = round((frame_index / fps) * cls.MICROSECONDS_PER_SECOND)
        return cls(us)

    def to_frame_index(self, fps: float) -> int:
        """Convert microsecond time to discrete frame index."""
        if fps <= 0:
            raise ValueError(f"FPS must be positive, got {fps}")
        return math.floor((self._us / self.MICROSECONDS_PER_SECOND) * fps)

    def __repr__(self) -> str:
        return f"TimelineTime({self._us}us, {self.seconds:.3f}s)"

    def __eq__(self, other: object) -> bool:
        if isinstance(other, TimelineTime):
            return self._us == other._us
        if isinstance(other, int):
            return self._us == other
        return False

    def __lt__(self, other: object) -> bool:
        if isinstance(other, TimelineTime):
            return self._us < other._us
        if isinstance(other, int):
            return self._us < other
        raise TypeError(f"Cannot compare TimelineTime with {type(other).__name__}")

    def __le__(self, other: object) -> bool:
        return self < other or self == other

    def __gt__(self, other: object) -> bool:
        return not (self <= other)

    def __ge__(self, other: object) -> bool:
        return not (self < other)

    def __add__(self, other: object) -> "TimelineTime":
        if isinstance(other, TimelineTime):
            return TimelineTime(self._us + other._us)
        if isinstance(other, int):
            return TimelineTime(self._us + other)
        raise TypeError(f"Cannot add {type(other).__name__} to TimelineTime")

    def __sub__(self, other: object) -> "TimelineTime":
        if isinstance(other, TimelineTime):
            return TimelineTime(self._us - other._us)
        if isinstance(other, int):
            return TimelineTime(self._us - other)
        raise TypeError(f"Cannot subtract {type(other).__name__} from TimelineTime")

    def __hash__(self) -> int:
        return hash(self._us)
