---
# بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
# USLaP BATCH ENGINE PROTOCOL
## Implements QUF protocol per CLAUDE.md — do not duplicate rules here

---

## BATCH RUN 1 — FAILURE ANALYSIS

From batch run 1 (100 candidates, ~5 confirmed A1_ENTRIES):

| Failure | Root(s) affected | Cause |
|---------|-----------------|-------|
| S10 overuse | ر-و-د assigned to 11+ words | و→r(S10) and ر→r(S15) treated as equivalent |
| Root flooding | ش-ر-ك across 8+ words | No frequency cap |
| N15 blindness | ك-و-ن assigned to GRAIN, CROWN, CORN | C/G/K-R-N skeleton not detected |
| Semantic-first | SACRIFICE→ش-ر-ك (conceptual, not phonetic) | Meaning checked before consonants mapped |
| Score inflation | 8-9/10 for entries failing basic mapping | No calibrated scoring gate |
| OP_PREFIX missed | M- words not tested for مُ prefix | R08 not implemented |
| Root transposition missed | ش-ر-ك not tested as ش-ك-ر | R02 not implemented |

---

## REQUIRED ALGORITHM GATES (implement in this order)

### GATE 0 — SUFFIX STRIP (before any analysis)
Strip ALL downstream suffixes before extracting consonants:
- Latin: -tion, -ment, -ary, -ory, -ous, -ness, -ity, -al, -ic, -ist, -ism, -ize, -ure, -ance, -ence, -ion
- Greek: -ology, -ography, -onomy, -osis, -oma, -sis
- Germanic: -ing, -ness, -ful, -less, -ward, -ship, -hood
Only analyse the stripped stem. Never analyse the full word including suffixes.

### GATE 1 — CONSONANT EXTRACTION (mandatory first step)
Extract consonants from stripped stem. Vowels are NOT root letters.
Mark each consonant with its position (C1, C2, C3...).
This list is the ONLY input to Gates 2-5. No meaning at this stage.

### GATE 2 — QURANIC CHECK (before phonetic mapping)
Query USLaP_Quran_Root_Count.xlsx ROOT_LIST for proposed root.
- ROOT NOT IN QUR'AN → score cap 7, flag PENDING_REVIEW, do not map further
- ROOT IN QUR'AN → record token count, proceed to Gate 3

**TWO-TRACK Q-GATE (updated):**
GATE 2 now runs two tracks before declaring failure:
- Track A: ROOT_LIST (USLaP_Quran_Root_Count.xlsx) — PASS → ORIG1, continue
- Track B: if ROOT_LIST FAIL → query Kashgari corpus (Dankoff & Kelly digital edition) for consonant skeleton — PASS → ORIG2 entry, route to BITIG_A1_ENTRIES
- Only if BOTH fail → cap score at 7, flag as UNDER_INVESTIGATION

**BITIG RULES FOR BATCH PROCESSING (B01–B07):**
Before tagging any entry as ORIG2, the engine must check:
- B01: Does the candidate contain /f/? If yes → foreign contamination flag, re-examine
- B02: Are pharyngeals (ح, ع, خ, غ) present in the proposed Bitig root? If yes → suspect ORIG1 bleed-through, run R01
- B03: Strip Bitig suffixes before tracing: -lı/-li, -lar/-ler, -da/-de, -gan/-gen, -mak/-mek
- B04: Vowel harmony shifts are NOT U-gate failures for ORIG2 entries
- B05: /w/ in candidate → re-examine as ORIG1 (و/wāw)
- B06: Kashgari citation (page/line) required — "sounds Turkic" is rejected
- B07: Semantic alignment with Qur'anic framework required (not derivation, alignment)

**R11 — Transposition as Semantic-First Diagnostic (add to engine validation):**
After any root candidate is proposed, run R11 check:
- Extract consonant ORDER from the English word (strip vowels, strip suffix, read positions left→right)
- Compare to proposed root's consonant order
- If proposed root has same consonants but DIFFERENT order → semantic-first detected (R10+R11 conjunction)
- Run R02 (Root Transposition Check): try all 6 permutations of the consonants
- The transposition is not coincidence — it is the fingerprint of the engine reading concepts, not phonemes
- Example: SACRIFICE consonant order S(1)-K(2)-R(3) → ش-ك-ر. Engine proposed ش-ر-ك (S-R-K), transposing positions 2 and 3. K-R swap = semantic-first proof.

### GATE 3 — CONSONANT MAPPING (QUF U-gate)
Map every consonant from Gate 1 to an Arabic letter via M1 shift table (S01-S26).
- ALL consonants must map. If ANY consonant is unmapped → FAIL → AUTO_REJECTED
- Generate chain string: "ق→K(S01), س→S(S21), م→M(S17)"
- If chain string cannot be generated → AUTO_REJECTED
- Note: vowels between consonants are NOT required to map

### GATE 3a — S10 DISCRIMINATOR (fires when و→r is used)
If any mapping uses و→r (S10) for an English "r":
- Check: does at least ONE other consonant independently confirm this root?
- If و→r is the SOLE link to this root → FLAG_S10_UNSUPPORTED → PENDING_REVIEW (not auto-fail)
- Log: "S10_UNSUPPORTED: only connection is و→r, no corroborating consonant"

### GATE 3b — N15 SKELETON DETECTOR (fires before general root assignment)
Check consonant skeleton against known high-confidence patterns BEFORE general algorithm:
```
[c/g/k] + [r] + [n/m] → FORCE test ق-ر-ن (R133, N15) first
[m] + [r] + [j/y] → FORCE test م-ر-ج (R102) first  
[m] + [v/w] + [t] → FORCE test م-و-ت (R103) first
[s/z] + [l] + [m] → FORCE test س-ل-م (SALAMA, high frequency) first
```
If skeleton matches and Q-gate passes for the forced root → assign that root.
Only if forced root fails → proceed to general algorithm.

### GATE 3c — OP_PREFIX CHECK (fires for M- words)
If English word begins with M-:
1. Strip M from start of word
2. Re-extract consonants from remainder
3. Run Gates 2-3 on remainder
4. If Q-gate passes AND all remaining consonants map → output BOTH:
   - Full word (M- included, mapped as مُ OP_PREFIX)
   - Note: "OP_PREFIX candidate: مُ + [root]"

### GATE 4 — ROOT TRANSPOSITION (fires when Gate 3 fails)
When Gate 3 fails but ALL THREE consonants are present in M1 for some root:
1. Generate all 6 permutations of the three consonant letters
2. For each permutation: check Q-gate (Gate 2)
3. If any permutation passes Q-gate AND maps all consonants → output:
   "TRANSPOSITION_CANDIDATE: [failed root] → [passing permutation]"
4. Do not auto-assign — flag for human review

### GATE 5 — ROOT FREQUENCY CAP
After each batch completes, count how many times each root was assigned:
- Root count > 5 in a 100-word batch → FLAG_OVERUSE → ALL instances of that root go to PENDING_REVIEW
- Root count > 10 → flag as ENGINE_MISFIRE for that root cluster → all instances auto-moved to PENDING_REVIEW with note "root overuse detected"

---

## SCORING CALIBRATION

| Score | Conditions | Output tier |
|-------|------------|-------------|
| 10/10 | All consonants map + Q-gate 5+ tokens + semantic clear + Foundation layer + chain string generated + no competing root | CONFIRMED_HIGH |
| 9/10 | All above but Q-gate 2-4 tokens OR one documented OP_ used | CONFIRMED_HIGH |
| 8/10 | All consonants map + Q-gate passes (any tokens) + semantic plausible + chain string generated | CONFIRMED_HIGH |
| 7/10 | Consonants map but one requires undocumented operation OR Q-gate 1 token | PENDING_REVIEW |
| 6/10 | Two+ consonants need uncommon operations OR semantic chain needs explanation | PENDING_REVIEW |
| 5/10 | Skeleton matches but one consonant unmapped OR S10_UNSUPPORTED | PENDING_REVIEW |
| <5/10 | Any consonant unmapped, Q-gate fails, or chain string not generatable | AUTO_REJECTED |

Expected yield from a calibrated batch of 100:
- 15-25 CONFIRMED_HIGH (scores 8-10)
- 20-30 PENDING_REVIEW (scores 5-7)
- 50-60 AUTO_REJECTED (scores <5)
If CONFIRMED_HIGH > 40 in 100 words: scoring is inflated. Review calibration.

---

## OUTPUT FILE STRUCTURE (three files, not one)

```
BATCH_OUTPUT_[DATE]/
├── CONFIRMED_HIGH.xlsx    — scores 8-10, all gates passed, chain logged, ready for bbi review
├── PENDING_REVIEW.xlsx    — scores 5-7, needs human judgment
└── AUTO_REJECTED.txt      — scores <5, one line per word with rejection reason
```

AUTO_REJECTED.txt format per line:
```
WORD | PROPOSED_ROOT | GATE_FAILED | DETAIL
REVOLUTION | ر-و-د | GATE_3a_S10 | و→r sole mapping; root appeared 11x in batch (GATE_5_OVERUSE)
SACRIFICE | ش-ر-ك | GATE_4_TRANSPOSITION | try ش-ك-ر (R02) before rejecting
GRAIN | ك-و-ن | GATE_3b_N15 | C/G/K-R-N skeleton → should test ق-ر-ن first
```

---

## KNOWN SKELETON PATTERNS (update as lattice grows)

| English skeleton | Likely root | Network | Priority |
|-----------------|-------------|---------|----------|
| [c/g/k]-R-N | ق-ر-ن (R133) | N15 | HIGH |
| M-R-[j/y/ch] | م-ر-ج (R102) | N08 | HIGH |
| M-[v/w]-T | م-و-ت (R103) | — | HIGH |
| S-[l]-M | س-ل-م (R4) | — | HIGH |
| [k/g]-[s/z]-M | ق-س-م (R86) | — | HIGH — check KISMET/COSMOS |
| N-[s/z]-R | ن-ص-ر (R159) | — | HIGH |

---

## REFERENCES
- QUF protocol: CLAUDE.md sections QUF GATE + M1 PHONETIC SHIFTS
- Permitted operations (OP_NASAL, OP_STOP etc.): CLAUDE.md PERMITTED OPERATIONS table
- Analytical rules (R01-R10): CLAUDE.md ANALYTICAL RULES (R-SERIES)
- AI validation: USLaP_AI_VALIDATION_PROTOCOL.md
