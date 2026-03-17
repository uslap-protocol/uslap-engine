---
# بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ
# USLaP AI VALIDATION PROTOCOL
## How to use any AI for USLaP work while preventing protocol violation

---

## WHY OTHER AIs FAIL

All major AI systems (GPT, DeepSeek, Gemini, Mistral, etc.) are trained on Western academic data — Wikipedia, academic papers, etymological databases. This training data IS the material USLaP refutes. Without intervention, any AI will:
- Apply semantic-first mapping (meaning before consonants)
- Cite Western etymological sources as authoritative  
- Use banned terms (PIE, cognate, loanword, Semitic)
- Score entries 8-9/10 for chains that fail basic consonant mapping
- Revert to Western frameworks as context window fills

---

## FIVE-LAYER ENFORCEMENT SYSTEM

### Layer 1 — Session Opening Protocol (mandatory for any AI session)
Paste verbatim at session start, before ANY other instruction:

```
MANDATORY USLaP OPERATING RULES — read and acknowledge before proceeding:

1. DIRECTION: Allah's Arabic is the origin. All languages are downstream. 
   NEVER reverse the direction. NEVER write "Arabic borrowed from Greek/Latin/Persian."

2. BANNED: PIE, Proto-Indo-European, Semitic, cognate, loanword, "borrowed from [any language]"
   Any of these = stop and restate without them.

3. FOR EVERY WORD — this order, always:
   a. Strip suffixes (-tion, -ment, -ary, -ous, -ology etc.)
   b. Extract consonants from remainder only
   c. Map consonants to Arabic letters using M1 shift table (S01-S26)
   d. Check mapped root in Qur'an — cite the exact verse and token count
   e. Only THEN check semantic coherence

4. OUTPUT FORMAT — every entry must include:
   - Arabic word with full diacritics / transliteration / English meaning
   - Phonetic chain: every consonant mapped with S-ID (e.g. ق→K(S01))
   - Qur'anic verse (surah:ayah number, token count)
   - One sentence: what would disprove this chain

5. FAILURE CONDITIONS — auto-reject if:
   - Any English consonant appears in the word but is missing from the chain
   - The chain cannot be written
   - The root is not in the Qur'an (no score above 7)
   - A Western source is cited as origin confirmation

Confirm you have read and understood these rules. State the last ENTRY_ID 
and ROOT_ID from the lattice before proceeding with any analysis.
```

### Layer 2 — The Chain Test (after every proposed entry)
Ask the AI: "Write the phonetic chain for this entry. Format: X→Y(S_ID) for every consonant."
- If it produces the chain → check every consonant manually against M1 table
- If ANY English consonant is missing from the chain → reject the entry
- If it cannot produce the chain → reject the entry

This test does not require the AI to understand USLaP philosophy. It either maps every consonant or it doesn't.

### Layer 3 — The Falsifiability Test (after chain is verified)
Ask: "What evidence would disprove this phonetic chain?"
- If answer is "nothing" or vague → F-gate failed → reject
- If answer is specific (e.g. "if ق cannot produce K through documented S01 shift") → F-gate passes

### Layer 4 — Validation Pass (never write AI output directly to lattice)
ALL AI-generated entries — from DeepSeek, Cline, other Claude instances, any AI — must pass through a validation session where CLAUDE.md is loaded. The validating session:
- Is author-blind (does not care which AI produced the entry)
- Runs QUF on every entry
- Rejects any entry that fails any gate
- May suggest corrections (transposition, OP_PREFIX etc.) before final decision

NO AI OUTPUT GOES DIRECTLY TO THE LATTICE.

### Layer 5 — Batch Frequency Audit (after any batch run)
After any AI produces multiple entries, run the frequency audit:
- List every proposed root and how many times it appears
- Any root appearing > 5 times in a 100-word batch → manual review of ALL instances
- Any root appearing > 10 times → flag as AI misfire, discard entire cluster

---

## SESSION LENGTH MANAGEMENT

AI context windows fill. When instructions scroll out of active context:
- The AI reverts to training data (Western frameworks)
- Quality degrades after approximately 15-20 exchanges

SOLUTION: Structure sessions as short bursts.
- Maximum 10-15 entries per session
- Re-paste Layer 1 protocol at the start of every session (not every exchange)
- End session and start new one when quality begins to drop

---

## AI-SPECIFIC NOTES

| AI | Failure pattern | Mitigation |
|----|----------------|------------|
| DeepSeek | Good phonetic tracing, reverts to Western source citation | Layer 1 + explicitly ban citing Wiktionary/Etymonline/Beekes in the opening prompt |
| Cline | Follows file operations accurately, may not apply QUF | Use Cline ONLY for file writes, never for linguistic analysis |
| Other Claude instances | Same training data bias, but responds well to CLAUDE.md | Load CLAUDE.md as context, use Layer 2-3 checks |
| GPT-class | Strongest Western framework bias | Layers 1-5 all required; re-paste Layer 1 every 10 exchanges |

---

## GOLD STANDARD OUTPUTS

Use these confirmed entries as calibration examples when testing any AI:
- SACRIFICE: S-A-C-R-I-F-I-C-E → strip -ICE(OP_SUFFIX) → SACRIF → strip S(OP_PREFIX?) → ACRIF → ش-ك-ر via S-ب, C-ك, R-ر. Wait — correct trace: ش→S(S05), ك→C(S20), ر→R(S15). Chain: ش→S(S05), ك→K(S20), ر→R(S15). Root ش-ك-ر (shukr/gratitude, Q2:152). NOT ش-ر-ك.
- MIRACLE: M-I-R-A-C-L-E → strip مُ(OP_PREFIX) → R-C-L → ر→R(S15), ر-س-ل with س→C(S21), ل→L(S16). Chain: [مُ→M(OP_PREFIX)], ر→R(S15), س→C(S21), ل→L(S16). Root ر-س-ل (rasala/prophethood, Q13:38).
- GRAIN: G-R-A-I-N → G-R-N skeleton → N15 check first → ق-ر-ن (R133). Chain: ق→G(S14/S01), ر→R(S15), ن→N(S18). NOT ك-و-ن.

If an AI produces incorrect traces for these known entries, its output for the current session is unreliable. Restart with Layer 1 protocol.

---

## REFERENCES
- Master protocol: CLAUDE.md
- Batch engine rules: USLaP_BATCH_ENGINE_PROTOCOL.md
- M1 shift table: CLAUDE.md section M1 PHONETIC SHIFT TABLE
- Analytical rules R01-R10: CLAUDE.md section ANALYTICAL RULES (R-SERIES)
