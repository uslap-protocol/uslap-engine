#!/usr/bin/env python3
"""
Generate a 3D mannequin in RUKŪʿ pose with dermatome lines.
Uses the same body geometry as generate_dermatomes.py but bends
the trunk 90° forward at the hip joint.

The hip pivot = the XY intersection = the lateral hip (greater trochanter).
Everything above the hip rotates 90° forward.
Everything below stays vertical.

In rukūʿ: ALL dermatome lines align vertically.
T11/T12 (horizontal in standing) become vertical.
L5 (already vertical) stays vertical.
"""
import math, os, sys

# Import everything from the standing generator
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from generate_dermatomes import (
    PI, lerp, smoothstep, prof_at, body_surface, foot_ring,
    arm_ring, arm_center, arm_r,
    PROFILE, CROTCH_Y, BLEND_TOP, BLEND_BOT,
    FOOT_LEN, ANKLE_Y, ARM_LEN, SHOULDER_Y, SHOULDER_X,
    L4_KEYFRAMES, L5_KEYFRAMES, S1_KEYFRAMES, S2_KEYFRAMES,
    L1_KEYFRAMES, L2_KEYFRAMES, L3_KEYFRAMES,
    COCCYX_KEYFRAMES, S3_KEYFRAMES, S4_KEYFRAMES, S5_KEYFRAMES,
    DERMATOMES,
    interp_keyframes, build_spiral, _rad,
)

# ═══════════════════════════════════════════
# RUKŪʿ TRANSFORMATION
# Pivot: hip joint at y = HIP_Y
# Above hip: rotate 90° forward (around X axis)
# Below hip: stay as-is
# ═══════════════════════════════════════════
HIP_Y = 0.850  # pivot height

def ruku_transform(x, y, z):
    """Transform a standing-pose point into rukūʿ pose.
    Below HIP_Y: unchanged (legs stay vertical).
    Above HIP_Y: rotate 90° forward around X-axis at hip level.

    Standing: spine along +Y, back at +Z, belly at -Z.
    Rukūʿ trunk: spine along -Z (forward), back at +Y (up), belly at -Y (down).

    Rotation (relative to hip): (dy, dz) → (dz, -dy)
    - dy = y - HIP_Y (height above hip)
    - dz = z (depth: + = posterior/back, - = anterior/belly)
    - new_y = HIP_Y + dz  (back goes UP, belly goes DOWN)
    - new_z = -dy  (height becomes forward reach)
    """
    if y <= HIP_Y:
        return (x, y, z)

    dy = y - HIP_Y
    new_y = HIP_Y + z    # depth → height (back=up, belly=down)
    new_z = -dy           # height → forward (-Z)
    return (x, new_y, new_z)


def write_ruku_obj(path):
    """Generate the standing mannequin, then transform all vertices into rukūʿ."""

    # ── First, generate all standing geometry (same as generate_dermatomes.py) ──
    verts_standing = []
    groups = []

    ring_n = 24

    # Body rings
    body_ring_indices = []
    for yi in range(16, 350, 5):
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
                    verts_standing.append((x, y, z))
                    ring.append(len(verts_standing) - 1)
                body_ring_indices.append(ring)
        else:
            ring = []
            for i in range(ring_n + 1):
                a = 2 * PI * i / ring_n
                posterior = max(0, math.cos(a))
                ga = glute * posterior * posterior
                x = r * math.sin(a)
                z = (r + ga) * math.cos(a)
                verts_standing.append((x, y, z))
                ring.append(len(verts_standing) - 1)
            body_ring_indices.append(ring)

    # Foot rings
    foot_ring_indices = []
    for side in ['R', 'L']:
        for fi in range(11):
            frac = fi / 10.0
            ring = []
            for i in range(ring_n + 1):
                a = 2 * PI * i / ring_n
                pt = foot_ring(frac, a, side)
                verts_standing.append(pt)
                ring.append(len(verts_standing) - 1)
            foot_ring_indices.append(ring)

    # Arm rings
    arm_ring_indices = []
    for side in ['R', 'L']:
        for ai in range(21):
            t = ai / 20.0
            ring = []
            for i in range(ring_n + 1):
                a = 2 * PI * i / ring_n
                pt = arm_ring(t, a, side)
                verts_standing.append(pt)
                ring.append(len(verts_standing) - 1)
            arm_ring_indices.append(ring)

    # Dermatome spirals
    derm_groups = []
    for d in DERMATOMES:
        for side in ['R', 'L']:
            pts = build_spiral(d, side)
            start = len(verts_standing)
            for p in pts:
                verts_standing.append(p)
            end = len(verts_standing) - 1
            derm_groups.append({
                'name': f"{d['label']}_{side}",
                'color': d['color'],
                'start': start,
                'end': end,
            })

    # ── Now transform ALL vertices into rukūʿ ──
    verts_ruku = [ruku_transform(x, y, z) for x, y, z in verts_standing]

    # ── Write OBJ ──
    mtl_name = os.path.basename(path).replace('.obj', '.mtl')
    with open(path, 'w') as f:
        f.write(f"# Dermatome Mannequin — RUKŪʿ POSE\n")
        f.write(f"# Hip pivot at y={HIP_Y}. Trunk rotated 90° forward.\n")
        f.write(f"# ALL dermatome lines align vertically.\n")
        f.write(f"# Verts: {len(verts_ruku)}\n")
        f.write(f"mtllib {mtl_name}\n\n")

        for v in verts_ruku:
            f.write(f"v {v[0]:.6f} {v[1]:.6f} {v[2]:.6f}\n")

        # Faces — same connectivity as standing, just vertices moved
        def write_faces(f, ring_list, group_name, mat_name):
            f.write(f"\ng {group_name}\nusemtl {mat_name}\n")
            for ri in range(len(ring_list) - 1):
                r0 = ring_list[ri]
                r1 = ring_list[ri + 1]
                if len(r0) != len(r1): continue
                n = len(r0) - 1
                for j in range(n):
                    f.write(f"f {r0[j]+1} {r0[j+1]+1} {r1[j+1]+1} {r1[j]+1}\n")

        # Body surfaces
        leg_R, leg_L, torso = [], [], []
        ri = 0
        for yi in range(16, 350, 5):
            y = yi / 200.0
            _, r, sep, _ = prof_at(y)
            if sep > 0.01:
                leg_R.append(body_ring_indices[ri]); ri += 1
                leg_L.append(body_ring_indices[ri]); ri += 1
            else:
                torso.append(body_ring_indices[ri]); ri += 1

        write_faces(f, leg_R, 'Leg_R', 'body')
        write_faces(f, leg_L, 'Leg_L', 'body')
        write_faces(f, torso, 'Torso', 'body')

        foot_R = foot_ring_indices[:11]
        foot_L = foot_ring_indices[11:]
        write_faces(f, foot_R, 'Foot_R', 'body')
        write_faces(f, foot_L, 'Foot_L', 'body')

        arm_R = arm_ring_indices[:21]
        arm_L = arm_ring_indices[21:]
        write_faces(f, arm_R, 'Arm_R', 'body')
        write_faces(f, arm_L, 'Arm_L', 'body')

        # Dermatome spirals
        f.write("\n# ═══ DERMATOME SPIRALS ═══\n")
        for dg in derm_groups:
            f.write(f"\ng {dg['name']}\nusemtl {dg['color']}\n")
            f.write("l " + " ".join(str(i + 1) for i in range(dg['start'], dg['end'] + 1)) + "\n")

    # MTL (same as standing)
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
            'vert_marker':(0.95, 0.95, 0.95),
        }
        for name, (r, g, b) in mats.items():
            f.write(f"newmtl {name}\nKd {r:.2f} {g:.2f} {b:.2f}\n\n")

    print(f"✓ {path}")
    print(f"✓ {mtl_path}")
    print(f"  Verts: {len(verts_ruku)}")
    print(f"  Hip pivot: y={HIP_Y}")
    print(f"\n  Open: https://3dviewer.net or 3dview.org")


if __name__ == '__main__':
    write_ruku_obj(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'dermatomes_ruku.obj'))
