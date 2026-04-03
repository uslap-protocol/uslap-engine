# NEXT SESSION: Warp Cloth Wrap — Body Shape Fix

## WHAT WAS ESTABLISHED THIS SESSION

### Ruku Discovery
- **Ruku is the ONLY pose where ALL body warp lines run vertical** (perpendicular to floor)
- Ribs (horizontal in standing) hang vertically in ruku — torso tips 90°
- Documented in `RUKU_WARP_ALIGNMENT_DISCOVERY.md`

### Warp Architecture
- 11 warp lines per leg (Co + S5-S1 + L5-L1 = 11 vertebral levels)
- Each originates at its vertebra on the sacrum
- Each fans out, wraps around the pelvis bowl
- Each meets المِحْوَر الظَّهْرِي (stable conductor) at a DIFFERENT height
- Meeting points evenly distributed along the seam from hip to heel
- The stable conductor IS the seam line for clothing

### Clothing Discovery
- Cloth anchored at sacrum, wrapped around in ruku, seam = stable conductor
- ONE seam per leg (not 4 like modern trousers)
- Modern clothing cuts on cadaver/mannequin = wrong starting point

### Files Created
- `warp_cloth_wrap.html` — 3D cloth wrap viewer (HAS BUG)
- `warp_3d_viewer.html` — warp line viewer
- `warp_lines_illustration.html` — 2D SVG illustration
- `RUKU_WARP_ALIGNMENT_DISCOVERY.md` — full discovery document

## WHAT IS BROKEN

### bodyPt() function in warp_cloth_wrap.html
The function takes `(angle, y, side)` and ALWAYS produces two separate ellipses for R and L. This is wrong because:

1. **At pelvis level (y > 135)**: body is ONE continuous shape (peanut/oval)
2. **At crotch level (y ≈ 135)**: body pinches into figure-8
3. **Below crotch (y < 120)**: two separate leg shapes

Current code applies `side` offset at ALL heights. Need to rebuild as:

```
bodyPt(angle, y) — NO side parameter above crotch
```

### Cross-section should look like:
```
y=200 (waist):     one oval        ○
y=170 (pelvis):    wider oval      ⬭
y=140 (coccyx):    peanut          ∞ (with posterior indent)
y=135 (crotch):    figure-8        ∞ (pinching)
y=120 (thigh):     two lobes       ○ ○ (barely touching)
y=80 (mid-thigh):  two separate    ○   ○
y=0 (knee):        two smaller     ○   ○
y=-285 (heel):     two tiny        · ·
```

### Approach: Metaball / bi-lobe function
- Two circular lobes with centers that separate as y decreases
- At pelvis level: centers overlap = one merged shape
- Below crotch: centers separate = two distinct shapes
- Radius function r(y) for each lobe (tapers to ankle)
- Separation function sep(y) = 0 at waist, increases below crotch

### The warp ribbons
Once bodyPt is fixed, warp ribbons should work because they already use bodyPt to trace paths. The ribbons need to:
1. Start at vertebra (on the posterior midline at sacrum height)
2. Fan laterally along the pelvis surface
3. Wrap around the unified body surface (NOT crossing to the wrong side)
4. End at their meeting dot on the seam

### Ibn Sīnā / Lattice data used
- BA013: المِحْوَر الظَّهْرِي / al-miḥwar al-ẓahrī / stable conductor = THE SEAM
- BA016-017: الخَطّ البَطْنِي السُّفْلِي / ventral lower lines (the wrapped warps)
- BN006: المَفْصِل العَجُزِي الحَرْقَفِي / SI joint = keystone
- BN012: سِلْسِلَة التَّعْوِيض / compensation cascade = 7 stations along the seam
- Q23:14: فَكَسَوْنَا الْعِظَامَ لَحْمًا — flesh IS a garment (Allah's word, not Ibn Sīnā's)

### Key ATT terms
- عَجْب الذَّنَب / ʿajb al-dhanab / coccyx (origin of everything)
- المِحْوَر الظَّهْرِي / al-miḥwar al-ẓahrī / dorsal axial (stable conductor = seam)
- مَفْصِل الوَرِك / mafṣil al-warik / hip joint
- فَخِذ / fakhidh / femur
- عَقِب / ʿaqib / heel
- رُكْبَة / rukbah / knee
- كَاحِل / kāḥil / ankle
