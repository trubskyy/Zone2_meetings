from datetime import date

from app.live import MAX_GAP_S, LiveParticipant
from app.zones import tanaka_max_hr, zone_profile


def test_tanaka():
    assert tanaka_max_hr(40) == 180


def test_karvonen_defaults():
    # age 40 -> max 180, rest 60 -> reserve 120; zone 2 = 60%..70% HRR = 132..143
    p = zone_profile(birth_year=1986, resting_hr=60, today=date(2026, 6, 1))
    assert p.max_hr == 180
    assert p.zone2 == (132, 143)
    assert p.estimated  # max HR came from the age formula
    assert p.classify(100) == 1
    assert p.classify(135) == 2
    assert p.classify(150) == 3
    assert p.classify(179) == 5


def test_measured_zone2_override_keeps_ladder_monotonic():
    p = zone_profile(resting_hr=50, max_hr=190, zone2_low=125, zone2_high=160)
    assert p.zone2 == (125, 160)
    assert list(p.floors) == sorted(p.floors)
    assert len(set(p.floors)) == 5
    assert p.classify(160) == 2
    assert p.classify(161) == 3
    assert not p.estimated


def test_live_participant_accrues_zone2_time_and_caps_gaps():
    prof = zone_profile(resting_hr=60, max_hr=180)  # zone 2 = 132..143
    lp = LiveParticipant(user_id=1, name="A", profile=prof, share_bpm=False)
    lp.record(bpm=135, now=0)
    lp.record(bpm=136, now=10)  # 10 s in zone 2
    lp.record(bpm=150, now=15)  # 5 s in zone 2 (credited to previous reading)
    lp.record(bpm=135, now=20)  # 5 s in zone 3
    lp.record(effort="conversational", now=1000)  # long gap: only MAX_GAP_S credited (to zone 2)
    assert lp.zone2_s == 15 + MAX_GAP_S
    assert lp.tracked_s == 20 + MAX_GAP_S
    assert lp.public_state()["bpm"] is None  # not shared by default
    assert lp.public_state()["zone"] == 2
