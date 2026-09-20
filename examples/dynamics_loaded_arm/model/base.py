"""360 × 220 × 16 base, real foundation and bracket fastener holes."""

from common import box, bore, finish


def build():
    # ---- feature: base-stock (build) ----
    body = box(-40, 320, -110, 110, 0, 16, chamfer=True)
    # ---- feature: foundation-holes (subtract) ----
    for x in (-25, 300):
        for y in (-85, 85):
            body = bore(body, 4.5, 18, (x, y, -1))
    # ---- feature: bracket-blind-taps (subtract) ----
    for sy in (-50, 50):
        for x in (-33, 33):
            for dy in (-18, 18):
                body = bore(body, 4.1, 13, (x, sy + dy, 4))
    for x in (-36, 50):
        for y in (-100, -84):
            body = bore(body, 3.1, 13, (x, y, 4))
    return finish(body)
