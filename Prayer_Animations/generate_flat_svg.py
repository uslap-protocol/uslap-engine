#!/usr/bin/env python3
"""
ONE leg gore, flat SVG. Anchored at lateral hip (XY intersection).
X = WEFT (horizontal). Y = WARP (vertical). Origin = lateral hip.
"""
import math, os

PI = math.pi
def lerp(a,b,t): return a+(b-a)*t

PROFILE = [
    (0.080,0.035,0.200,0.000),(0.150,0.040,0.200,0.000),(0.250,0.048,0.200,0.000),
    (0.350,0.055,0.200,0.000),(0.450,0.050,0.200,0.000),(0.500,0.055,0.200,0.000),
    (0.600,0.070,0.200,0.000),(0.700,0.080,0.200,0.008),(0.780,0.085,0.200,0.025),
    (0.830,0.090,0.195,0.060),(0.870,0.095,0.150,0.065),(0.910,0.100,0.100,0.055),
    (0.955,0.105,0.050,0.035),(1.000,0.100,0.000,0.015),(1.045,0.098,0.000,0.005),
    (1.085,0.100,0.000,0.000),(1.125,0.105,0.000,0.000),
]

def prof_at(y):
    if y<=PROFILE[0][0]: return PROFILE[0]
    if y>=PROFILE[-1][0]: return PROFILE[-1]
    for i in range(len(PROFILE)-1):
        y0,r0,s0,g0=PROFILE[i]; y1,r1,s1,g1=PROFILE[i+1]
        if y0<=y<=y1:
            t=(y-y0)/(y1-y0) if y1!=y0 else 0
            return(y,lerp(r0,r1,t),lerp(s0,s1,t),lerp(g0,g1,t))
    return PROFILE[-1]

def interp_kf(kf,t):
    if t<=kf[0][0]: return kf[0][1]
    if t>=kf[-1][0]: return kf[-1][1]
    for i in range(len(kf)-1):
        t0,a0=kf[i]; t1,a1=kf[i+1]
        if t0<=t<=t1: return lerp(a0,a1,(t-t0)/(t1-t0) if t1!=t0 else 0)
    return kf[-1][1]

def angle_to_x(deg,r,off):
    d=(270.0-deg)%360.0
    if d>270: d=270
    return off+r*1.5*PI*(d/270.0-0.5)

L1_KF=[(0,0),(.14,15),(.29,40),(.43,80),(.57,130),(.71,175),(.86,220),(.93,250),(1,270)]
L2_KF=[(0,0),(.06,15),(.14,40),(.23,80),(.34,130),(.49,170),(.57,195),(.71,220),(.86,250),(1,270)]
L3_KF=[(0,0),(.08,20),(.15,50),(.25,90),(.38,130),(.50,155),(.58,175),(.70,210),(.83,240),(.93,260),(1,270)]
L4_KF=[(0,0),(.04,15),(.10,40),(.18,70),(.28,105),(.38,135),(.48,160),(.55,175),(.62,195),(.72,210),(.82,215),(.92,218),(1,220)]
L5_KF=[(0,0),(.01,30),(.02,60),(.03,85),(.04,90),(.20,90),(.40,90),(.60,92),(.80,97),(.90,102),(1,105)]
S1_KF=[(0,0),(.05,10),(.12,22),(.22,36),(.35,46),(.50,53),(.65,58),(.78,61),(.90,63),(1,65)]
S2_KF=[(0,0),(.06,6),(.15,12),(.28,15),(.42,12),(.56,3),(.68,-15),(.78,-35),(.88,-60),(1,-90)]
SEAM_KF=[(0,270),(1,270)]
# T11 and T12: horizontal bands wrapping around the trunk
T11_LINE_KF=[(0,0),(0.25,90),(0.50,180),(0.75,270),(1.0,270)]  # wraps to seam
T12_LINE_KF=[(0,0),(0.25,90),(0.50,180),(0.75,270),(1.0,270)]

T11_Y=1.125; BB_Y=1.085; PB_Y=0.830
HIP_Y=0.850  # lateral hip / greater trochanter height
HIP_ANGLE=90  # lateral

DERMATOMES = [
    dict(label='T11',color='#999999', sy=1.125, bot=1.100, kf=T11_LINE_KF, lw=1.5),
    dict(label='T12',color='#777777', sy=1.085, bot=1.060, kf=T12_LINE_KF, lw=1.5),
    dict(label='L1', color='#88bbee', sy=1.045, bot=0.830, kf=L1_KF, lw=2),  # bot=PB
    dict(label='L2', color='#6699dd', sy=1.000, bot=0.55, kf=L2_KF, lw=2),
    dict(label='L3', color='#dd5555', sy=0.955, bot=0.48, kf=L3_KF, lw=2),
    dict(label='L4', color='#ddcc22', sy=0.910, bot=0.08, kf=L4_KF, lw=2),
    dict(label='L5', color='#00ee00', sy=0.870, bot=0.08, kf=L5_KF, lw=3.5, is_warp=True),
    dict(label='S1', color='#ee7788', sy=0.830, bot=0.08, kf=S1_KF, lw=2),
    dict(label='S2', color='#4466cc', sy=0.800, bot=0.48, kf=S2_KF, lw=2),
    dict(label='SEAM',color='#ee2222',sy=0.870, bot=0.04, kf=SEAM_KF, lw=1.5),
]

VERTS_LIST = [
    ('T11',1.125),('T12',1.085),('L1',1.045),('L2',1.000),('L3',0.955),
    ('L4',0.910),('L5',0.870),('S1',0.830),('S2',0.800),('S3',0.780),
    ('S4',0.765),('S5',0.755),('Co',0.745),
]

def top_edge_y(deg):
    a=deg%360
    if a<=180: return lerp(T11_Y,BB_Y,(a/180)**2)
    elif a<=270: return lerp(BB_Y,PB_Y,(a-180)/90)
    else: return lerp(PB_Y,T11_Y,((a-270)/90)**2)


def generate_svg(path):
    # No splay for single leg — just the offset for the 270° strip
    MR = 0.105

    def off(y):
        return 0.75 * PI * MR  # no gap, no splay — single leg

    def fx(deg, y):
        _, r, _, g = prof_at(y)
        # Glute adds significantly to posterior circumference
        # Factor 0.8 (was 0.3) so hip/glute IS the widest level
        er = r + g * max(0, math.cos(deg * PI / 180)) ** 2 * 0.8
        return angle_to_x(deg, er, off(y))

    # Lateral hip position (the anchor point)
    HIP_X = fx(HIP_ANGLE, HIP_Y)

    # All coordinates relative to hip
    def cx(body_x):
        return body_x - HIP_X

    def cy(body_y):
        return body_y - HIP_Y

    # SVG scaling
    SCALE = 1800  # px per meter
    # Compute bounds
    pts = []
    for yi in range(16, int(T11_Y * 200) + 2, 4):
        y = yi / 200.0
        for di in range(0, 361, 10):
            if y > top_edge_y(di) + 0.001: continue
            pts.append((cx(fx(di, y)), cy(y)))

    min_x = min(p[0] for p in pts) - 0.03
    max_x = max(p[0] for p in pts) + 0.03
    min_y = min(p[1] for p in pts) - 0.08
    max_y = max(p[1] for p in pts) + 0.03

    W = int((max_x - min_x) * SCALE) + 100
    H = int((max_y - min_y) * SCALE) + 100
    OX = 50 - int(min_x * SCALE)  # SVG origin for body (0,0) = hip
    OY = 50 + int(max_y * SCALE)

    def s(bx, by):
        """Body coords (centered on hip) → SVG coords."""
        return OX + bx * SCALE, OY - by * SCALE

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
    svg.append(f'<rect width="{W}" height="{H}" fill="#1a1a2e"/>')

    # ── Find where L5 is at the lateral hip level ──
    # L5 IS the Y axis. Find L5's position at hip height.
    # Walk L5 and find the point closest to hip height.
    l5_at_hip_x = None
    l5_at_hip_y_body = None
    best_dy = 1e9
    for st in range(301):
        t = st / 300.0
        y = lerp(0.870, 0.08, t)
        if abs(y - HIP_Y) < best_dy:
            best_dy = abs(y - HIP_Y)
            a = interp_kf(L5_KF, t) % 360
            l5_at_hip_x = cx(fx(a, y))
            l5_at_hip_y_body = cy(y)

    # ── X AXIS (WEFT) — horizontal through L5 at hip level ──
    x1, y1 = s(min_x, l5_at_hip_y_body)
    x2, y2 = s(max_x, l5_at_hip_y_body)
    svg.append(f'<line x1="{x1:.0f}" y1="{y1:.0f}" x2="{x2:.0f}" y2="{y2:.0f}" stroke="#ffffff" stroke-width="1.5" stroke-dasharray="8,4"/>')
    svg.append(f'<text x="{x2-30}" y="{y2-8}" fill="#ffffff" font-size="14" font-family="monospace" font-weight="bold">X (WEFT)</text>')

    # ── Y AXIS = L5 itself (no separate line — L5 IS the Y axis) ──
    # L5 is drawn later with the dermatome lines. Just label it.

    # ── ORIGIN MARKER — where X crosses L5 ──
    ox, oy = s(l5_at_hip_x, l5_at_hip_y_body)
    svg.append(f'<circle cx="{ox:.0f}" cy="{oy:.0f}" r="8" fill="none" stroke="#ffffff" stroke-width="2.5"/>')
    svg.append(f'<line x1="{ox-14:.0f}" y1="{oy:.0f}" x2="{ox+14:.0f}" y2="{oy:.0f}" stroke="#ffffff" stroke-width="2"/>')
    svg.append(f'<text x="{ox+15}" y="{oy-12}" fill="#ffffff" font-size="12" font-family="monospace">LATERAL HIP</text>')
    svg.append(f'<text x="{ox+15}" y="{oy+2}" fill="#888888" font-size="10" font-family="monospace">Y=L5 | X=WEFT</text>')

    # ── GORE OUTLINE (filled) ──
    outline_pts = []
    # Top edge
    for i in range(129):
        deg = 360.0 * i / 128
        y = top_edge_y(deg)
        outline_pts.append(s(cx(fx(deg, y)), cy(y)))
    # Right edge down to ankle
    for yi in range(int(top_edge_y(0)*200), 15, -2):
        y = yi / 200.0
        if y > top_edge_y(0): continue
        outline_pts.append(s(cx(fx(0, y)), cy(y)))
    # Bottom across
    for i in range(128, -1, -1):
        deg = 360.0 * i / 128
        y = 0.08
        if y > top_edge_y(deg) + 0.001: continue
        outline_pts.append(s(cx(fx(deg, y)), cy(y)))
    pts_str = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in outline_pts)
    svg.append(f'<polygon points="{pts_str}" fill="#c4a878" stroke="#aa8855" stroke-width="1" opacity="0.6"/>')

    # ── VERTEBRAE along spine edge (0°) ──
    spine_pts = []
    for vn, vy in VERTS_LIST:
        sx, sy = s(cx(fx(0, vy)), cy(vy))
        spine_pts.append((sx, sy, vn))
    line_str = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in spine_pts)
    svg.append(f'<polyline points="{line_str}" fill="none" stroke="#00bb00" stroke-width="1.5"/>')
    for sx, sy, vn in spine_pts:
        svg.append(f'<polygon points="{sx-4},{sy} {sx},{sy-4} {sx+4},{sy} {sx},{sy+4}" fill="#00bb00"/>')
        svg.append(f'<text x="{sx+6}" y="{sy+3}" font-size="9" fill="#00bb00" font-family="monospace">{vn}</text>')

    # ── LANDMARKS ──
    for label, deg, y, color in [('T11',0,T11_Y,'#ff4444'), ('BB',180,BB_Y,'#ff8800'), ('PB',270,PB_Y,'#cc00cc')]:
        sx, sy = s(cx(fx(deg, y)), cy(y))
        svg.append(f'<circle cx="{sx:.0f}" cy="{sy:.0f}" r="6" fill="{color}"/>')
        svg.append(f'<text x="{sx+10}" y="{sy+4}" font-size="12" fill="{color}" font-family="monospace" font-weight="bold">{label}</text>')

    # ── TOP EDGE LINE ──
    te_pts = []
    for i in range(129):
        deg = 360.0 * i / 128
        y = top_edge_y(deg)
        te_pts.append(s(cx(fx(deg, y)), cy(y)))
    svg.append(f'<polyline points="{" ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in te_pts)}" fill="none" stroke="#cccc00" stroke-width="1.5"/>')

    # ── DERMATOME LINES ──
    # L5 is STRAIGHT from lateral hip to foot centre — it IS the Y axis
    MJ = 0.15
    for d in DERMATOMES:
        if d.get('is_warp'):
            # L5: CURVES from spine (0°) down to lateral hip,
            # then STRAIGHT from lateral hip to centre of plantar.
            #
            # Upper part (spine to hip): use keyframes, curves
            upper_pts = []
            for st in range(101):
                t = st / 100.0
                y = lerp(d['sy'], d['bot'], t)
                if y < HIP_Y: break  # stop at hip
                a = interp_kf(d['kf'], t) % 360
                upper_pts.append(s(cx(fx(a, y)), cy(y)))
            if upper_pts:
                pts_str = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in upper_pts)
                svg.append(f'<polyline points="{pts_str}" fill="none" stroke="{d["color"]}" stroke-width="{d["lw"]}" stroke-linecap="round"/>')

            # Lower part (hip to foot): STRAIGHT LINE
            sx1, sy1 = s(l5_at_hip_x, l5_at_hip_y_body)
            foot_center_x = cx(fx(180, 0.08 - 0.11))
            foot_center_y = cy(0.08 - 0.11)
            sx2, sy2 = s(foot_center_x, foot_center_y)
            svg.append(f'<line x1="{sx1:.0f}" y1="{sy1:.0f}" x2="{sx2:.0f}" y2="{sy2:.0f}" stroke="{d["color"]}" stroke-width="{d["lw"]}" stroke-linecap="round"/>')

            svg.append(f'<text x="{sx1+10}" y="{sy1-8}" font-size="13" fill="{d["color"]}" font-family="monospace" font-weight="bold">L5 = Y (WARP)</text>')
            continue

        segs = [[]]
        px = None
        for st in range(301):
            t = st / 300.0
            y = lerp(d['sy'], d['bot'], t)
            a = interp_kf(d['kf'], t) % 360
            x = cx(fx(a, y))
            yy = cy(y)
            if px is not None and abs(x - px) > MJ:
                segs.append([])
            segs[-1].append(s(x, yy))
            px = x

        for seg in segs:
            if len(seg) < 2: continue
            pts_str = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in seg)
            svg.append(f'<polyline points="{pts_str}" fill="none" stroke="{d["color"]}" stroke-width="{d["lw"]}" stroke-linecap="round"/>')

        # Label near start
        if segs[0]:
            lx, ly = segs[0][0]
            svg.append(f'<text x="{lx+5}" y="{ly-5}" font-size="11" fill="{d["color"]}" font-family="monospace" font-weight="bold">{d["label"]}</text>')

    # ── ANGLE MARKERS on X axis ──
    for deg in [0, 45, 90, 135, 180, 225, 270]:
        _, r, _, g = prof_at(HIP_Y)
        er = r + g * max(0, math.cos(deg * PI / 180)) ** 2 * 0.3
        x_body = cx(angle_to_x(deg, er, off(HIP_Y)))
        sx, sy = s(x_body, 0)
        svg.append(f'<line x1="{sx:.0f}" y1="{sy-6:.0f}" x2="{sx:.0f}" y2="{sy+6:.0f}" stroke="#888888" stroke-width="1"/>')
        label_map = {0:'0°\nSpine', 90:'90°\nLateral', 180:'180°\nAnterior', 270:'270°\nSeam'}
        if deg in label_map:
            lines = label_map[deg].split('\n')
            svg.append(f'<text x="{sx}" y="{sy+20}" text-anchor="middle" font-size="9" fill="#888888" font-family="monospace">{lines[0]}</text>')
            if len(lines)>1:
                svg.append(f'<text x="{sx}" y="{sy+31}" text-anchor="middle" font-size="8" fill="#666666" font-family="monospace">{lines[1]}</text>')

    # ── LEGEND ──
    ly = H - 20
    for d in reversed(DERMATOMES):
        svg.append(f'<rect x="{W-130}" y="{ly-8}" width="15" height="3" fill="{d["color"]}"/>')
        svg.append(f'<text x="{W-110}" y="{ly-3}" font-size="10" fill="{d["color"]}" font-family="monospace">{d["label"]}</text>')
        ly -= 16

    # ── TITLE ──
    svg.append(f'<text x="{W//2}" y="22" text-anchor="middle" font-size="15" fill="#ffffff" font-family="monospace">RIGHT LEG — Anchored at Lateral Hip</text>')
    svg.append(f'<text x="{W//2}" y="38" text-anchor="middle" font-size="10" fill="#888888" font-family="monospace">X=WEFT (horizontal) | Y=WARP (vertical) | Origin=Lateral Hip (90°)</text>')

    svg.append('</svg>')

    with open(path, 'w') as f:
        f.write('\n'.join(svg))
    print(f"✓ {path}\n  {W}x{H}px\n  Open in browser")


if __name__ == '__main__':
    generate_svg(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dermatome_one_leg.svg'))
