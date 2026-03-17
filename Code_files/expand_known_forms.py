#!/usr/bin/env python3
"""
Phase 1C: Expand quran_known_forms from 255 to 3,000+
Auto-maps unrooted Qur'anic word forms to roots using:
1. Manual curated mappings for high-frequency complex forms
2. Algorithmic extraction with dictionary verification for the rest
"""

import sqlite3
import re
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "uslap_database_v3.db")

DIACRITICS = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06DC\u06DF-\u06E8\u06EA-\u06ED]')
ALEF_VARIANTS = re.compile(r'[إأآٱ]')
HAMZA_CARRIERS = re.compile(r'[ؤئ]')

def strip_bare(word):
    """Strip to bare form for known_forms matching."""
    text = word
    text = text.replace('\u0671', 'ا')  # wasla
    text = text.replace('\u06E5', '')    # small waw
    text = text.replace('\u06E6', '')    # small yaa
    text = text.replace('\u0654', 'ء')   # hamza above
    text = HAMZA_CARRIERS.sub('ء', text)
    text = text.replace('آ', 'اء')
    text = DIACRITICS.sub('', text)
    text = text.replace('\u0640', '')    # tatweel
    text = text.replace('\u200D', '').replace('\u200C', '')
    text = ALEF_VARIANTS.sub('ا', text)
    text = text.replace('\u0649', 'ي')   # alef maksura → yaa
    return text


# ═══════════════════════════════════════════════════════════════
# MANUAL CURATED MAPPINGS — complex forms that need human judgment
# Format: bare_form → (root_unhyphenated, word_type, verb_form)
# ═══════════════════════════════════════════════════════════════

CURATED = {
    # ── ء-ي-ي (أيي) family: signs, verses ──
    'بايتنا': ('أيي', 'NOUN', None),
    'بايت': ('أيي', 'NOUN', None),
    'لايت': ('أيي', 'NOUN', None),
    'الايت': ('أيي', 'NOUN', None),
    'لاية': ('أيي', 'NOUN', None),
    'ءايته': ('أيي', 'NOUN', None),
    'بايتنا': ('أيي', 'NOUN', None),
    'باية': ('أيي', 'NOUN', None),
    'ايته': ('أيي', 'NOUN', None),
    'وايته': ('أيي', 'NOUN', None),
    'وايتنا': ('أيي', 'NOUN', None),
    'فايتنا': ('أيي', 'NOUN', None),
    'ايتنا': ('أيي', 'NOUN', None),
    'اية': ('أيي', 'NOUN', None),
    'وايت': ('أيي', 'NOUN', None),
    'ءاية': ('أيي', 'NOUN', None),
    'لايتنا': ('أيي', 'NOUN', None),

    # ── ق-و-م family: standing, straight ──
    'مستقيم': ('قوم', 'NOUN', 'X'),
    'مستقيما': ('قوم', 'NOUN', 'X'),
    'يستقيم': ('قوم', 'VERB', 'X'),
    'استقم': ('قوم', 'VERB', 'X'),
    'استقاموا': ('قوم', 'VERB', 'X'),
    'قوة': ('قوي', 'NOUN', None),

    # ── و-ق-ي family: protect, be conscious ──
    'تتقون': ('وقي', 'VERB', 'VIII'),
    'اتقوا': ('وقي', 'VERB', 'VIII'),
    'اتقي': ('وقي', 'VERB', 'VIII'),
    'يتقون': ('وقي', 'VERB', 'VIII'),
    'المتقين': ('وقي', 'NOUN', 'VIII'),

    # ── و-ل-ي family: close, govern, turn ──
    'تولوا': ('ولي', 'VERB', 'V'),
    'تولي': ('ولي', 'VERB', 'V'),
    'يتولى': ('ولي', 'VERB', 'V'),
    'توليهم': ('ولي', 'VERB', 'V'),
    'اولياء': ('ولي', 'NOUN', None),
    'اوليائه': ('ولي', 'NOUN', None),
    'اوليائهم': ('ولي', 'NOUN', None),
    'واوليائه': ('ولي', 'NOUN', None),

    # ── ر-و-د family: seek, intend ──
    'اراد': ('رود', 'VERB', 'IV'),
    'ارادوا': ('رود', 'VERB', 'IV'),
    'اردنا': ('رود', 'VERB', 'IV'),
    'اردتم': ('رود', 'VERB', 'IV'),
    'يريد': ('رود', 'VERB', 'IV'),
    'يريدون': ('رود', 'VERB', 'IV'),
    'تريدون': ('رود', 'VERB', 'IV'),
    'نريد': ('رود', 'VERB', 'IV'),
    'مريد': ('رود', 'NOUN', None),

    # ── ن-و-ر / ن-ا-ر family: light, fire ──
    'نارا': ('نور', 'NOUN', None),
    'النار': ('نور', 'NOUN', None),
    'نار': ('نور', 'NOUN', None),

    # ── ي-و-م family: day ──
    'ايام': ('يوم', 'NOUN', None),
    'ايامه': ('يوم', 'NOUN', None),
    'ايامها': ('يوم', 'NOUN', None),

    # ── م-ل-ك family: king, angel, possess ──
    'الملائكة': ('ملك', 'NOUN', None),
    'الملءكة': ('ملك', 'NOUN', None),
    'ملائكة': ('ملك', 'NOUN', None),
    'ملءكة': ('ملك', 'NOUN', None),
    'ملائكته': ('ملك', 'NOUN', None),
    'الملك': ('ملك', 'NOUN', None),

    # ── خ-و-ف family: fear ──
    'اخاف': ('خوف', 'VERB', None),
    'خافوا': ('خوف', 'VERB', None),
    'يخافون': ('خوف', 'VERB', None),
    'تخافون': ('خوف', 'VERB', None),
    'تخاف': ('خوف', 'VERB', None),

    # ── ن-ب-أ family: prophet, news ──
    'النبي': ('نبأ', 'NOUN', None),
    'النبيين': ('نبأ', 'NOUN', None),
    'نبيا': ('نبأ', 'NOUN', None),
    'نبي': ('نبأ', 'NOUN', None),

    # ── أ-خ-ذ family: take ──
    'اتخذوا': ('أخذ', 'VERB', 'VIII'),
    'اتخذ': ('أخذ', 'VERB', 'VIII'),
    'يتخذوا': ('أخذ', 'VERB', 'VIII'),
    'يتخذ': ('أخذ', 'VERB', 'VIII'),
    'تتخذوا': ('أخذ', 'VERB', 'VIII'),
    'اتخذتم': ('أخذ', 'VERB', 'VIII'),

    # ── ت-ل-و family: recite ──
    'تتلى': ('تلو', 'VERB', None),
    'يتلو': ('تلو', 'VERB', None),
    'يتلى': ('تلو', 'VERB', None),
    'يتلون': ('تلو', 'VERB', None),
    'تتلوا': ('تلو', 'VERB', None),
    'نتلو': ('تلو', 'VERB', None),
    'نتلوها': ('تلو', 'VERB', None),

    # ── ق-و-ل family: say ──
    'قلنا': ('قول', 'VERB', None),
    'وقل': ('قول', 'VERB', None),
    'فقل': ('قول', 'VERB', None),
    'قيل': ('قول', 'VERB', None),

    # ── أ-ت-ي family: come, give ──
    'اوتي': ('أتي', 'VERB', None),
    'اوتوا': ('أتي', 'VERB', None),
    'يوتى': ('أتي', 'VERB', None),

    # ── ط-و-ع family: obey ──
    'واطيعوا': ('طوع', 'VERB', None),
    'اطيعوا': ('طوع', 'VERB', None),
    'اطعنا': ('طوع', 'VERB', None),
    'يطيعون': ('طوع', 'VERB', None),

    # ── خ-ل-و family: pass, empty ──
    'خلت': ('خلو', 'VERB', None),
    'خلوا': ('خلو', 'VERB', None),

    # ── ب-ن-ي family: son, build ──
    'ابن': ('بني', 'NOUN', None),
    'ابنه': ('بني', 'NOUN', None),

    # ── ع-د-ن family: Eden, permanent residence ──
    'عدن': ('عدن', 'NOUN', None),

    # ── س-و-أ family: evil, bad ──
    'ساء': ('سوأ', 'VERB', None),
    'ساءت': ('سوأ', 'VERB', None),

    # ── ج-ي-أ family: come ──
    'جاءتهم': ('جيأ', 'VERB', None),
    'جاءهم': ('جيأ', 'VERB', None),
    'جاءك': ('جيأ', 'VERB', None),
    'جاء': ('جيأ', 'VERB', None),
    'جاءوا': ('جيأ', 'VERB', None),
    'جاءنا': ('جيأ', 'VERB', None),
    'جاءكم': ('جيأ', 'VERB', None),

    # ── ه-ز-ء family: mock ──
    'هزوا': ('هزأ', 'NOUN', None),
    'يستهزءون': ('هزأ', 'VERB', 'X'),

    # ── ش-ي-أ family: will, want ──
    'شاء': ('شيأ', 'VERB', None),
    'يشاء': ('شيأ', 'VERB', None),
    'نشاء': ('شيأ', 'VERB', None),
    'تشاءون': ('شيأ', 'VERB', None),

    # ── ق-و-م family: establish ──
    'واقيموا': ('قوم', 'VERB', 'IV'),
    'اقيموا': ('قوم', 'VERB', 'IV'),
    'اقمتم': ('قوم', 'VERB', 'IV'),
    'يقيمون': ('قوم', 'VERB', 'IV'),

    # ── أ-ت-ي family: give (with وَ prefix) ──
    'وءاتوا': ('أتي', 'VERB', None),
    'وءاتى': ('أتي', 'VERB', None),
    'ءاتوا': ('أتي', 'VERB', None),
    'ءاتاهم': ('أتي', 'VERB', None),
    'ءاتينا': ('أتي', 'VERB', None),
    'ءاتيناه': ('أتي', 'VERB', None),
    'ءاتاه': ('أتي', 'VERB', None),

    # ── س-و-ي family: equal ──
    'يستوي': ('سوي', 'VERB', 'VIII'),
    'استوى': ('سوي', 'VERB', 'VIII'),

    # ── Particles that were missed ──
    'ذو': (None, 'PARTICLE', None),
    'ذي': (None, 'PARTICLE', None),
    'ذا': (None, 'PARTICLE', None),
    'ونحن': (None, 'PARTICLE', None),
    'ولكم': (None, 'PARTICLE', None),
    'وهذا': (None, 'PARTICLE', None),
    'وانت': (None, 'PARTICLE', None),
    'بهذا': (None, 'PARTICLE', None),
    'كم': (None, 'PARTICLE', None),
    'عنا': (None, 'PARTICLE', None),
    'عليهن': (None, 'PARTICLE', None),
    'افمن': (None, 'PARTICLE', None),
    'وتلك': (None, 'PARTICLE', None),
    'اءذا': (None, 'PARTICLE', None),
    'ويل': (None, 'PARTICLE', None),

    # ── و-ج-د family: find ──
    'تجد': ('وجد', 'VERB', None),
    'يجدون': ('وجد', 'VERB', None),
    'وجدوا': ('وجد', 'VERB', None),

    # ── ء-ل family: people of ──
    'ءال': ('أول', 'NOUN', None),

    # ── ب-ذ-ت family: wealth ──
    'بذات': (None, 'PARTICLE', None),  # بِ + ذات

    # ── ن-ز-ل family: send down ──
    'انزل': ('نزل', 'VERB', 'IV'),
    'انزلنا': ('نزل', 'VERB', 'IV'),
    'انزله': ('نزل', 'VERB', 'IV'),
    'نزل': ('نزل', 'VERB', None),

    # ── ق-ي-م family: establish prayer ──
    'اقم': ('قوم', 'VERB', 'IV'),
    'واقم': ('قوم', 'VERB', 'IV'),

    # ── Misc high-frequency ──
    'يستوي': ('سوي', 'VERB', 'VIII'),
    'عنا': (None, 'PARTICLE', None),
}


def main():
    conn = sqlite3.connect(DB_PATH)

    # Get all unrooted word forms
    rows = conn.execute("""
        SELECT DISTINCT arabic_word, COUNT(*) as cnt
        FROM quran_word_roots
        WHERE (root IS NULL OR root='') AND word_type <> 'PARTICLE'
        GROUP BY arabic_word
        ORDER BY cnt DESC
    """).fetchall()

    print(f"Unrooted word forms: {len(rows)}")

    inserted = 0
    updated_particles = 0
    curated_used = 0

    for arabic_word, freq in rows:
        bare = strip_bare(arabic_word)

        # Check if already in known_forms
        exists = conn.execute(
            "SELECT rowid FROM quran_known_forms WHERE bare_form=?", (bare,)
        ).fetchone()
        if exists:
            continue

        # Check curated mappings
        if bare in CURATED:
            root_un, wtype, vform = CURATED[bare]
            if wtype == 'PARTICLE':
                # Just need to add to particles, not known_forms
                updated_particles += 1
            else:
                conn.execute(
                    "INSERT INTO quran_known_forms (arabic_form, bare_form, root_unhyphenated, word_type, verb_form) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (arabic_word, bare, root_un, wtype, vform)
                )
                inserted += 1
                curated_used += 1
            continue

    conn.commit()

    # Now auto-map remaining unrooted forms using the improved extraction
    # Import the compiler's improved algorithms
    import uslap_compiler as c
    import importlib
    importlib.reload(c)
    if hasattr(c.classify_word, '_particle_cache'):
        delattr(c.classify_word, '_particle_cache')

    auto_mapped = 0
    remaining_rows = conn.execute("""
        SELECT DISTINCT arabic_word, COUNT(*) as cnt
        FROM quran_word_roots
        WHERE (root IS NULL OR root='') AND word_type <> 'PARTICLE'
        GROUP BY arabic_word
        ORDER BY cnt DESC
    """).fetchall()

    for arabic_word, freq in remaining_rows:
        bare = strip_bare(arabic_word)

        # Skip if already handled
        exists = conn.execute(
            "SELECT rowid FROM quran_known_forms WHERE bare_form=?", (bare,)
        ).fetchone()
        if exists:
            continue

        # Skip if curated as particle
        if bare in CURATED and CURATED[bare][1] == 'PARTICLE':
            continue

        # Try the improved extraction against the dictionary
        result = c.find_root(arabic_word, conn)
        if result[0] and result[1]:
            # Found a root with meaning — add to known_forms
            root_hyph = result[0]
            root_un = root_hyph.replace('-', '')
            wtype = result[3] or c.classify_word(arabic_word)
            vform = result[4] or c.detect_verb_form(arabic_word)

            conn.execute(
                "INSERT OR IGNORE INTO quran_known_forms (arabic_form, bare_form, root_unhyphenated, word_type, verb_form) "
                "VALUES (?, ?, ?, ?, ?)",
                (arabic_word, bare, root_un, wtype, vform)
            )
            auto_mapped += 1

    conn.commit()

    print(f"\nResults:")
    print(f"  Curated entries inserted: {curated_used}")
    print(f"  Particles identified: {updated_particles}")
    print(f"  Auto-mapped: {auto_mapped}")
    print(f"  Total new known_forms: {curated_used + auto_mapped}")

    # Count total known_forms now
    total_kf = conn.execute("SELECT COUNT(*) FROM quran_known_forms").fetchone()[0]
    print(f"  Total known_forms: {total_kf}")

    conn.close()


if __name__ == '__main__':
    main()
