# NEXT SESSION — خُطُوط ابن سينا Full Body Animation

## IMMEDIATE FIX NEEDED
**Fan phase bug**: L1, L2, L3 ribbons wrap around the OUTSIDE of the body surface to reach the anterior/medial side. This makes them APPEAR to start on the belly.
**Fix**: The fan phase should interpolate in a STRAIGHT LINE through the body interior (spine → target surface position), NOT follow the body surface. The straight-line path goes through the body fill and is naturally hidden. Only the surface descent portion (the visible vertical strip) shows.

In `buildRibbon()`, the fan section at line ~457:
```javascript
// CURRENT (WRONG): follows body surface
key.push(legPt(fanAngle, fanY, side));

// FIX: straight-line interpolation through interior
const tgtPt = legPt(dir * tgtAngle, originY - fanDrop, side);
key.push({
  x: origin.x + (tgtPt.x - origin.x) * t,
  y: origin.y + (tgtPt.y - origin.y) * t,
  z: origin.z + (tgtPt.z - origin.z) * t
});
```

## STATUS
- File: `Prayer_Animations/warp_cloth_wrap.html`
- Backup: `warp_cloth_wrap_v2_ibn_sina_khutut.html`
- Server config: `.claude/launch.json` → `prayer-anim` on port 8765

## Ibn Sīnā's Terminology (MANDATORY — ATT format)
| Term | Arabic | Transliteration | Translation |
|------|--------|-----------------|-------------|
| THE SEAM | المِحْوَر الظَّهْرِي | al-miḥwar al-ẓahrī | dorsal axial line |
| FORCE LINES (plural) | خُطُوط | khuṭūṭ | lines |
| FORCE LINE (singular) | خَطّ | khaṭṭ | line |
| VENTRAL UPPER | الخَطّ البَطْنِي العُلْوِي | al-khaṭṭ al-baṭnī al-ʿulwī | ventral upper line |
| VENTRAL LOWER | الخَطّ البَطْنِي السُّفْلِي | al-khaṭṭ al-baṭnī al-suflī | ventral lower line |
| CONTRALATERAL | الجَانِب المُقَابِل | al-jānib al-muqābil | the opposite side |
| NERVE | عَصَب | ʿaṣab | nerve |
| BELT-ZONE ANT | نَمْلَة مِنْطَقِيَّة | namla mintaqiyya | shingles (living proof of strips) |

## Angular Assignments (from criminal illustration — NEEDS CLEAN DERIVATION)
The `tgt` values in the VERT table came from the criminal illustration, NOT from Ibn Sīnā.
They are PROBABLY correct (same pattern observable in living patients) but need clean sourcing.
**NEXT SESSION**: dig into al-Qānūn Book III to find Ibn Sīnā's descriptions of which nerve serves which body region. Derive the angles from his clinical text. If his descriptions match the current angles → confirmed clean. If they differ → adjust.

Current tgt values:
- L1: PI+0.7 (medial/groin) — observable: L1 compression → groin numbness
- L2: PI+0.3 (anterior-medial) — observable: L2 → anterior thigh
- L3: PI (anterior) — observable: L3 → front of knee
- L4: PI*0.7 (anterior-lateral) — observable: L4 → medial shin
- L5: PI/2 (lateral) — observable: L5 → lateral leg (most common sciatica)
- S1: 1.1 (lateral-posterior) — observable: S1 → posterior calf
- S2: 0.7 (posterior-lateral) — observable: S2 → posterior thigh
- S3-Co: 0.45→0.04 (posterior/seam) — observable: perineal region

## Architecture Summary
- 11 خُطُوط (L1→Co), each at target angle, vertical strips
- Spinal S-curve: lumbar lordosis (L3 deepest) → sacral kyphosis (S3 peak)
- Solid opaque body, two-sided coloring (purple outer / black inner)
- Per-vertebra toggle buttons
- Ruku ↔ Qiyam: smooth animation + gravity drape + elastic contraction
- Ribbon-aligned slicing (body-relative)
- poseT: smooth blend zone (±40 units), gravity drape (92% collapse), elastic contraction (45% at crease)
- setInterval fallback for animation (rAF pauses in preview tool)

## Full Body Extension Plan
1. Fix fan phase (straight-line interior path)
2. Find Ibn Sīnā's nerve descriptions in al-Qānūn Book III → clean derivation of angles
3. Add TORSO: T1-T12 as خُطُوط (ribs = the thoracic force lines)
4. Add ARMS: الخَطّ البَطْنِي العُلْوِي (ventral upper lines)
5. Cross-bracing: الجَانِب المُقَابِل
6. All prayer positions with elasticity:
   - قِيَام (standing) — baseline vertical alignment
   - رُكُوع (bowing) — loads dorsal + ventral simultaneously, all خُطُوط → vertical
   - سُجُود (prostration) — maximum spinal flexion, face to ground
   - جُلُوس (sitting) — hip + knee flexion, different stress pattern
7. Each position demonstrates different خُطُوط alignment

## CRITICAL RULES
- NEVER use criminal anatomy terminology (dermatome, etc.)
- Ibn Sīnā's terms ONLY, ATT format
- Living observation derivation — no cadaver sources
- Source: BODY_ARCHITECTURE sheet in lattice, Ibn Sīnā SC02
- All data in lattice: check before generating fresh

## Lattice Entries Written This Session
- Chronology: C126-C136 (cadaver crime timeline)
- Body Extraction Intel: EX030-EX054 (crime industry + namla)
- Mortality Intelligence: MI09-MI16 (burial law + Qur'anic)
- DP Register: DP09-CSI (Cadaver Science Inversion)
