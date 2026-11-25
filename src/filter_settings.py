"""v2 filtering settings, shared by ex_filtering.py and the Filtering tab.
No heavy imports here, so the UI can read these values without loading pandas/scipy at startup."""

SWING_SPEED_DEFAULT = 0.1    # m/s; paw speed above this = swing. 0 keeps every frame (stance included)
# Per-experiment defaults, from v2 (Savitzky-Golay) paw speed histograms on 15 SCA2-Q129 sessions per test:
# groundwalk/gridwalk speeds are bimodal (jitter ~0.02, swing ~0.5-0.6) with the valley at 0.08-0.126 -> 0.1.
# beamwalk has one broad peak (~0.06-0.1, slow gripping/sliding), no valley -> 0.03 only removes jitter.
# swimming not measured -> SWING_SPEED_DEFAULT.
SWING_SPEED_BY_EXPERIMENT = {"groundwalk": 0.1, "gridwalk": 0.1, "beamwalk": 0.03}
# Per species ("0" = Mus, "1" = Acomys). Acomys values are PROVISIONAL (same as Mus): resting Acomys paws jitter
# more (~0.05 m/s vs ~0.02) and swing is faster (0.5-1.3 m/s), so 0.15-0.2 may suit them better once more
# Acomys sessions have been tested (only 9 groundwalk sessions so far).
SWING_SPEED_BY_SPECIES = {"0": SWING_SPEED_BY_EXPERIMENT,
                          "1": {"groundwalk": 0.1, "gridwalk": 0.1, "beamwalk": 0.03}}
FLOOR_PCT = 10               # floor = 10th percentile of left hind toe Y (90th in the upside-down right view)
FROZEN_MIN_REPEATS = 1       # a marker whose X and Y repeat EXACTLY for this many frames is a tracker placeholder
                             # (real smoothed positions always change a little, even on a resting paw)
# Implausible-position checks (v2). Real paw moves in a clean session: <= ~18 mm/frame; tracking jumps: 40-65 mm.
NOSE_EXIT_TOL = 0.001        # m; the window ends at the first frame the nose is this close to its exit (final) X...
NOSE_HOLD_FRAMES = 5         # ...or at the first frame the nose freezes for this many frames (stopped being tracked)
NOSE_EXIT_ZONE = 0.02        # m; ...but only a freeze this close to the exit counts (mid-walk freezes, e.g. the nose
                             # hidden by the beam, are placeholders, not the end of the trial)
MAX_JUMP_M = 0.03            # m per frame (3 m/s at 100 fps); a measured marker moving more than this = tracking jump
MAX_JUMP_BY_SPECIES = {"0": 0.03,   # Mus: real paw moves <= ~25 mm/frame; fake jumps from ~25-40 mm
                       "1": 0.04}   # Acomys: faster, real smooth swings reach ~31 mm/frame
START_MOVE_TOL = 0.005       # m; the start marker must move this far from its first value to count as appearing
                             # (a parked placeholder can drift by ~1 mm before the animal enters, e.g. Acomys clips)
HIND_AHEAD_TOL = 0.01        # m; hind paw more than this ahead of the front paw on the same side = label swap
BODY_LENGTH_RANGE = (0.7, 1.3)  # nose-tail base distance allowed, as a fraction of the session median
MAX_BAD_FRACTION = 0.2       # more of the window than this failing the body checks = nose track broken: warn
SPIKE_MAX_M = 0.008          # m; a marker that jumps out and straight back by more than this in one frame = jitter
                             # (805-file test: footprint never exceeds ~6 mm; beam jitter reaches 20 mm)
MIN_TRACKED_PCT = 70         # warn when fewer than this % of the window frames have all four paws tracked
HEIGHT_CUTOFF_X = -0.020     # m; heights are blanked once the right hind toe X reaches this (same for old and new camera)


def default_swing_speed(animal_choice, experiment):
    """Default swing speed threshold (m/s) for a species ("0" Mus, "1" Acomys) and test."""
    table = SWING_SPEED_BY_SPECIES.get(str(animal_choice), SWING_SPEED_BY_EXPERIMENT)
    return table.get(experiment, SWING_SPEED_DEFAULT)


def max_jump(animal_choice):
    return MAX_JUMP_BY_SPECIES.get(str(animal_choice), MAX_JUMP_M)


def mm(m):
    return f"{m * 1000:g} mm"


def settings_rows(animal_choice="0"):
    """(group, setting, value, meaning) for every fixed v2 setting, as shown in the Filtering and Tutorial tabs."""
    lo, hi = BODY_LENGTH_RANGE
    return [
        ("Movement window", "Start movement", mm(START_MOVE_TOL),
         "The start marker must move this far from its first position before the window starts."),
        ("Movement window", "Nose exit tolerance", mm(NOSE_EXIT_TOL),
         "The window ends at the first frame the nose is this close to its final (exit) X position."),
        ("Movement window", "Nose freeze", f"{NOSE_HOLD_FRAMES} frames",
         "The window also ends when the nose stops being tracked (frozen for this many frames) near the exit."),
        ("Movement window", "Nose exit zone", mm(NOSE_EXIT_ZONE),
         "A nose freeze counts as the end only within this distance of the exit; freezes mid-walk "
         "(e.g. nose hidden by the beam) are ignored."),
        ("Removed positions", "Placeholder", f"{FROZEN_MIN_REPEATS} repeat",
         "A marker whose X and Y repeat exactly is a tracker placeholder: that frame is removed."),
        ("Removed positions", "Max jump", f"{mm(max_jump(animal_choice))} / frame",
         "A marker moving more than this in one frame is a tracking jump: that marker, that frame is removed."),
        ("Removed positions", "Spike", mm(SPIKE_MAX_M),
         "A marker that jumps out and straight back by more than this is jitter: removed (tail excluded)."),
        ("Removed positions", "Hind ahead of front", mm(HIND_AHEAD_TOL),
         "Hind paw further than this ahead of the front paw (label swap): the whole frame is removed."),
        ("Removed positions", "Body length", f"{lo:g}-{hi:g} x median",
         "Nose to tail base outside this range of the session median: the whole frame is removed."),
        ("Floor", "Floor percentile", f"{FLOOR_PCT}th",
         "Auto floor = this percentile of the hind toe height (the resting toe level)."),
        ("Floor", "Height cutoff", f"X = {mm(HEIGHT_CUTOFF_X)}",
         "With the height cutoff on, heights are blanked once the right hind toe reaches this X position."),
        ("Warnings", "Body check failures", f"> {MAX_BAD_FRACTION:.0%}",
         "More of the window than this failing the body checks: 'CHECK THIS VIDEO' warning."),
        ("Warnings", "Tracked frames", f"< {MIN_TRACKED_PCT}%",
         "Fewer window frames than this with all four paws tracked: low tracking warning."),
    ]
