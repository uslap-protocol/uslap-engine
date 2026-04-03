#!/usr/bin/env python3
"""
خُطُوط ابن سينا — Ibn Sīnā's Lines
ONE leg, 11 خُطُوط (Co → L1), flat 2D SVG.

Two panels: STANDING | RUKŪʿ
Anchored at lateral hip (XY intersection).
L5 = WARP (straight from hip to plantar).
المِحْوَر الظَّهْرِي = the seam (stable conductor).

Source: Q23:14 فَكَسَوْنَا الْعِظَامَ لَحْمًا
Reference: 3 criminal maps cross-referenced.
"""
import math, os

PI = math.pi
def lerp(a, b, t): return a + (b - a) * t

PROFILE = [
    (0.080,0.035,0.200,0.000),(0.150,0.040,0.200,0.000),(0.250,0.048,0.200,0.000),
    (0.350,0.055,0.200,0.000),(0.450,0.050,0.200,0.000),(0.500,0.055,0.200,0.000),
    (0.600,0.070,0.200,0.000),(0.700,0.080,0.200,0.008),(0.780,0.085,0.200,0.025),
    (0.830,0.090,0.195,0.060),(0.870,0.095,0.150,0.065),(0.910,0.100,0.100,0.055),
    (0.955,0.105,0.050,0.035),(1.000,0.100,0.000,0.015),(1.045,0.098,0.000,0.005),
    (1.085,0.100,0.000,0.000),(1.125,0.105,0.000,0.000),
]

def prof_at(y):
    if y <= PROFILE[0][0]: return PROFILE[0]
    if y >= PROFILE[-1][0]: return PROFILE[-1]
    for i in range(len(PROFILE) - 1):
        y0, r0, s0, g0 = PROFILE[i]; y1, r1, s1, g1 = PROFILE[i + 1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0) if y1 != y0 else 0
            return (y, lerp(r0, r1, t), lerp(s0, s1, t), lerp(g0, g1, t))
    return PROFILE[-1]

def ikf(kf, t):
    if t <= kf[0][0]: return kf[0][1]
    if t >= kf[-1][0]: return kf[-1][1]
    for i in range(len(kf) - 1):
        t0, a0 = kf[i]; t1, a1 = kf[i + 1]
        if t0 <= t <= t1: return lerp(a0, a1, (t - t0) / (t1 - t0) if t1 != t0 else 0)
    return kf[-1][1]

def a2x(deg, r, off):
    d = (270.0 - deg) % 360.0
    if d > 270: d = 270
    return off + r * 1.5 * PI * (d / 270.0 - 0.5)

HIP_Y = 0.850
T11_Y = 1.125; BB_Y = 1.085; PB_Y = 0.830

def top_edge_y(deg):
    a = deg % 360
    if a <= 180: return lerp(T11_Y, BB_Y, (a / 180) ** 2)
    elif a <= 270: return lerp(BB_Y, PB_Y, (a - 180) / 90)
    else: return lerp(PB_Y, T11_Y, ((a - 270) / 90) ** 2)

# ═══════════════════════════════════════════
# 11 خُطُوط — from criminal maps, cross-referenced
# Each: (label, arabic, color, spine_y, bot_y, keyframes, line_width)
# Keyframes: (t, angle_degrees)
# Angles: 0°=posterior, 90°=lateral, 180°=anterior, 270°=seam
# ═══════════════════════════════════════════
KHUTUT = [
    # T11/T12 — trunk bands, terminate at 180° (anterior)
    ('T11', 'خَطّ ١١', '#aaaaaa', 1.125, 1.100,
     [(0,0),(.25,90),(.50,180),(1,180)], 1.5),
    ('T12', 'خَطّ ١٢', '#888888', 1.085, 1.060,
     [(0,0),(.25,90),(.50,180),(1,180)], 1.5),
    # L1 — groin/inguinal, ends at PB (seam)
    ('L1', 'خَطّ ل١', '#88bbee', 1.045, 0.830,
     [(0,0),(.14,15),(.29,40),(.43,80),(.57,130),(.71,175),(.86,220),(.93,250),(1,270)], 2),
    # L2 — anterior thigh, ends at seam
    ('L2', 'خَطّ ل٢', '#6699dd', 1.000, 0.55,
     [(0,0),(.06,15),(.14,40),(.23,80),(.34,130),(.49,170),(.57,195),(.71,220),(.86,250),(1,270)], 2),
    # L3 — anterior thigh to knee, ends at seam
    ('L3', 'خَطّ ل٣', '#dd5555', 0.955, 0.48,
     [(0,0),(.08,20),(.15,50),(.25,90),(.38,130),(.50,155),(.58,175),(.70,210),(.83,240),(.93,260),(1,270)], 2),
    # L4 — the crossover, big toe
    ('L4', 'خَطّ ل٤', '#ddcc22', 0.910, 0.08,
     [(0,0),(.04,15),(.10,40),(.18,70),(.28,105),(.38,135),(.48,160),(.55,175),(.62,195),(.72,210),(.82,215),(.92,218),(1,220)], 2),
    # L5 — THE WARP. Straight from lateral hip to plantar.
    ('L5', 'الخَطّ الخَامِس', '#00ee00', 0.870, 0.08,
     [(0,0),(.01,30),(.02,60),(.03,85),(.04,90),(.20,90),(.40,90),(.60,92),(.80,97),(.90,102),(1,105)], 3.5),
    # S1 — posterior-lateral, heel
    ('S1', 'خَطّ ع١', '#ee7788', 0.830, 0.08,
     [(0,0),(.05,10),(.12,22),(.22,36),(.35,46),(.50,53),(.65,58),(.78,61),(.90,63),(1,65)], 2),
    # S2 — posterior midline, back of knee
    ('S2', 'خَطّ ع٢', '#4466cc', 0.800, 0.48,
     [(0,0),(.06,6),(.15,12),(.28,15),(.42,12),(.56,3),(.68,-15),(.78,-35),(.88,-60),(1,-90)], 2),
    # S3 — perineal
    ('S3', 'خَطّ ع٣', '#9966aa', 0.780, 0.76,
     [(0,0),(.5,180),(1,360)], 1),
    # S4/S5 — perineal inner
    ('S4S5', 'خَطّ ع٤-٥', '#886699', 0.765, 0.75,
     [(0,0),(.5,180),(1,360)], 1),
    # SEAM — المِحْوَر الظَّهْرِي — the stable conductor
    ('SEAM', 'المِحْوَر', '#ff2222', 0.870, 0.04,
     [(0,270),(1,270)], 2),
]

VERTS = [
    ('T11',1.125),('T12',1.085),('L1',1.045),('L2',1.000),('L3',0.955),
    ('L4',0.910),('L5',0.870),('S1',0.830),('S2',0.800),('S3',0.780),
    ('S4',0.765),('S5',0.755),('Co',0.745),
]


def generate(path):
    MR = 0.105
    def off(y): return 0.75 * PI * MR
    def fx(deg, y):
        _, r, _, g = prof_at(y)
        er = r + g * max(0, math.cos(deg * PI / 180)) ** 2 * 0.8
        return a2x(deg, er, off(y))

    HIP_X = fx(90, HIP_Y)
    def cx(x): return x - HIP_X
    def cy(y): return y - HIP_Y

    # Compute all line points
    line_pts = []
    for label, ar, color, sy, bot, kf, lw in KHUTUT:
        pts = []
        is_warp = (label == 'L5')
        for s in range(301):
            t = s / 300.0
            y = lerp(sy, bot, t)
            a = ikf(kf, t) % 360
            bx = cx(fx(a, y))
            by = cy(y)
            # L5 below hip: force straight
            if is_warp and by < 0:
                # Foot center
                foot_cx = cx(fx(180, 0.08 - 0.11))
                foot_cy = cy(0.08 - 0.11)
                hip_bx = cx(fx(90, HIP_Y))  # = 0 by design
                # Linear from hip to foot
                frac = -by / (-foot_cy) if foot_cy != 0 else 0
                bx = lerp(0, foot_cx, min(frac, 1.0))
            pts.append((bx, by))
        line_pts.append((label, ar, color, lw, pts))

    # ═══════════════════════════════════════
    # SVG — Two panels: STANDING | RUKŪʿ
    # ═══════════════════════════════════════
    SC = 1400
    PW = 550; PH = 1500; GAP = 100
    W = PW * 2 + GAP + 100
    H = PH + 140
    P1X = 50 + PW // 2; P2X = 50 + PW + GAP + PW // 2
    P1Y = 100 + int(0.30 * PH); P2Y = P1Y

    def s1(bx, by): return P1X + bx * SC, P1Y - by * SC

    def s2(bx, by):
        if by <= 0:
            return P2X + bx * SC, P2Y - by * SC
        else:
            return P2X + (-by) * SC, P2Y - (-bx) * SC

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">')
    svg.append(f'<rect width="{W}" height="{H}" fill="#111122"/>')

    # Titles
    svg.append(f'<text x="{P1X}" y="28" text-anchor="middle" font-size="18" fill="#fff" font-family="monospace" font-weight="bold">قِيَام / STANDING</text>')
    svg.append(f'<text x="{P2X}" y="28" text-anchor="middle" font-size="18" fill="#fff" font-family="monospace" font-weight="bold">رُكُوع / RUKŪʿ</text>')
    svg.append(f'<text x="{W//2}" y="52" text-anchor="middle" font-size="12" fill="#888" font-family="monospace">خُطُوط ابن سينا — 11 lines per leg — L5 = WARP</text>')
    svg.append(f'<text x="{W//2}" y="68" text-anchor="middle" font-size="11" fill="#666" font-family="monospace">Q23:14 فَكَسَوْنَا الْعِظَامَ لَحْمًا</text>')

    # Panel backgrounds
    svg.append(f'<rect x="40" y="80" width="{PW+20}" height="{PH}" fill="#1a1a2e" rx="6"/>')
    svg.append(f'<rect x="{40+PW+GAP}" y="80" width="{PW+20}" height="{PH}" fill="#1a2e1a" rx="6"/>')

    # Arrow between
    ax = 50 + PW + GAP // 2
    svg.append(f'<text x="{ax}" y="{P1Y}" text-anchor="middle" font-size="28" fill="#fff">→</text>')
    svg.append(f'<text x="{ax}" y="{P1Y+18}" text-anchor="middle" font-size="9" fill="#888" font-family="monospace">fold at hip</text>')

    # FOLD LINES (hip level)
    for px, py in [(P1X, P1Y), (P2X, P2Y)]:
        svg.append(f'<line x1="{px-250}" y1="{py}" x2="{px+250}" y2="{py}" stroke="#fff" stroke-width="1" stroke-dasharray="5,3" opacity="0.4"/>')

    # HIP MARKERS
    for px, py in [(P1X, P1Y), (P2X, P2Y)]:
        svg.append(f'<circle cx="{px}" cy="{py}" r="6" fill="none" stroke="#fff" stroke-width="2"/>')
        svg.append(f'<line x1="{px-10}" y1="{py}" x2="{px+10}" y2="{py}" stroke="#fff" stroke-width="1.5"/>')
        svg.append(f'<line x1="{px}" y1="{py-10}" x2="{px}" y2="{py+10}" stroke="#fff" stroke-width="1.5"/>')

    # DRAW LINES — both panels
    MJ = 0.12
    for label, ar, color, lw, pts in line_pts:
        for panel_fn, panel_name in [(s1, 'standing'), (s2, 'ruku')]:
            svg_pts = [panel_fn(bx, by) for bx, by in pts]

            # Split at jumps
            segs = [[svg_pts[0]]]
            for i in range(1, len(svg_pts)):
                dx = abs(svg_pts[i][0] - svg_pts[i-1][0])
                dy = abs(svg_pts[i][1] - svg_pts[i-1][1])
                if dx > 80 or dy > 80:
                    segs.append([])
                segs[-1].append(svg_pts[i])

            for seg in segs:
                if len(seg) < 2: continue
                ps = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in seg)
                svg.append(f'<polyline points="{ps}" fill="none" stroke="{color}" stroke-width="{lw}" stroke-linecap="round" opacity="0.9"/>')

            # Label at start
            if svg_pts:
                lx, ly = svg_pts[0]
                svg.append(f'<text x="{lx+5}" y="{ly-4}" font-size="9" fill="{color}" font-family="monospace" font-weight="bold">{label}</text>')

    # VERTEBRAE — standing panel only
    for vn, vy in VERTS:
        sx, sy = s1(cx(fx(0, vy)), cy(vy))
        svg.append(f'<polygon points="{sx-3},{sy} {sx},{sy-3} {sx+3},{sy} {sx},{sy+3}" fill="#0a0"/>')
        svg.append(f'<text x="{sx+5}" y="{sy+3}" font-size="7" fill="#0a0" font-family="monospace">{vn}</text>')

    # LANDMARKS
    for lbl, deg, y, clr in [('T11', 0, T11_Y, '#f44'), ('BB', 180, BB_Y, '#f80'), ('PB', 270, PB_Y, '#c0c')]:
        sx, sy = s1(cx(fx(deg, y)), cy(y))
        svg.append(f'<circle cx="{sx}" cy="{sy}" r="4" fill="{clr}"/>')
        svg.append(f'<text x="{sx+6}" y="{sy+3}" font-size="9" fill="{clr}" font-family="monospace" font-weight="bold">{lbl}</text>')

    # ANNOTATIONS
    svg.append(f'<text x="{P1X}" y="{H-45}" text-anchor="middle" font-size="10" fill="#aaa" font-family="monospace">L5 (green) = WARP = straight from hip to plantar</text>')
    svg.append(f'<text x="{P1X}" y="{H-30}" text-anchor="middle" font-size="10" fill="#aaa" font-family="monospace">T11/T12 = horizontal trunk bands (WEFT direction)</text>')
    svg.append(f'<text x="{P2X}" y="{H-45}" text-anchor="middle" font-size="10" fill="#8f8" font-family="monospace">ALL lines align vertically in رُكُوع</text>')
    svg.append(f'<text x="{P2X}" y="{H-30}" text-anchor="middle" font-size="10" fill="#8f8" font-family="monospace">Hip = pivot = fold line = hinge of رُكُوع</text>')

    # Legend
    ly = 95
    for label, ar, color, lw, _ in line_pts:
        svg.append(f'<rect x="10" y="{ly}" width="12" height="3" fill="{color}"/>')
        svg.append(f'<text x="26" y="{ly+4}" font-size="8" fill="{color}" font-family="monospace">{label} {ar}</text>')
        ly += 13

    svg.append('</svg>')

    with open(path, 'w') as f:
        f.write('\n'.join(svg))
    print(f"✓ {path}\n  {W}x{H}px")


if __name__ == '__main__':
    generate(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'khutut_ibn_sina.svg'))
