"""Astra Trading 'Ingot A' — improved mark geometry generator.

Geometry is derived, not eyeballed:
  * one stroke weight S for both legs and the bullion bar
  * the roof is a chamfer perpendicular to the leg axis
  * the crossbar (gauge tick) is weight-matched and overshoots symmetrically
  * the whole glyph is optically centred and carries equal clear space
"""
import math, pathlib, re

A = -0.5368                     # dx/dy of the leg  (outer edge: x = A*y + B_OUT)
M = -A                          # roof slope (perpendicular to the leg axis)
B_OUT = 286.5
S = 92.0                        # stroke weight
B_IN = B_OUT + S * math.sqrt(1 + A * A)
BASE = 452.0                    # shared baseline for both feet
BAR_L, BAR_R = 346.0, 438.0
VB = 512.0


def _x_at(edge_B, c):
    return (A * c + edge_B) / (1 - A * M)


def build(apex_y=66.0, cross_t=64.0, cross_cy=305.0, over=22.0, cap_h=64.0):
    # roof line through apex: solve c so the apex (on the outer edge) is at apex_y
    c = apex_y
    for _ in range(80):
        xo = _x_at(B_OUT, c)
        yo = M * xo + c
        c += (apex_y - yo) * 0.5
    BT = M * BAR_L + c                      # bar top follows the roof
    OT = (_x_at(B_OUT, c), None); OT = (OT[0], M * OT[0] + c)
    IT = (_x_at(B_IN, c), None);  IT = (IT[0], M * IT[0] + c)
    IB = (A * BASE + B_IN, BASE)
    OB = (A * BASE + B_OUT, BASE)

    leg = [OT, IT, IB, OB]
    bar = [(BAR_L, BT), (BAR_R, BT), (BAR_R, BASE), (BAR_L, BASE)]
    ct, cb = cross_cy - cross_t / 2, cross_cy + cross_t / 2
    cross = [(A * ct + B_OUT - over, ct), (BAR_R + over, ct),
             (BAR_R + over, cb), (A * cb + B_OUT - over, cb)]
    cap = [(BAR_L, BT), (BAR_R, BT), (BAR_R, BT + cap_h), (BAR_L, BT + cap_h)] if cap_h else []
    return dict(leg=leg, cross=cross, bar=bar, cap=cap)


def _pts(shapes):
    return [p for s in shapes.values() for p in s]


def _bbox(shapes):
    xs = [p[0] for p in _pts(shapes)]; ys = [p[1] for p in _pts(shapes)]
    return min(xs), min(ys), max(xs), max(ys)


def _path(pts):
    return "M " + " L ".join(f"{x:.2f} {y:.2f}" for x, y in pts) + " Z"


def svg(shapes, gold="#E8C766", cap_fill="#FBF3DA", center=True, pad=0.0):
    dx = dy = 0.0
    if center:
        x0, y0, x1, y1 = _bbox(shapes)
        w, h = x1 - x0, y1 - y0
        dx = (VB - w) / 2 - x0
        dy = (VB - h) / 2 - y0
    g = f'<g transform="translate({dx:.2f} {dy:.2f})">' if (dx or dy) else "<g>"
    body = (f'<path d="{_path(shapes["leg"])}" fill="{gold}"/>'
            f'<path d="{_path(shapes["cross"])}" fill="{gold}"/>'
            f'<path d="{_path(shapes["bar"])}" fill="{gold}"/>')
    if shapes["cap"]:
        body += f'<path d="{_path(shapes["cap"])}" fill="{cap_fill}"/>'
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" '
            f'role="img" aria-label="Astra Trading"><title>Astra Trading</title>{g}{body}</g></svg>')


def report(shapes):
    x0, y0, x1, y1 = _bbox(shapes)
    print(f"  ink {x1-x0:.1f} x {y1-y0:.1f}  margins L{x0:.1f} R{512-x1:.1f} T{y0:.1f} B{512-y1:.1f}")


if __name__ == "__main__":
    variants = {
        "w1_over":  dict(cross_t=64, cross_cy=305, over=22, cap_h=64),
        "w2_flush": dict(cross_t=64, cross_cy=305, over=0,  cap_h=64),
        "w3_nocap": dict(cross_t=64, cross_cy=305, over=22, cap_h=0),
        "w4_thin":  dict(cross_t=52, cross_cy=305, over=22, cap_h=46),
    }
    for n, kw in variants.items():
        sh = build(**kw)
        pathlib.Path(f"brand/build/_{n}.svg").write_text(svg(sh))
        print(n); report(sh)
