"""Source-level collision semantics for the four-bar assembly."""

COLLISION_EXCLUSION_COMPONENT_PAIRS = (
    ("ground", "crank"),
    ("ground", "rocker"),
    ("crank", "coupler"),
    ("coupler", "rocker"),
)
