#!/usr/bin/env python3
"""
Generate a dermatome 3D mannequin with spiral nerve lines as OBJ.
Real-world scale: 1.75m tall. No Blender needed.
Clinical reference: Keegan & Garrett 1948 dermatome map.

Fixes: non-overlapping legs, feet, arms, correct spiral positions.
"""
import math, os

PI = math.pi

def lerp(a, b, t):
    return a + (b - a) * t

def smoothstep(t):
    t = max(0, min(1, t))
    return t * t * (3 - 2 * t)

# ══════════════════════════════════════════════════════
# BODY PROFILE — (y_meters, radius, separation, glute)
# glute = extra posterior bulge for buttocks/hamstrings
# ══════════════════════════════════════════════════════
PROFILE = [
    # y,     r,     sep,    glute
    (0.080, 0.035, 0.200, 0.000),   # ankle
    (0.150, 0.040, 0.200, 0.000),   # lower shin
    (0.250, 0.048, 0.200, 0.000),   # shin
    (0.350, 0.055, 0.200, 0.000),   # mid calf
    (0.450, 0.050, 0.200, 0.000),   # upper calf
    (0.500, 0.055, 0.200, 0.000),   # knee
    (0.600, 0.070, 0.200, 0.000),   # lower thigh
    (0.700, 0.080, 0.200, 0.008),   # mid thigh — hamstring
    (0.780, 0.090, 0.200, 0.025),   # upper thigh — glutes start
    (0.820, 0.105, 0.195, 0.055),   # crotch — WIDEST (glutes + hips)
    (0.850, 0.120, 0.150, 0.070),   # pelvis — peak glute, WIDEST POINT
    (0.880, 0.115, 0.100, 0.060),   # pelvis merging — full glutes
    (0.910, 0.110, 0.050, 0.040),   # hips — glutes tapering
    (0.940, 0.105, 0.000, 0.020),   # merged — lumbar curve
    (0.980, 0.095, 0.000, 0.008),   # waist narrow (NARROWER than hips)
    (1.020, 0.105, 0.000, 0.000),   # above waist
    (1.060, 0.115, 0.000, 0.000),   # lower ribs
    (1.100, 0.130, 0.000, 0.000),   # ribcage
    (1.150, 0.145, 0.000, 0.000),   # chest
    (1.200, 0.155, 0.000, 0.000),   # upper chest
    (1.250, 0.180, 0.000, 0.000),   # shoulders (widest)
    (1.300, 0.160, 0.000, 0.000),   # upper shoulder
    (1.340, 0.060, 0.000, 0.000),   # neck base
    (1.380, 0.050, 0.000, 0.000),   # neck
    (1.420, 0.048, 0.000, 0.000),   # upper neck
    (1.460, 0.060, 0.000, 0.000),   # jaw
    (1.510, 0.075, 0.000, 0.000),   # face
    (1.560, 0.082, 0.000, 0.000),   # widest head
    (1.620, 0.078, 0.000, 0.000),   # upper head
    (1.680, 0.065, 0.000, 0.000),   # top head
    (1.750, 0.025, 0.000, 0.000),   # crown
]

def prof_at(y):
    if y <= PROFILE[0][0]: return PROFILE[0]
    if y >= PROFILE[-1][0]: return PROFILE[-1]
    for i in range(len(PROFILE) - 1):
        y0, r0, s0, g0 = PROFILE[i]
        y1, r1, s1, g1 = PROFILE[i+1]
        if y0 <= y <= y1:
            t = (y - y0) / (y1 - y0) if y1 != y0 else 0
            return (y, lerp(r0, r1, t), lerp(s0, s1, t), lerp(g0, g1, t))
    return PROFILE[-1]

# ══════════════════════════════════════════════════════
# SURFACE POINT — with crotch blending + glute bulge
# ══════════════════════════════════════════════════════
CROTCH_Y = 0.820
BLEND_TOP = 0.910
BLEND_BOT = 0.790

def body_surface(angle, y, side='R', offset=0.0):
    """Point on body surface. angle: 0=back, PI/2=lateral, PI=front, >PI=medial.
    offset: radial offset above surface (for lines that need to sit ON TOP of glutes)."""
    _, r, sep, glute = prof_at(y)
    hsep = sep / 2.0
    sign = 1.0 if side == 'R' else -1.0

    # Glute bulge: cos(angle)=+1 at posterior (angle=0), 0 at lateral, -1 at anterior
    # Only add on posterior half, with smooth cos^2 falloff
    posterior = max(0, math.cos(angle))
    glute_add = glute * posterior * posterior

    # Total radius with offset
    r_total = r + glute_add + offset

    # Leg point
    lx = sign * hsep + r_total * math.sin(angle)
    lz = r_total * math.cos(angle)

    # Body point (merged, no sep offset)
    bx = r_total * math.sin(angle)
    bz = r_total * math.cos(angle)

    if y >= BLEND_TOP:
        return (bx, y, bz)
    elif y <= BLEND_BOT:
        return (lx, y, lz)
    else:
        sm = smoothstep((y - BLEND_BOT) / (BLEND_TOP - BLEND_BOT))
        return (lerp(lx, bx, sm), y, lerp(lz, bz, sm))


# ══════════════════════════════════════════════════════
# FOOT — elongated shape extending forward from ankle
# ══════════════════════════════════════════════════════
FOOT_LEN = 0.26  # heel to toe
ANKLE_Y = 0.080

def foot_ring(frac, angle, side='R'):
    """frac: 0=heel, 1=toes. angle: 0=top, PI=sole, PI/2=outer."""
    sign = 1.0 if side == 'R' else -1.0
    _, r, sep, _ = prof_at(ANKLE_Y)
    cx = sign * sep / 2.0

    # Width: widens at ball, narrows at toes
    fw = lerp(0.035, 0.050, frac / 0.6) if frac < 0.6 else lerp(0.050, 0.018, (frac - 0.6) / 0.4)
    # Height: tall at heel, flat at toes
    fh = lerp(0.030, 0.010, frac)

    x = cx + fw * math.sin(angle)
    y_drop = lerp(0, 0.035, min(frac * 2, 1.0))  # drops from ankle
    y = ANKLE_Y - y_drop + fh * math.cos(angle)
    z = r - frac * FOOT_LEN  # extends forward

    return (x, y, z)


# ══════════════════════════════════════════════════════
# ARM — cylinder from shoulder to fingertips
# Pose: ~30° abduction, palms forward
# ══════════════════════════════════════════════════════
ARM_LEN = 0.72
SHOULDER_Y = 1.28
SHOULDER_X = 0.185

ARM_R = [  # (t, radius)
    (0.0, 0.052), (0.15, 0.048), (0.35, 0.044), (0.48, 0.040),
    (0.52, 0.038), (0.65, 0.034), (0.80, 0.030), (0.88, 0.032),
    (0.94, 0.026), (1.0, 0.012),
]

def arm_r(t):
    if t <= 0: return ARM_R[0][1]
    if t >= 1: return ARM_R[-1][1]
    for i in range(len(ARM_R) - 1):
        t0, r0 = ARM_R[i]
        t1, r1 = ARM_R[i+1]
        if t0 <= t <= t1:
            return lerp(r0, r1, (t - t0) / (t1 - t0))
    return ARM_R[-1][1]

def arm_center(t, side='R'):
    """Center point of arm at position t (0=shoulder, 1=fingertip)."""
    sign = 1.0 if side == 'R' else -1.0
    abd = math.radians(30)
    fwd = math.radians(8)
    x = sign * (SHOULDER_X + t * ARM_LEN * math.sin(abd))
    y = SHOULDER_Y - t * ARM_LEN * math.cos(abd)
    z = -t * ARM_LEN * math.sin(fwd)
    return (x, y, z)

def arm_ring(t, angle, side='R'):
    """Point on arm surface at position t, angle around cross-section."""
    cx, cy, cz = arm_center(t, side)
    r = arm_r(t)
    sign = 1.0 if side == 'R' else -1.0
    abd = math.radians(30)
    # Cross-section perpendicular to arm axis
    # Simplified: lateral = along arm axis outward, other = z
    x = cx + r * math.cos(angle) * math.cos(abd) * sign
    y = cy + r * math.cos(angle) * math.sin(abd)
    z = cz + r * math.sin(angle)
    return (x, y, z)


# ══════════════════════════════════════════════════════
# DERMATOME DEFINITIONS — KEYFRAME-BASED PATHS
# Each line defined by (t, angle_radians) keyframes
# traced directly from Keegan & Garrett clinical map
# Angles: 0=posterior, PI/2=lateral, PI=anterior, >PI=medial
# t: 0=spine origin, 1=distal endpoint
# ══════════════════════════════════════════════════════

def _rad(deg):
    return deg * PI / 180.0

# ── L4: THE CROSSOVER ──────────────────────────────
# Traced from clinical map:
#   Lateral view: diagonal from posterior hip → anterior knee
#   Front view: crosses ventral axial line at knee → medial shin → big toe
#   Back view: barely visible upper thigh, appears on medial lower leg
#   Angular sweep: ~220° (spine to medial ankle)
#   Wrap is FAST through hip/thigh, SLOW on shin (line mostly descends vertically)
L4_KEYFRAMES = [
    # (t,   angle_deg)  — traced from clinical map
    (0.00,    0),     # spine origin (posterior midline)
    (0.04,   15),     # just starting to wrap past sacrum
    (0.10,   40),     # wrapping past glutes
    (0.18,   70),     # reaching lateral hip
    (0.28,  105),     # anterior-lateral upper thigh
    (0.38,  135),     # anterior thigh (visible on front view)
    (0.48,  160),     # approaching knee, nearing ventral axial line
    (0.55,  175),     # at knee — about to cross ventral axial line
    (0.62,  195),     # just past crossing — now on medial side
    (0.72,  210),     # medial shin
    (0.82,  215),     # medial lower shin (line nearly vertical now)
    (0.92,  218),     # medial ankle area
    (1.00,  220),     # medial ankle — continues to big toe via foot
]

# ── L1: GROIN / INGUINAL ──────────────────────────
# Front view: small band at groin, most MEDIAL of all thigh lines
# Short line — wraps quickly to medial groin, ends at upper thigh
# Sweep: ~210° over short distance
# All lines use similar spiral shape (parallel) with even angular spacing.
# At mid-thigh (y≈0.65), gaps between adjacent lines ≈ 40°.
# Lines that reach the seam converge in their final 20% of descent.

L1_KEYFRAMES = [
    (0.00,    0),     # spine
    (0.14,   15),     # past sacrum
    (0.29,   40),     # past glutes
    (0.43,   80),     # lateral hip — fast fan-out
    (0.57,  130),     # anterior
    (0.71,  175),     # anterior-medial
    (0.86,  220),     # medial
    (0.93,  250),     # approaching seam
    (1.00,  270),     # ← CONVERGES TO SEAM
]

# ── L2: ANTERIOR THIGH ────────────────────────────
L2_KEYFRAMES = [
    (0.00,    0),     # spine
    (0.06,   15),     # past sacrum
    (0.14,   40),     # past glutes
    (0.23,   80),     # lateral hip
    (0.34,  130),     # anterior-lateral
    (0.49,  170),     # anterior thigh
    (0.57,  195),     # anterior-medial
    (0.71,  220),     # medial
    (0.86,  250),     # approaching seam
    (1.00,  270),     # ← CONVERGES TO SEAM
]

# ── L3: ANTERIOR THIGH TO KNEE ────────────────────
L3_KEYFRAMES = [
    (0.00,    0),     # spine
    (0.08,   20),     # past sacrum
    (0.15,   50),     # past glutes
    (0.25,   90),     # lateral hip
    (0.38,  130),     # anterior-lateral
    (0.50,  155),     # anterior thigh
    (0.58,  175),     # anterior knee
    (0.70,  210),     # crossing to medial
    (0.83,  240),     # approaching seam
    (0.93,  260),     # nearly there
    (1.00,  270),     # ← CONVERGES TO SEAM
]

# ── L5: LATERAL SHIN → DORSUM OF FOOT ─────────────
# Lateral view: clearly visible as band on lateral shin
# Does NOT cross ventral axial line — stays lateral/anterior-lateral
# Sweep: ~105°. Evenly spaced from S1 (below) and L4 (above).
L5_KEYFRAMES = [
    (0.00,    0),     # spine
    (0.01,   30),     # rapid lateral turn
    (0.02,   60),     # reaching lateral
    (0.03,   85),     # near-lateral
    (0.04,   90),     # full lateral — stays ~90° down the leg
    (0.20,   90),     # lateral thigh
    (0.40,   90),     # lateral knee
    (0.60,   92),     # lateral shin
    (0.80,   97),     # lateral-anterior lower shin
    (0.90,  102),     # anterior-lateral ankle
    (1.00,  105),     # dorsum of foot
]

# ── S1: POSTERIOR-LATERAL → HEEL → LITTLE TOE ─────
# Largest lower limb dermatome
# Back view: wide band on posterior thigh and calf
# Stays posterior-lateral throughout — does NOT cross ventral axial line
# Sweep: ~65°. Evenly spaced from S2 (below) and L5 (above).
S1_KEYFRAMES = [
    (0.00,    0),     # spine
    (0.05,   10),     # past sacrum — even fan-out
    (0.12,   22),     # past glutes
    (0.22,   36),     # posterior-lateral hip
    (0.35,   46),     # posterior-lateral thigh
    (0.50,   53),     # posterior-lateral knee
    (0.65,   58),     # posterior-lateral calf — plateaus
    (0.78,   61),     # posterior-lateral lower calf
    (0.90,   63),     # posterior-lateral ankle
    (1.00,   65),     # posterior-lateral → heel, sole, little toe
]

# ── S2: POSTERIOR MIDLINE → CONVERGES TO SEAM ─────
# Back view: narrow strip close to posterior midline
# Approaches seam from the posterior side
# Goes through posterior → medial (the short way around)
# Using negative angles: 15° → 0° → -90° (= 270°)
# Evenly spaced from S1 (above). Smooth convergence to seam.
S2_KEYFRAMES = [
    (0.00,    0),     # spine
    (0.06,    6),     # past sacrum
    (0.15,   12),     # posterior — even fan-out
    (0.28,   15),     # posterior thigh — peak lateral excursion
    (0.42,   12),     # starting to curve toward seam
    (0.56,    3),     # crossing posterior midline
    (0.68,  -15),     # heading toward medial (inner leg)
    (0.78,  -35),     # approaching seam
    (0.88,  -60),     # nearly there
    (1.00,  -90),     # ← CONVERGES TO SEAM (= 270°)
]

# ── COCCYX LINE (THE SEAM / VENTRAL AXIAL LINE) ───
# The main axis: coccyx → perineum → inner leg → plantar
# Starts at coccyx (posterior, 0°), sweeps through perineum
# to the pure MEDIAL surface (270°) of the inner leg,
# then runs straight down the inner leg to the sole
# All dermatome lines spiral around this central axis
# Origin: pubic bone / groin (matches clinical map image)
# Already at the medial surface — goes straight down inner leg
COCCYX_KEYFRAMES = [
    (0.00,  270),     # pubic bone — already at inner (medial) surface
    (0.10,  270),     # inner upper thigh
    (0.25,  270),     # inner mid thigh
    (0.40,  270),     # inner lower thigh
    (0.55,  270),     # inner knee
    (0.70,  270),     # inner shin
    (0.85,  270),     # inner lower shin
    (1.00,  270),     # inner ankle → continues to plantar (sole)
]

# ── S3: PERINEAL RING (outer) ─────────────────────
# Concentric ring around perineum/buttocks, visible between legs
S3_KEYFRAMES = [
    (0.00,    0),
    (0.25,   90),
    (0.50,  180),
    (0.75,  270),
    (1.00,  360),    # full ring
]

# ── S4: PERINEAL RING (middle) ────────────────────
S4_KEYFRAMES = [
    (0.00,    0),
    (0.25,   90),
    (0.50,  180),
    (0.75,  270),
    (1.00,  360),
]

# ── S5: PERINEAL RING (innermost) ─────────────────
S5_KEYFRAMES = [
    (0.00,    0),
    (0.25,   90),
    (0.50,  180),
    (0.75,  270),
    (1.00,  360),
]

DERMATOMES = [
    # L1: groin (short, medial)
    dict(label='L1', color='lt_blue', spine_y=0.92, bot=0.78,
         keyframes=[(t, _rad(a)) for t, a in L1_KEYFRAMES],
         note='groin/inguinal — terminates at medial upper thigh'),
    # L2: anterior thigh
    dict(label='L2', color='lt_blue', spine_y=0.90, bot=0.55,
         keyframes=[(t, _rad(a)) for t, a in L2_KEYFRAMES],
         note='anterior thigh — terminates mid-thigh'),
    # L3: anterior thigh to knee
    dict(label='L3', color='red_dot', spine_y=0.88, bot=0.48,
         keyframes=[(t, _rad(a)) for t, a in L3_KEYFRAMES],
         note='anterior thigh across knee'),
    # L4: THE crossover (verified ✓)
    dict(label='L4', color='yellow', spine_y=0.86, bot=0.08,
         keyframes=[(t, _rad(a)) for t, a in L4_KEYFRAMES],
         foot=0.7, foot_angle=-PI/2,
         note='lateral thigh → crosses ventral axial line at knee → medial shin → big toe'),
    # L5: lateral shin to dorsum of foot
    dict(label='L5', color='yellow', spine_y=0.84, bot=0.08,
         keyframes=[(t, _rad(a)) for t, a in L5_KEYFRAMES],
         foot=0.9, foot_angle=0,
         note='lateral shin → dorsum of foot → toes'),
    # S1: posterior-lateral to heel
    dict(label='S1', color='pink', spine_y=0.82, bot=0.08,
         keyframes=[(t, _rad(a)) for t, a in S1_KEYFRAMES],
         foot=1.0, foot_angle=PI/2,
         note='posterior-lateral → heel → sole → little toe'),
    # S2: posterior midline — ends at popliteal fossa (back of knee)
    dict(label='S2', color='blue_dot', spine_y=0.80, bot=0.48,
         keyframes=[(t, _rad(a)) for t, a in S2_KEYFRAMES],
         note='posterior midline of thigh — ends at back of knee'),
    # S3: perineal outer ring
    dict(label='S3', color='pink', spine_y=0.84, bot=0.83,
         keyframes=[(t, _rad(a)) for t, a in S3_KEYFRAMES],
         note='perineal ring — outer'),
    # S4: perineal middle ring
    dict(label='S4', color='red', spine_y=0.835, bot=0.83,
         keyframes=[(t, _rad(a)) for t, a in S4_KEYFRAMES],
         note='perineal ring — middle'),
    # S5: perineal innermost ring
    dict(label='S5', color='red', spine_y=0.832, bot=0.83,
         keyframes=[(t, _rad(a)) for t, a in S5_KEYFRAMES],
         note='perineal ring — innermost'),
    # COCCYX LINE (THE SEAM) — pubic bone → inner leg → plantar
    dict(label='SEAM', color='red', spine_y=0.85, bot=0.04,
         keyframes=[(t, _rad(a)) for t, a in COCCYX_KEYFRAMES],
         foot=1.0, foot_angle=PI,
         note='ventral axial line / seam — pubic bone to plantar'),
]


def interp_keyframes(keyframes, t):
    """Interpolate angle from keyframe list at position t."""
    if t <= keyframes[0][0]:
        return keyframes[0][1]
    if t >= keyframes[-1][0]:
        return keyframes[-1][1]
    for i in range(len(keyframes) - 1):
        t0, a0 = keyframes[i]
        t1, a1 = keyframes[i + 1]
        if t0 <= t <= t1:
            frac = (t - t0) / (t1 - t0) if t1 != t0 else 0
            return lerp(a0, a1, frac)
    return keyframes[-1][1]


def build_spiral(d, side='R', steps=120):
    """Build smooth spiral polyline for one dermatome using keyframes."""
    pts = []
    sy = d['spine_y']
    by = d['bot']
    kf = d.get('keyframes', None)
    foot = d.get('foot', 0)
    fa = d.get('foot_angle', 0)
    ds = 1.0 if side == 'R' else -1.0

    # Origin on spine (posterior midline)
    _, r, sep, gl = prof_at(sy)
    pts.append((0.0, sy, r + gl + 0.005))

    LINE_OFFSET = 0.004  # 4mm above surface — clears glute mesh

    if kf:
        # Keyframe-based path (new accurate method)
        for s in range(1, steps + 1):
            t = s / steps
            cy = lerp(sy, by, t)
            angle = ds * interp_keyframes(kf, t)
            pts.append(body_surface(angle, cy, side, offset=LINE_OFFSET))
    else:
        # Legacy formula path (for trunk bands etc.)
        tgt = d.get('tgt', PI)
        te = d.get('tgt_end', tgt)
        for s in range(1, steps + 1):
            t = s / steps
            cy = lerp(sy, by, t)
            wrap = 1.0 - (1.0 - t) ** 3
            target = lerp(tgt, te, t)
            angle = ds * target * wrap
            pts.append(body_surface(angle, cy, side, offset=LINE_OFFSET))

    # Foot extension
    if foot > 0:
        for fs in range(1, 16):
            frac = (fs / 15) * foot
            pts.append(foot_ring(frac, ds * fa, side))

    return pts


# ══════════════════════════════════════════════════════
# OBJ GENERATION
# ══════════════════════════════════════════════════════
def write_obj(path):
    verts = []
    groups = []  # (name, material, vert_indices)

    # ── Reference ──
    verts.append((0, 0, 0))
    verts.append((0, 1.75, 0))

    # ── Body rings ──
    ring_n = 24
    body_ring_indices = []

    # Leg + torso rings (with glute bulge)
    for yi in range(16, 350, 5):  # y = 0.080 to 1.745 in 0.025 steps
        y = yi / 200.0
        _, r, sep, glute = prof_at(y)
        hsep = sep / 2.0

        if sep > 0.01:
            for side_sign, side_label in [(1, 'R'), (-1, 'L')]:
                ring = []
                for i in range(ring_n + 1):
                    a = 2 * PI * i / ring_n
                    posterior = max(0, math.cos(a))
                    ga = glute * posterior * posterior
                    x = side_sign * hsep + r * math.sin(a)
                    z = (r + ga) * math.cos(a)
                    verts.append((x, y, z))
                    ring.append(len(verts) - 1)
                body_ring_indices.append(ring)
        else:
            ring = []
            for i in range(ring_n + 1):
                a = 2 * PI * i / ring_n
                posterior = max(0, math.cos(a))
                ga = glute * posterior * posterior
                x = r * math.sin(a)
                z = (r + ga) * math.cos(a)
                verts.append((x, y, z))
                ring.append(len(verts) - 1)
            body_ring_indices.append(ring)

    # ── Foot rings ──
    foot_ring_indices = []
    for side in ['R', 'L']:
        for fi in range(11):
            frac = fi / 10.0
            ring = []
            for i in range(ring_n + 1):
                a = 2 * PI * i / ring_n
                pt = foot_ring(frac, a, side)
                verts.append(pt)
                ring.append(len(verts) - 1)
            foot_ring_indices.append(ring)

    # ── Arm rings ──
    arm_ring_indices = []
    for side in ['R', 'L']:
        for ai in range(21):
            t = ai / 20.0
            ring = []
            for i in range(ring_n + 1):
                a = 2 * PI * i / ring_n
                pt = arm_ring(t, a, side)
                verts.append(pt)
                ring.append(len(verts) - 1)
            arm_ring_indices.append(ring)

    # ── Dermatome spirals ──
    derm_groups = []
    for d in DERMATOMES:
        for side in ['R', 'L']:
            pts = build_spiral(d, side)
            start = len(verts)
            for p in pts:
                verts.append(p)
            end = len(verts) - 1
            derm_groups.append({
                'name': f"{d['label']}_{side}",
                'color': d['color'],
                'start': start,
                'end': end,
            })

    # ═══ VERTEBRAE — build geometry before writing ═══
    VERTEBRAE = [
        ('C1', 1.72), ('C2', 1.70), ('C3', 1.55), ('C4', 1.38),
        ('C5', 1.30), ('C6', 1.25), ('C7', 1.20),
        ('T1', 1.28), ('T2', 1.24), ('T3', 1.20), ('T4', 1.16),
        ('T5', 1.12), ('T6', 1.08), ('T7', 1.04), ('T8', 1.00),
        ('T9', 0.97), ('T10', 0.96), ('T11', 0.95), ('T12', 0.94),
        ('L1', 0.92), ('L2', 0.90), ('L3', 0.88), ('L4', 0.86), ('L5', 0.84),
        ('S1', 0.82), ('S2', 0.80), ('S3', 0.785), ('S4', 0.775), ('S5', 0.77),
    ]

    VS = 0.008
    vert_markers = []  # (name, oct_start_index)
    for vname, vy in VERTEBRAE:
        _, r_prof, _, gl = prof_at(vy)
        vz = r_prof + gl + 0.008  # place on top of glute surface
        cx, cy, cz = 0.0, vy, vz
        oct_start = len(verts)
        for dx, dy, dz in [(VS,0,0), (-VS,0,0), (0,VS,0), (0,-VS,0), (0,0,VS), (0,0,-VS)]:
            verts.append((cx+dx, cy+dy, cz+dz))
        vert_markers.append((vname, oct_start))

    # ═══ L/S connection lines ═══
    DISTAL = {
        'L1': dict(angle=_rad(210), y=0.78, foot=0,   fa=0),
        'L2': dict(angle=_rad(190), y=0.55, foot=0,   fa=0),
        'L3': dict(angle=_rad(180), y=0.48, foot=0,   fa=0),
        'L4': dict(angle=_rad(220), y=0.08, foot=0.7, fa=-PI/2),
        'L5': dict(angle=_rad(105), y=0.08, foot=0.9, fa=0),
        'S1': dict(angle=_rad(65),  y=0.08, foot=1.0, fa=PI/2),
        'S2': dict(angle=_rad(-90), y=0.48, foot=0,   fa=0),
    }

    connect_lines = []  # (label, side, start_idx, end_idx)
    for label, ep in DISTAL.items():
        vert_y = None
        for vn, vy in VERTEBRAE:
            if vn == label:
                vert_y = vy
                break
        if vert_y is None:
            continue

        _, r_spine, _, gl_spine = prof_at(vert_y)
        r_spine_back = r_spine + gl_spine  # include glute bulge

        for side in ['R', 'L']:
            ds = 1.0 if side == 'R' else -1.0
            start_i = len(verts)
            verts.append((0.0, vert_y, r_spine_back + 0.008))

            steps = 40
            for s in range(1, steps + 1):
                t = s / steps
                cy = lerp(vert_y, ep['y'], t)
                wrap = 1.0 - (1.0 - t) ** 3
                angle = ds * ep['angle'] * wrap
                verts.append(body_surface(angle, cy, side, offset=0.004))

            if ep['foot'] > 0:
                for fs in range(1, 11):
                    frac = (fs / 10) * ep['foot']
                    verts.append(foot_ring(frac, ds * ep['fa'], side))

            end_i = len(verts) - 1
            connect_lines.append((label, side, start_i, end_i))

    # ── Write OBJ — ALL verts collected, now write everything ──
    mtl_name = os.path.basename(path).replace('.obj', '.mtl')
    with open(path, 'w') as f:
        f.write(f"# Dermatome Mannequin — 1.75m scale\n")
        f.write(f"# Verts: {len(verts)} | Dermatomes: {len(derm_groups)}\n")
        f.write(f"mtllib {mtl_name}\n\n")

        # Write ALL vertices at once
        for v in verts:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

        # Helper: connect two rings into quad faces
        def write_faces(f, ring_list, group_name, mat_name):
            f.write(f"\n# ═══ {group_name} ═══\ng {group_name}\nusemtl {mat_name}\n")
            for ri in range(len(ring_list) - 1):
                r0 = ring_list[ri]
                r1 = ring_list[ri + 1]
                if len(r0) != len(r1):
                    continue
                n = len(r0) - 1
                for j in range(n):
                    f.write(f"f {r0[j]+1} {r0[j+1]+1} {r1[j+1]+1} {r1[j]+1}\n")

        # Body surfaces
        leg_R_rings = []
        leg_L_rings = []
        torso_rings = []
        ri = 0
        for yi in range(16, 350, 5):
            y = yi / 200.0
            _, r, sep, _ = prof_at(y)
            if sep > 0.01:
                leg_R_rings.append(body_ring_indices[ri]); ri += 1
                leg_L_rings.append(body_ring_indices[ri]); ri += 1
            else:
                torso_rings.append(body_ring_indices[ri]); ri += 1

        write_faces(f, leg_R_rings, 'Leg_R', 'body')
        write_faces(f, leg_L_rings, 'Leg_L', 'body')
        write_faces(f, torso_rings, 'Torso', 'body')

        foot_R = foot_ring_indices[:11]
        foot_L = foot_ring_indices[11:]
        write_faces(f, foot_R, 'Foot_R', 'body')
        write_faces(f, foot_L, 'Foot_L', 'body')

        arm_R = arm_ring_indices[:21]
        arm_L = arm_ring_indices[21:]
        write_faces(f, arm_R, 'Arm_R', 'body')
        write_faces(f, arm_L, 'Arm_L', 'body')

        # Vertebra markers
        f.write("\n# ═══ VERTEBRAE ═══\n")
        for vname, oct_start in vert_markers:
            f.write(f"\ng Vert_{vname}\nusemtl vert_marker\n")
            o = oct_start + 1
            for a, b, c in [
                (0,2,4), (0,4,3), (0,3,5), (0,5,2),
                (1,4,2), (1,3,4), (1,5,3), (1,2,5)
            ]:
                f.write(f"f {o+a} {o+b} {o+c}\n")

        # Connection lines
        f.write("\n# ═══ VERTEBRA → DISTAL CONNECTIONS ═══\n")
        for label, side, si, ei in connect_lines:
            f.write(f"\ng Connect_{label}_{side}\nusemtl {label.lower()}_connect\n")
            f.write("l " + " ".join(str(i + 1) for i in range(si, ei + 1)) + "\n")

        # Dermatome spirals
        f.write("\n# ═══ DERMATOME SPIRALS ═══\n")
        for dg in derm_groups:
            f.write(f"\ng {dg['name']}\nusemtl {dg['color']}\n")
            f.write("l " + " ".join(str(i + 1) for i in range(dg['start'], dg['end'] + 1)) + "\n")

    # ── Write MTL ──
    mtl_path = path.replace('.obj', '.mtl')
    with open(mtl_path, 'w') as f:
        mats = {
            'body':       (0.45, 0.45, 0.45),
            'lt_blue':    (0.55, 0.78, 0.95),
            'blue_dot':   (0.30, 0.50, 0.90),
            'red':        (0.95, 0.20, 0.20),
            'red_dot':    (0.90, 0.35, 0.35),
            'yellow':     (0.95, 0.88, 0.25),
            'pink':       (0.95, 0.55, 0.60),
            'vert_marker':(0.95, 0.95, 0.95),  # white vertebra markers
            # Connection line colors — match dermatome but brighter
            'l1_connect': (0.70, 0.88, 1.00),
            'l2_connect': (0.70, 0.88, 1.00),
            'l3_connect': (1.00, 0.50, 0.50),
            'l4_connect': (1.00, 0.95, 0.40),
            'l5_connect': (1.00, 0.95, 0.40),
            's1_connect': (1.00, 0.65, 0.70),
            's2_connect': (0.45, 0.65, 1.00),
        }
        for name, (r, g, b) in mats.items():
            f.write(f"newmtl {name}\nKd {r:.2f} {g:.2f} {b:.2f}\n\n")

    print(f"✓ {path}")
    print(f"✓ {mtl_path}")
    print(f"  Vertices: {len(verts)}")
    print(f"  Body rings: {len(body_ring_indices)}")
    print(f"  Foot rings: {len(foot_ring_indices)}")
    print(f"  Arm rings: {len(arm_ring_indices)}")
    print(f"  Dermatome lines: {len(derm_groups)}")
    print(f"\n  Open: https://3dviewer.net")


if __name__ == '__main__':
    write_obj(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dermatomes_mannequin.obj'))
