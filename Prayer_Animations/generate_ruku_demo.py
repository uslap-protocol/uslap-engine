#!/usr/bin/env python3
"""
Demonstrate how dermatome lines align in rukūʿ.

Left panel:  STANDING — flat gore, lines fanning out
Right panel: RUKŪʿ    — fold at hip, upper rotates 90° forward
                        ALL lines become vertical/aligned

The WEFT line (hip) is the FOLD LINE = the hinge of rukūʿ.
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

# Dermatome keyframes
T11_KF=[(0,0),(0.25,90),(0.50,180),(1.0,180)]  # terminates at 180° (anterior)
T12_KF=[(0,0),(0.25,90),(0.50,180),(1.0,180)]
L1_KF=[(0,0),(.14,15),(.29,40),(.43,80),(.57,130),(.71,175),(.86,220),(.93,250),(1,270)]
L2_KF=[(0,0),(.06,15),(.14,40),(.23,80),(.34,130),(.49,170),(.57,195),(.71,220),(.86,250),(1,270)]
L3_KF=[(0,0),(.08,20),(.15,50),(.25,90),(.38,130),(.50,155),(.58,175),(.70,210),(.83,240),(.93,260),(1,270)]
L4_KF=[(0,0),(.04,15),(.10,40),(.18,70),(.28,105),(.38,135),(.48,160),(.55,175),(.62,195),(.72,210),(.82,215),(.92,218),(1,220)]
L5_KF=[(0,0),(.01,30),(.02,60),(.03,85),(.04,90),(.20,90),(.40,90),(.60,92),(.80,97),(.90,102),(1,105)]
S1_KF=[(0,0),(.05,10),(.12,22),(.22,36),(.35,46),(.50,53),(.65,58),(.78,61),(.90,63),(1,65)]
S2_KF=[(0,0),(.06,6),(.15,12),(.28,15),(.42,12),(.56,3),(.68,-15),(.78,-35),(.88,-60),(1,-90)]

HIP_Y = 0.850

LINES = [
    dict(label='T11', color='#aaaaaa', sy=1.125, bot=1.100, kf=T11_KF, lw=1.5),
    dict(label='T12', color='#888888', sy=1.085, bot=1.060, kf=T12_KF, lw=1.5),
    dict(label='L1',  color='#88bbee', sy=1.045, bot=0.830, kf=L1_KF, lw=2),
    dict(label='L2',  color='#6699dd', sy=1.000, bot=0.55,  kf=L2_KF, lw=2),
    dict(label='L3',  color='#dd5555', sy=0.955, bot=0.48,  kf=L3_KF, lw=2),
    dict(label='L4',  color='#ddcc22', sy=0.910, bot=0.08,  kf=L4_KF, lw=2),
    dict(label='L5',  color='#00ee00', sy=0.870, bot=0.08,  kf=L5_KF, lw=3),
    dict(label='S1',  color='#ee7788', sy=0.830, bot=0.08,  kf=S1_KF, lw=2),
    dict(label='S2',  color='#4466cc', sy=0.800, bot=0.48,  kf=S2_KF, lw=2),
]


def generate(path):
    MR = 0.105
    def off(y): return 0.75 * PI * MR
    def fx(deg, y):
        _, r, _, g = prof_at(y)
        er = r + g * max(0, math.cos(deg*PI/180))**2 * 0.8
        return angle_to_x(deg, er, off(y))

    # Hip position (anchor)
    HIP_X = fx(90, HIP_Y)

    # Body coords centered on hip
    def cx(x): return x - HIP_X
    def cy(y): return y - HIP_Y

    # Compute all line points in body coords (centered on hip)
    line_data = []  # (label, color, lw, [(x,y)...])
    for d in LINES:
        pts = []
        for s in range(201):
            t = s / 200.0
            y = lerp(d['sy'], d['bot'], t)
            a = interp_kf(d['kf'], t) % 360
            pts.append((cx(fx(a, y)), cy(y)))
        line_data.append((d['label'], d['color'], d['lw'], pts))

    # ═══════════════════════════════════════
    # SVG LAYOUT: two panels side by side
    # Left = STANDING, Right = RUKŪʿ
    # ═══════════════════════════════════════
    SC = 1200  # scale
    PW = 600   # panel width
    PH = 1600  # panel height
    GAP = 80   # gap between panels
    W = PW * 2 + GAP + 100
    H = PH + 120

    # Panel centers
    P1_CX = 50 + PW // 2   # standing panel
    P1_CY = 80 + int(0.35 * PH)  # hip at ~35% from top
    P2_CX = 50 + PW + GAP + PW // 2  # rukūʿ panel
    P2_CY = P1_CY

    def s1(bx, by):
        """Standing panel: body coords → SVG."""
        return P1_CX + bx * SC, P1_CY - by * SC

    def s2_ruku(bx, by):
        """Rukūʿ panel: body coords → SVG.
        Below hip (by <= 0): same as standing (leg stays vertical).
        Above hip (by > 0): rotate 90° forward.
        Height above hip → horizontal distance (leftward = forward).
        Horizontal position → flips to become small vertical adjustment."""
        if by <= 0:
            # Leg: unchanged
            return P2_CX + bx * SC, P2_CY - by * SC
        else:
            # Trunk: rotate 90° forward
            # Height above hip → horizontal distance (leftward = forward)
            # Horizontal offset flips to become small vertical adjustment
            rx = -by   # height becomes leftward reach
            ry = -bx   # horizontal offset flips to become small vertical adjustment
            return P2_CX + rx * SC, P2_CY - ry * SC

    svg = []
    svg.append(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}">')
    svg.append(f'<rect width="{W}" height="{H}" fill="#1a1a2e"/>')

    # Titles
    svg.append(f'<text x="{P1_CX}" y="30" text-anchor="middle" font-size="20" fill="#ffffff" font-family="monospace" font-weight="bold">STANDING</text>')
    svg.append(f'<text x="{P1_CX}" y="52" text-anchor="middle" font-size="12" fill="#888888" font-family="monospace">Lines fan outward</text>')
    svg.append(f'<text x="{P2_CX}" y="30" text-anchor="middle" font-size="20" fill="#ffffff" font-family="monospace" font-weight="bold">RUKŪʿ</text>')
    svg.append(f'<text x="{P2_CX}" y="52" text-anchor="middle" font-size="12" fill="#888888" font-family="monospace">ALL lines align vertically</text>')

    # Panel backgrounds
    svg.append(f'<rect x="50" y="65" width="{PW}" height="{PH}" fill="#222244" rx="8"/>')
    svg.append(f'<rect x="{50+PW+GAP}" y="65" width="{PW}" height="{PH}" fill="#223322" rx="8"/>')

    # ── WEFT LINE (hip fold line) — both panels ──
    for panel_cx, panel_cy in [(P1_CX, P1_CY), (P2_CX, P2_CY)]:
        svg.append(f'<line x1="{panel_cx-280}" y1="{panel_cy}" x2="{panel_cx+280}" y2="{panel_cy}" stroke="#ffffff" stroke-width="1" stroke-dasharray="6,4" opacity="0.5"/>')
        svg.append(f'<text x="{panel_cx+200}" y="{panel_cy-6}" fill="#ffffff" font-size="9" font-family="monospace" opacity="0.7">← FOLD LINE (hip) →</text>')

    # ── HIP MARKERS ──
    for panel_cx, panel_cy in [(P1_CX, P1_CY), (P2_CX, P2_CY)]:
        svg.append(f'<circle cx="{panel_cx}" cy="{panel_cy}" r="6" fill="none" stroke="#ffffff" stroke-width="2"/>')

    # ── DERMATOME LINES — STANDING (left panel) ──
    for label, color, lw, pts in line_data:
        svg_pts = [s1(x, y) for x, y in pts]
        pts_str = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in svg_pts)
        svg.append(f'<polyline points="{pts_str}" fill="none" stroke="{color}" stroke-width="{lw}" stroke-linecap="round"/>')
        # Label
        sx, sy = svg_pts[0]
        svg.append(f'<text x="{sx+5}" y="{sy-4}" font-size="10" fill="{color}" font-family="monospace" font-weight="bold">{label}</text>')

    # ── DERMATOME LINES — RUKŪʿ (right panel) ──
    for label, color, lw, pts in line_data:
        svg_pts = [s2_ruku(x, y) for x, y in pts]
        # Split if there's a sharp jump (at the fold)
        segs = [[svg_pts[0]]]
        for i in range(1, len(svg_pts)):
            dx = abs(svg_pts[i][0] - svg_pts[i-1][0])
            dy = abs(svg_pts[i][1] - svg_pts[i-1][1])
            if dx > 100 or dy > 100:
                segs.append([])
            segs[-1].append(svg_pts[i])

        for seg in segs:
            if len(seg) < 2: continue
            pts_str = " ".join(f"{p[0]:.1f},{p[1]:.1f}" for p in seg)
            svg.append(f'<polyline points="{pts_str}" fill="none" stroke="{color}" stroke-width="{lw}" stroke-linecap="round"/>')

        # Label
        sx, sy = svg_pts[0]
        svg.append(f'<text x="{sx+5}" y="{sy-4}" font-size="10" fill="{color}" font-family="monospace" font-weight="bold">{label}</text>')

    # ── ANNOTATIONS ──
    # Standing: show fan angle
    svg.append(f'<text x="{P1_CX}" y="{P1_CY + 380}" text-anchor="middle" font-size="11" fill="#aaaaaa" font-family="monospace">Lines fan from spine</text>')
    svg.append(f'<text x="{P1_CX}" y="{P1_CY + 396}" text-anchor="middle" font-size="11" fill="#aaaaaa" font-family="monospace">T11/T12 = horizontal (WEFT)</text>')
    svg.append(f'<text x="{P1_CX}" y="{P1_CY + 412}" text-anchor="middle" font-size="11" fill="#aaaaaa" font-family="monospace">L5 = vertical (WARP)</text>')

    # Rukūʿ: show alignment
    svg.append(f'<text x="{P2_CX}" y="{P2_CY + 380}" text-anchor="middle" font-size="11" fill="#88ff88" font-family="monospace">Trunk folds 90° at hip</text>')
    svg.append(f'<text x="{P2_CX}" y="{P2_CY + 396}" text-anchor="middle" font-size="11" fill="#88ff88" font-family="monospace">T11/T12 rotate → become VERTICAL</text>')
    svg.append(f'<text x="{P2_CX}" y="{P2_CY + 412}" text-anchor="middle" font-size="11" fill="#88ff88" font-family="monospace">ALL lines ALIGN ↓</text>')

    # Arrow between panels
    ax = 50 + PW + GAP // 2
    svg.append(f'<text x="{ax}" y="{P1_CY}" text-anchor="middle" font-size="30" fill="#ffffff" font-family="monospace">→</text>')
    svg.append(f'<text x="{ax}" y="{P1_CY + 20}" text-anchor="middle" font-size="10" fill="#888888" font-family="monospace">fold</text>')

    # Legend
    ly = H - 20
    for d in reversed(LINES):
        svg.append(f'<rect x="10" y="{ly-8}" width="15" height="3" fill="{d["color"]}"/>')
        svg.append(f'<text x="30" y="{ly-3}" font-size="9" fill="{d["color"]}" font-family="monospace">{d["label"]}</text>')
        ly -= 14

    svg.append('</svg>')

    with open(path, 'w') as f:
        f.write('\n'.join(svg))
    print(f"✓ {path}\n  {W}x{H}px")


if __name__ == '__main__':
    generate(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dermatome_ruku_demo.svg'))
