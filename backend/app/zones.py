"""Personal heart-rate zones.

Defaults use the Karvonen method (percent of heart-rate reserve) with a Tanaka max-HR estimate
(208 - 0.7 x age). A user's measured Zone 2 bounds (lab/field test) override the estimate.
These are training estimates, not medical advice.
"""

from dataclasses import dataclass
from datetime import date

DEFAULT_RESTING_HR = 60
DEFAULT_AGE = 35

# Lower bound of each zone as a fraction of heart-rate reserve.
_HRR_FLOORS = {1: 0.50, 2: 0.60, 3: 0.70, 4: 0.80, 5: 0.90}

# Self-reported effort (talk test) -> zone. Used when no sensor is connected.
EFFORT_ZONES = {
    "easy": 1,  # could sing
    "conversational": 2,  # full sentences, can't sing — the talk test for Zone 2
    "short_sentences": 3,
    "breathless": 4,
}


def tanaka_max_hr(age: int) -> int:
    return round(208 - 0.7 * age)


@dataclass(frozen=True)
class ZoneProfile:
    resting_hr: int
    max_hr: int
    # Lower BPM bound for zones 1..5 (index 0 = zone 1).
    floors: tuple[int, int, int, int, int]
    estimated: bool

    @property
    def zone2(self) -> tuple[int, int]:
        return self.floors[1], self.floors[2] - 1

    def classify(self, bpm: int) -> int:
        """Return zone 1..5. Anything below the zone-1 floor counts as zone 1."""
        zone = 1
        for i, floor in enumerate(self.floors):
            if bpm >= floor:
                zone = i + 1
        return zone

    def as_dict(self) -> dict:
        bounds = []
        for i, low in enumerate(self.floors):
            high = self.floors[i + 1] - 1 if i < 4 else self.max_hr
            bounds.append({"zone": i + 1, "low": low, "high": high})
        return {
            "resting_hr": self.resting_hr,
            "max_hr": self.max_hr,
            "estimated": self.estimated,
            "zones": bounds,
        }


def zone_profile(
    *,
    birth_year: int | None = None,
    resting_hr: int | None = None,
    max_hr: int | None = None,
    zone2_low: int | None = None,
    zone2_high: int | None = None,
    today: date | None = None,
) -> ZoneProfile:
    today = today or date.today()
    estimated = max_hr is None or resting_hr is None
    rest = resting_hr or DEFAULT_RESTING_HR
    age = today.year - birth_year if birth_year else DEFAULT_AGE
    mx = max_hr or tanaka_max_hr(age)
    reserve = mx - rest
    floors = [round(rest + _HRR_FLOORS[z] * reserve) for z in range(1, 6)]

    if zone2_low and zone2_high and zone2_low < zone2_high:
        # Measured Zone 2 wins; keep higher zones above it so the ladder stays monotonic.
        floors[1] = zone2_low
        floors[2] = zone2_high + 1
        floors[0] = min(floors[0], zone2_low - 1)
        floors[3] = max(floors[3], floors[2] + 1)
        floors[4] = max(floors[4], floors[3] + 1)
        estimated = False

    return ZoneProfile(resting_hr=rest, max_hr=mx, floors=tuple(floors), estimated=estimated)


def profile_for_user(user) -> ZoneProfile:
    return zone_profile(
        birth_year=user.birth_year,
        resting_hr=user.resting_hr,
        max_hr=user.max_hr,
        zone2_low=user.zone2_low,
        zone2_high=user.zone2_high,
    )
