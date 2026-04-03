#!/usr/bin/env python3
"""
ONE LEG — rukūʿ pose (leg stays vertical).
Dermatome territories as COLORED SURFACES (not just lines).
Each face colored by which territory it falls in.

Reference: Screen Shot cutaneous nerve 3D model + 3 criminal maps.
"""
import math, os

PI = math.pi
def lerp(a, b, t): return a + (b - a) * t

PROFILE = [
    (0.080, 0.035), (0.150, 0.040), (0.250, 0.048),
    (0.350, 0.055), (0.450, 0.050), (0.500, 0.055),
    (0.600, 0.070), (0.700, 0.080), (0.780, 0.090),
    (0.830, 0.105), (0.870, 0.120), (0.910, 0.115),
    (0.955, 0.110), (1.000, 0.100),
]

def prof_r(y):
    if y <= PROFILE[0][0]: return PROFILE[0][1]
    if y >= PROFILE[-1][0]: return PROFILE[-1][1]
    for i in range(len(PROFILE) - 1):
        y0, r0 = PROFILE[i]; y1, r1 = PROFILE[i + 1]
        if y0 <= y <= y1:
            return lerp(r0, r1, (y - y0) / (y1 - y0))
    return PROFILE[-1][1]

def ikf(kf, t):
    if t <= kf[0][0]: return kf[0][1]
    if t >= kf[-1][0]: return kf[-1][1]
    for i in range(len(kf) - 1):
        t0, a0 = kf[i]; t1, a1 = kf[i + 1]
        if t0 <= t <= t1: return lerp(a0, a1, (t - t0) / (t1 - t0) if t1 != t0 else 0)
    return kf[-1][1]

# Dermatome boundary keyframes (degrees)
# Each defines the boundary between this territory and the next
BOUNDARIES = [
    # (label, spine_y, bot_y, keyframes, color_rgb)
    # Order: from posterior (spine side) toward anterior (seam side)
    # S2 boundary (closest to spine/posterior)
    ('S2', 0.800, 0.48, [(0,0),(.06,6),(.15,12),(.28,15),(.42,12),(.56,3),(.68,-15),(.78,-35),(.88,-60),(1,-90)]),
    # S1 boundary
    ('S1', 0.830, 0.08, [(0,0),(.05,10),(.12,22),(.22,36),(.35,46),(.50,53),(.65,58),(.78,61),(.90,63),(1,65)]),
    # L5 boundary (THE WARP)
    ('L5', 0.870, 0.08, [(0,0),(.01,30),(.02,60),(.03,85),(.04,90),(.20,90),(.40,90),(.60,92),(.80,97),(.90,102),(1,105)]),
    # L4 boundary
    ('L4', 0.910, 0.08, [(0,0),(.04,15),(.10,40),(.18,70),(.28,105),(.38,135),(.48,160),(.55,175),(.62,195),(.72,210),(.82,215),(.92,218),(1,220)]),
    # L3 boundary
    ('L3', 0.955, 0.48, [(0,0),(.08,20),(.15,50),(.25,90),(.38,130),(.50,155),(.58,175),(.70,210),(.83,240),(.93,260),(1,270)]),
    # L2 boundary
    ('L2', 1.000, 0.55, [(0,0),(.06,15),(.14,40),(.23,80),(.34,130),(.49,170),(.57,195),(.71,220),(.86,250),(1,270)]),
    # L1 boundary
    ('L1', 1.045, 0.83, [(0,0),(.14,15),(.29,40),(.43,80),(.57,130),(.71,175),(.86,220),(.93,250),(1,270)]),
]

# Territory colors (between boundaries)
# Territory between spine edge (0°) and S2 = "S2 territory" (posterior midline)
# Territory between S2 and S1 = "S1 territory" (posterior-lateral)
# etc.
TERRITORY_COLORS = {
    'posterior': (0.30, 0.30, 0.80),  # S2+ (posterior midline) — blue
    'S2': (0.30, 0.30, 0.80),        # S2 territory — blue
    'S1': (0.90, 0.45, 0.55),        # S1 territory — pink
    'L5': (0.90, 0.85, 0.20),        # L5 territory — yellow
    'L4': (0.85, 0.80, 0.15),        # L4 territory — dark yellow
    'L3': (0.85, 0.35, 0.35),        # L3 territory — red
    'L2': (0.45, 0.70, 0.90),        # L2 territory — light blue
    'L1': (0.55, 0.78, 0.95),        # L1 territory — lighter blue
    'anterior': (0.55, 0.85, 0.55),  # beyond L1 toward seam — green (trunk territory)
}


def get_boundary_angle(boundary, y):
    """Get the angle of a boundary line at height y. Returns None if y is outside the line's range."""
    label, sy, bot, kf = boundary
    if y > sy or y < bot:
        return None
    t = (sy - y) / (sy - bot) if sy != bot else 0
    return ikf(kf, t)


def get_territory(angle_deg, y):
    """Determine which territory a point at (angle, y) belongs to."""
    # Normalize angle to 0-360
    a = angle_deg % 360

    # Get all active boundary angles at this height
    active = []
    for b in BOUNDARIES:
        ba = get_boundary_angle(b, y)
        if ba is not None:
            # Normalize
            ba_norm = ba % 360
            active.append((ba_norm, b[0]))

    if not active:
        # No boundaries active at this height — everything is trunk territory
        if a < 180:
            return 'posterior'
        else:
            return 'anterior'

    # Sort by angle
    active.sort(key=lambda x: x[0])

    # Find which territory the angle falls in
    # From 0° (spine) going counterclockwise:
    # 0° → first boundary = posterior/S2 territory
    # first boundary → second boundary = S1 territory
    # etc.

    territory_names = ['posterior'] + [b[0] for b in BOUNDARIES] + ['anterior']

    # Check each interval
    prev_angle = 0  # start from spine (0°)
    for i, (ba, label) in enumerate(active):
        if a < ba:
            return territory_names[i]
        prev_angle = ba

    # Past all boundaries = anterior/seam territory
    return 'anterior'


def write_obj(path):
    verts = []
    ring_n = 48
    SEP = 0.10  # half leg separation

    # Generate one right leg from hip to ankle
    y_list = []
    for yi in range(16, 195, 3):
        y_list.append(yi / 200.0)
    y_list.sort(reverse=True)

    rings = []
    ring_territories = []  # territory name for each vertex

    for y in y_list:
        r = prof_r(y)
        ring = []
        terrs = []
        for i in range(ring_n + 1):
            a_deg = 360.0 * i / ring_n
            a_rad = a_deg * PI / 180.0

            # Glute bulge for posterior
            glute = 0
            if y > 0.78 and y < 0.92:
                glute_peak = 0.070 if y > 0.83 and y < 0.88 else 0.030
                posterior = max(0, math.cos(a_rad))
                glute = glute_peak * posterior ** 2

            r_eff = r + glute
            x = SEP + r_eff * math.sin(a_rad)
            z = r_eff * math.cos(a_rad)

            verts.append((x, y, z))
            ring.append(len(verts) - 1)

            # Determine territory
            terr = get_territory(a_deg, y)
            terrs.append(terr)

        rings.append(ring)
        ring_territories.append(terrs)

    # Foot
    ANKLE_Y = 0.080
    FOOT_LEN = 0.26
    foot_rings = []
    foot_terrs = []
    for fi in range(11):
        frac = fi / 10.0
        fw = lerp(0.035, 0.050, frac / 0.6) if frac < 0.6 else lerp(0.050, 0.018, (frac - 0.6) / 0.4)
        fh = lerp(0.030, 0.010, frac)
        ring = []
        terrs = []
        for i in range(ring_n + 1):
            a = 2 * PI * i / ring_n
            a_deg = math.degrees(a)
            x = SEP + fw * math.sin(a)
            y_drop = lerp(0, 0.035, min(frac * 2, 1.0))
            y = ANKLE_Y - y_drop + fh * math.cos(a)
            z = prof_r(ANKLE_Y) - frac * FOOT_LEN
            verts.append((x, y, z))
            ring.append(len(verts) - 1)

            # Foot territories
            if a_deg < 65 or a_deg > 300:
                terrs.append('S1')      # sole/heel/little toe
            elif a_deg < 105:
                terrs.append('L5')      # dorsum
            elif a_deg < 200:
                terrs.append('L4')      # medial/big toe side
            else:
                terrs.append('L5')      # lateral
        foot_rings.append(ring)
        foot_terrs.append(terrs)

    # Dermatome boundary lines (on the surface, offset)
    derm_lines = []
    for b in BOUNDARIES:
        label, sy, bot, kf = b
        pts_start = len(verts)
        for s in range(201):
            t = s / 200.0
            y = lerp(sy, bot, t)
            a_deg = ikf(kf, t)
            a_rad = a_deg * PI / 180.0
            r = prof_r(y)

            glute = 0
            if y > 0.78 and y < 0.92:
                glute_peak = 0.070 if y > 0.83 and y < 0.88 else 0.030
                posterior = max(0, math.cos(a_rad))
                glute = glute_peak * posterior ** 2

            r_eff = r + glute + 0.004  # offset above surface
            x = SEP + r_eff * math.sin(a_rad)
            z = r_eff * math.cos(a_rad)
            verts.append((x, y, z))
        pts_end = len(verts) - 1
        derm_lines.append((label, pts_start, pts_end))

    # Seam line (المِحْوَر الظَّهْرِي)
    seam_start = len(verts)
    for yi in range(16, 180, 3):
        y = yi / 200.0
        r = prof_r(y) + 0.004
        a_rad = 270 * PI / 180
        x = SEP + r * math.sin(a_rad)
        z = r * math.cos(a_rad)
        verts.append((x, y, z))
    seam_end = len(verts) - 1

    # L5 WARP line (straight from hip to foot)
    warp_start = len(verts)
    hip_r = prof_r(0.85)
    hip_x = SEP + (hip_r + 0.005) * math.sin(PI / 2)
    hip_z = (hip_r + 0.005) * math.cos(PI / 2)
    foot_x = SEP
    foot_z = prof_r(ANKLE_Y) - FOOT_LEN * 0.5
    for s in range(21):
        t = s / 20.0
        verts.append((lerp(hip_x, foot_x, t), lerp(0.85, 0.08 - 0.035, t), lerp(hip_z, foot_z, t)))
    warp_end = len(verts) - 1

    # ═══════════════════════════════════════
    # WRITE OBJ
    # ═══════════════════════════════════════
    mtl_name = os.path.basename(path).replace('.obj', '.mtl')
    with open(path, 'w') as f:
        f.write(f"# ONE LEG — Rukūʿ pose (vertical)\n")
        f.write(f"# Colored dermatome territories\n")
        f.write(f"# Verts: {len(verts)}\nmtllib {mtl_name}\n\n")

        for v in verts:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

        # Body faces — grouped by territory
        territory_faces = {}
        for ri in range(len(rings) - 1):
            r0 = rings[ri]; r1 = rings[ri + 1]
            t0 = ring_territories[ri]; t1 = ring_territories[ri + 1]
            n = min(len(r0), len(r1)) - 1
            for j in range(n):
                # Use the territory of the top-left vertex
                terr = t0[j]
                if terr not in territory_faces:
                    territory_faces[terr] = []
                territory_faces[terr].append(f"f {r0[j]+1} {r0[j+1]+1} {r1[j+1]+1} {r1[j]+1}")

        # Ankle connection
        if rings and foot_rings:
            r0 = rings[-1]; r1 = foot_rings[0]
            t0 = ring_territories[-1]; t1 = foot_terrs[0]
            for j in range(min(len(r0), len(r1)) - 1):
                terr = t0[j]
                if terr not in territory_faces:
                    territory_faces[terr] = []
                territory_faces[terr].append(f"f {r0[j]+1} {r0[j+1]+1} {r1[j+1]+1} {r1[j]+1}")

        # Foot faces
        for ri in range(len(foot_rings) - 1):
            r0 = foot_rings[ri]; r1 = foot_rings[ri + 1]
            t0 = foot_terrs[ri]
            for j in range(min(len(r0), len(r1)) - 1):
                terr = t0[j]
                if terr not in territory_faces:
                    territory_faces[terr] = []
                territory_faces[terr].append(f"f {r0[j]+1} {r0[j+1]+1} {r1[j+1]+1} {r1[j]+1}")

        # Write territory groups
        for terr, faces in territory_faces.items():
            mat = f"terr_{terr}"
            f.write(f"\ng Territory_{terr}\nusemtl {mat}\n")
            for face in faces:
                f.write(face + "\n")

        # Boundary lines
        f.write("\n# ═══ BOUNDARY LINES ═══\n")
        for label, ps, pe in derm_lines:
            f.write(f"\ng Line_{label}\nusemtl line_{label}\n")
            f.write("l " + " ".join(str(i + 1) for i in range(ps, pe + 1)) + "\n")

        # Seam
        f.write(f"\ng Seam\nusemtl line_seam\n")
        f.write("l " + " ".join(str(i + 1) for i in range(seam_start, seam_end + 1)) + "\n")

        # WARP (L5 straight)
        f.write(f"\ng WARP_L5\nusemtl line_warp\n")
        f.write("l " + " ".join(str(i + 1) for i in range(warp_start, warp_end + 1)) + "\n")

    # MTL
    mtl_path = path.replace('.obj', '.mtl')
    with open(mtl_path, 'w') as f:
        for terr, (r, g, b) in TERRITORY_COLORS.items():
            f.write(f"newmtl terr_{terr}\nKd {r:.2f} {g:.2f} {b:.2f}\n\n")
        # Boundary line materials
        line_colors = {
            'S2': (0.20, 0.20, 0.70), 'S1': (0.80, 0.35, 0.45),
            'L5': (0.00, 0.90, 0.00), 'L4': (0.85, 0.80, 0.10),
            'L3': (0.75, 0.25, 0.25), 'L2': (0.35, 0.60, 0.80),
            'L1': (0.45, 0.68, 0.85),
        }
        for label, (r, g, b) in line_colors.items():
            f.write(f"newmtl line_{label}\nKd {r:.2f} {g:.2f} {b:.2f}\n\n")
        f.write("newmtl line_seam\nKd 0.90 0.10 0.10\n\n")
        f.write("newmtl line_warp\nKd 0.00 1.00 0.00\n\n")

    print(f"✓ {path}")
    print(f"✓ {mtl_path}")
    print(f"  Verts: {len(verts)}")
    print(f"  Territories: {list(territory_faces.keys())}")


if __name__ == '__main__':
    write_obj(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'one_leg_ruku.obj'))
