"""Generate the improved 'Ingot A' mark geometry (fixed perpendicular roof)."""
import math, pathlib

A = -0.5368                       # dx/dy of the leg (outer edge: x = A*y + B)
M = -A                            # roof slope (perpendicular to leg)
B_OUT = 286.5
S = 92.0
B_IN = B_OUT + S*math.sqrt(1+A*A)
BASE = 452.0
BAR_L, BAR_R = 346.0, 438.0

def _roof_c_from_bar(BT):
    # roof passes through the bar top-left corner (BAR_L, BT)
    return BT - M*BAR_L

def _x_at(edge_B, c):
    return (A*c + edge_B)/(1 - A*M)

def leg_corners(c):
    xi = _x_at(B_IN, c); xo = _x_at(B_OUT, c)
    return (xo, M*xo+c), (xi, M*xi+c)

def build(apex_y=66.0, cross_top=290.0, cross_bot=382.0, cross_right=438.0, cap_h=None):
    # choose bar top so the roof apex sits at apex_y
    # apex on outer edge: y = M*x+c, x=(A*c+B_OUT)/(1-A*M)
    # solve for c with apex_y
    c = (apex_y*(1-A*M) - M*(B_OUT)) / (1 - A*M + M*A)  # from y=M*x+c, x=(Ac+B)/(1-AM)
    # simpler: iterate
    for _ in range(60):
        xo = _x_at(B_OUT, c); yo = M*xo + c
        c += (apex_y - yo)*0.5
    BT = M*BAR_L + c
    OT, IT = leg_corners(c)
    IB = (A*BASE+B_IN, BASE); OB = (A*BASE+B_OUT, BASE)
    def f(p): return f"{p[0]:.2f} {p[1]:.2f}"
    leg = f"M {f(OT)} L {f(IT)} L {f(IB)} L {f(OB)} Z"
    bar = f"M {BAR_L:.2f} {BT:.2f} L {BAR_R:.2f} {BT:.2f} L {BAR_R:.2f} {BASE:.2f} L {BAR_L:.2f} {BASE:.2f} Z"
    ctl=(A*cross_top+B_IN, cross_top); cbl=(A*cross_bot+B_IN, cross_bot)
    cross = f"M {f(ctl)} L {cross_right:.2f} {cross_top:.2f} L {cross_right:.2f} {cross_bot:.2f} L {f(cbl)} Z"
    cap=""
    if cap_h: cap=f"M {BAR_L:.2f} {BT:.2f} L {BAR_R:.2f} {BT:.2f} L {BAR_R:.2f} {BT+cap_h:.2f} L {BAR_L:.2f} {BT+cap_h:.2f} Z"
    return dict(leg=leg, cross=cross, bar=bar, cap=cap, OT=OT, IT=IT, IB=IB, OB=OB, BT=BT)

def svg(g, gold="#E8C766", cap_fill="#FBF3DA"):
    cap = f'<path d="{g["cap"]}" fill="{cap_fill}"/>' if g["cap"] else ""
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512" '
            f'role="img" aria-label="Astra Trading"><title>Astra Trading</title>'
            f'<path d="{g["leg"]}" fill="{gold}"/><path d="{g["cross"]}" fill="{gold}"/>'
            f'<path d="{g["bar"]}" fill="{gold}"/>{cap}</svg>')

if __name__=="__main__":
    for name,kw in {
        "v_a": dict(apex_y=66),
        "v_b": dict(apex_y=80),
        "v_c": dict(apex_y=66, cross_top=300, cross_bot=392),
    }.items():
        g=build(**kw); pathlib.Path(f"brand/build/_{name}.svg").write_text(svg(g))
        print(name, "apex", g["OT"], "BT", round(g["BT"],1), "IT", g["IT"])
