#!/usr/bin/env python3
"""
WĀQI'AH — Root the 501 UNROOTED words in quran_word_roots.
Categories:
  1. ROOTED — word has a clear root, assign it + upgrade to MEDIUM_B
  2. PARTICLE — reclassify as PARTICLE (demonstratives, interrogatives, etc.)
  3. SKIP — genuinely unroutable (isolated letters, foreign names)
"""

import sqlite3
try:
    from uslap_db_connect import connect as _uslap_connect
    _HAS_WRAPPER = True
except ImportError:
    _HAS_WRAPPER = False
import sys

DB = "/Users/mmsetubal/Documents/USLaP workplace/Code_files/uslap_database_v3.db"

# ═══════════════════════════════════════════════════════════════
# MAPPING: arabic_word → (root, category, match_method)
# category: ROOT = assign root + MEDIUM_B
#           PARTICLE = reclassify confidence to PARTICLE
#           SKIP = leave as UNROOTED
# ═══════════════════════════════════════════════════════════════

MAPPING = {
    # ── VERBS: clear root identification ──
    # أ-ت-ي family (come/give)
    "تَأْتُوا۟": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "يَأْتِهِۦ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "يَأْتِكَ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "يَأْتُوكُمْ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أَتَوْا۟": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أَتَوْهُ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أَتَوْكَ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أَتَتْهُمْ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أَتَتْكُمُ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أَتَتْكَ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أَتَتْ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "وَأْتُوا۟": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أَتْلُ": ("ت-ل-و", "ROOT", "L8:MANUAL"),  # recite
    "ٱتْلُ": ("ت-ل-و", "ROOT", "L8:MANUAL"),

    # ء-ت-ي with prefixes (give = إيتاء)
    "وَإِيتَآئِ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "وَإِيتَآءِ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "وَإِيتَآءَ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "وَءَاتِ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "وَءَاتُوهُنَّ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "وَءَاتَتْ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "ءَاتِهِمْ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "ءَاتُونِىٓ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "ءَاتُونِى": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "ءَاتَوْهُ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "ءَاتَتْ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أُوتُوهُ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),
    "أُوتَ": ("ء-ت-ي", "ROOT", "L8:MANUAL"),

    # ج-ي-أ family (come)
    "جِئْتُمُونَا": ("ج-ي-أ", "ROOT", "L8:MANUAL"),
    "جِئْتَهُم": ("ج-ي-أ", "ROOT", "L8:MANUAL"),
    "جِئْتَنَا": ("ج-ي-أ", "ROOT", "L8:MANUAL"),
    "جِئْنَٰهُم": ("ج-ي-أ", "ROOT", "L8:MANUAL"),
    "جِئْنَٰكُم": ("ج-ي-أ", "ROOT", "L8:MANUAL"),
    "جِئْتُمْ": ("ج-ي-أ", "ROOT", "L8:MANUAL"),
    "جِئْتُم": ("ج-ي-أ", "ROOT", "L8:MANUAL"),
    "جِئْتُكَ": ("ج-ي-أ", "ROOT", "L8:MANUAL"),

    # ر-أ-ي family (see)
    "رَأَوْكَ": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "رَأَتْهُم": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "رَأَتْهُ": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "يَرَوْنَهُۥ": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "يَرَوْنَهُم": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "تَرَوْنَهُمْ": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "تَرَنِ": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "وَيَرَى": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "لِّيُرَوْا۟": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "لَتَرَوُنَّ": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "ٱلرَّأْىِ": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "أَرِنَا": ("ر-أ-ي", "ROOT", "L8:MANUAL"),
    "وَأَرِنَا": ("ر-أ-ي", "ROOT", "L8:MANUAL"),

    # و-ه-ب family (give/bestow)
    "يَهَبُ": ("و-ه-ب", "ROOT", "L8:MANUAL"),
    "وَيَهَبُ": ("و-ه-ب", "ROOT", "L8:MANUAL"),
    "فَهَبْ": ("و-ه-ب", "ROOT", "L8:MANUAL"),

    # ر-و-ح family (wind/spirit)
    "رِيحٌ": ("ر-و-ح", "ROOT", "L8:MANUAL"),
    "رِيحَ": ("ر-و-ح", "ROOT", "L8:MANUAL"),
    "رِيحٍ": ("ر-و-ح", "ROOT", "L8:MANUAL"),
    "ٱلرِّيَاحَ": ("ر-و-ح", "ROOT", "L8:MANUAL"),

    # ح-ي-ي family (life/live)
    "حَيَوٰةً": ("ح-ي-ي", "ROOT", "L8:MANUAL"),
    "حَيَوٰةٍ": ("ح-ي-ي", "ROOT", "L8:MANUAL"),
    "حَيَوٰةٌ": ("ح-ي-ي", "ROOT", "L8:MANUAL"),
    "وَيُحْىِ": ("ح-ي-ي", "ROOT", "L8:MANUAL"),
    "فَيُحْىِۦ": ("ح-ي-ي", "ROOT", "L8:MANUAL"),
    "تُحْىِ": ("ح-ي-ي", "ROOT", "L8:MANUAL"),
    "أُحْىِۦ": ("ح-ي-ي", "ROOT", "L8:MANUAL"),

    # و-ذ-ر family (leave/forsake)
    "تَذَرُنَّ": ("و-ذ-ر", "ROOT", "L8:MANUAL"),
    "تَذَرُ": ("و-ذ-ر", "ROOT", "L8:MANUAL"),
    "تَذَرْ": ("و-ذ-ر", "ROOT", "L8:MANUAL"),
    "لِيَذَرَ": ("و-ذ-ر", "ROOT", "L8:MANUAL"),
    "أَتَذَرُ": ("و-ذ-ر", "ROOT", "L8:MANUAL"),

    # خ-ش-ي family (fear)
    "تَخْشَوْهُمْ": ("خ-ش-ي", "ROOT", "L8:MANUAL"),
    "تَخْشَوْهُ": ("خ-ش-ي", "ROOT", "L8:MANUAL"),
    "وَيَخْشَ": ("خ-ش-ي", "ROOT", "L8:MANUAL"),
    "يَخْشَ": ("خ-ش-ي", "ROOT", "L8:MANUAL"),
    "أَتَخْشَوْنَهُمْ": ("خ-ش-ي", "ROOT", "L8:MANUAL"),

    # و-ج-د family (find)
    "تَجِدُوهُ": ("و-ج-د", "ROOT", "L8:MANUAL"),
    "لَتَجِدَنَّ": ("و-ج-د", "ROOT", "L8:MANUAL"),
    "لَأَجِدُ": ("و-ج-د", "ROOT", "L8:MANUAL"),

    # أ-خ-و family (brother/sister)
    "وَأَخِى": ("ء-خ-و", "ROOT", "L8:MANUAL"),
    "أُخْتٌ": ("ء-خ-و", "ROOT", "L8:MANUAL"),
    "أَخٌ": ("ء-خ-و", "ROOT", "L8:MANUAL"),
    "أَخَا": ("ء-خ-و", "ROOT", "L8:MANUAL"),
    "ٱلْأُخْتِ": ("ء-خ-و", "ROOT", "L8:MANUAL"),
    "ٱلْأَخِ": ("ء-خ-و", "ROOT", "L8:MANUAL"),
    "يَٰٓأُخْتَ": ("ء-خ-و", "ROOT", "L8:MANUAL"),
    "أُخْتِهَا": ("ء-خ-و", "ROOT", "L8:MANUAL"),
    "أُخْتَهَا": ("ء-خ-و", "ROOT", "L8:MANUAL"),
    "بِأَخٍ": ("ء-خ-و", "ROOT", "L8:MANUAL"),

    # ق-و-م family (stand/rise)
    "تَقُمْ": ("ق-و-م", "ROOT", "L8:MANUAL"),

    # م-ش-ي family (walk)
    "تَمْشِ": ("م-ش-ي", "ROOT", "L8:MANUAL"),

    # و-ض-ع family (put/place)
    "تَضَعُ": ("و-ض-ع", "ROOT", "L8:MANUAL"),
    "وَتَضَعُ": ("و-ض-ع", "ROOT", "L8:MANUAL"),
    "تَضَعَ": ("و-ض-ع", "ROOT", "L8:MANUAL"),
    "وَنَضَعُ": ("و-ض-ع", "ROOT", "L8:MANUAL"),
    "وَيَضَعُ": ("و-ض-ع", "ROOT", "L8:MANUAL"),

    # ز-ي-د family (increase)
    "تَزِدِ": ("ز-ي-د", "ROOT", "L8:MANUAL"),
    "زِدْنَٰهُمْ": ("ز-ي-د", "ROOT", "L8:MANUAL"),
    "نَّزِدْ": ("ز-ي-د", "ROOT", "L8:MANUAL"),
    "نَزِدْ": ("ز-ي-د", "ROOT", "L8:MANUAL"),

    # س-و-أ family (evil/harm)
    "تَسُؤْهُمْ": ("س-و-أ", "ROOT", "L8:MANUAL"),
    "تَسُؤْكُمْ": ("س-و-أ", "ROOT", "L8:MANUAL"),
    "سِىٓءَ": ("س-و-أ", "ROOT", "L8:MANUAL"),
    "سِيٓـَٔتْ": ("س-و-أ", "ROOT", "L8:MANUAL"),
    "سَيِّـَٔاتِهِۦ": ("س-و-أ", "ROOT", "L8:MANUAL"),
    "سَيِّـَٔاتِنَا": ("س-و-أ", "ROOT", "L8:MANUAL"),
    "سَيِّئُهُۥ": ("س-و-أ", "ROOT", "L8:MANUAL"),
    "سَيِّئًا": ("س-و-أ", "ROOT", "L8:MANUAL"),
    "أَسَأْتُمْ": ("س-و-أ", "ROOT", "L8:MANUAL"),

    # ب-أ-س family (might/distress)
    "بَأْسًا": ("ب-أ-س", "ROOT", "L8:MANUAL"),
    "بَأْسِكُمْ": ("ب-أ-س", "ROOT", "L8:MANUAL"),
    "بَأْسُهُۥ": ("ب-أ-س", "ROOT", "L8:MANUAL"),
    "بَأْسَكُمْ": ("ب-أ-س", "ROOT", "L8:MANUAL"),

    # ش-ع-ر family (rites/perceive)
    "شَعَٰٓئِرَ": ("ش-ع-ر", "ROOT", "L8:MANUAL"),
    "شَعَٰٓئِرِ": ("ش-ع-ر", "ROOT", "L8:MANUAL"),

    # ش-أ-ن family (affair/matter)
    "شَأْنٍ": ("ش-أ-ن", "ROOT", "L8:MANUAL"),
    "شَأْنِهِمْ": ("ش-أ-ن", "ROOT", "L8:MANUAL"),
    "شَأْنٌ": ("ش-أ-ن", "ROOT", "L8:MANUAL"),

    # ح-د-ق family (gardens)
    "حَدَآئِقَ": ("ح-د-ق", "ROOT", "L8:MANUAL"),

    # ط-ر-و family (fresh)
    "طَرِيًّا": ("ط-ر-و", "ROOT", "L8:MANUAL"),

    # ط-غ-ي family (transgress)
    "طَاغُونَ": ("ط-غ-ي", "ROOT", "L8:MANUAL"),

    # ض-ح-و family (forenoon)
    "ضُحَىٰهَا": ("ض-ح-و", "ROOT", "L8:MANUAL"),
    "وَٱلضُّحَىٰ": ("ض-ح-و", "ROOT", "L8:MANUAL"),

    # ص-ب-و family (youth/child)
    "صَبِيًّا": ("ص-ب-و", "ROOT", "L8:MANUAL"),

    # ع-و-ذ family (seek refuge)
    "عُذْتُ": ("ع-و-ذ", "ROOT", "L8:MANUAL"),

    # س-م-و family (name/hear — samiyy = namesake)
    "سَمِيًّا": ("س-م-و", "ROOT", "L8:MANUAL"),

    # و-س-ع family (encompass)
    "سَعَتِهِۦ": ("و-س-ع", "ROOT", "L8:MANUAL"),

    # ن-ب-أ family (news/tidings)
    "بِنَبَإٍ": ("ن-ب-أ", "ROOT", "L8:MANUAL"),
    "ٱلنَّبَإِ": ("ن-ب-أ", "ROOT", "L8:MANUAL"),
    "أَنۢبَأَكَ": ("ن-ب-أ", "ROOT", "L8:MANUAL"),
    "نَبَّأَهَا": ("ن-ب-أ", "ROOT", "L8:MANUAL"),
    "نَبَأَهُۥ": ("ن-ب-أ", "ROOT", "L8:MANUAL"),
    "نَّبَإِى۟": ("ن-ب-أ", "ROOT", "L8:MANUAL"),
    "يُنَبَّأْ": ("ن-ب-أ", "ROOT", "L8:MANUAL"),

    # ل-ق-ي family (meet/encounter)
    "يَلْقَ": ("ل-ق-ي", "ROOT", "L8:MANUAL"),
    "أَلْقِ": ("ل-ق-ي", "ROOT", "L8:MANUAL"),

    # ك-ف-ي family (suffice)
    "يَكْفِ": ("ك-ف-ي", "ROOT", "L8:MANUAL"),

    # ك-ي-د family (plot)
    "يَكَدْ": ("ك-ي-د", "ROOT", "L8:MANUAL"),

    # ق-ض-ي family (judge/decree)
    "يَقْضِ": ("ق-ض-ي", "ROOT", "L8:MANUAL"),
    "لِيَقْضِ": ("ق-ض-ي", "ROOT", "L8:MANUAL"),

    # ق-و-ل family (say)
    "يَقُلْ": ("ق-و-ل", "ROOT", "L8:MANUAL"),
    "تَقُل": ("ق-و-ل", "ROOT", "L8:MANUAL"),
    "وَأَقُل": ("ق-و-ل", "ROOT", "L8:MANUAL"),
    "فَقُلْتُ": ("ق-و-ل", "ROOT", "L8:MANUAL"),
    "قُلْنَ": ("ق-و-ل", "ROOT", "L8:MANUAL"),
    "قُلْتُهُۥ": ("ق-و-ل", "ROOT", "L8:MANUAL"),

    # غ-ي-ب family (unseen)
    "يَغْتَب": ("غ-ي-ب", "ROOT", "L8:MANUAL"),

    # ع-ي-ي family (tire/falter)
    "يَعْىَ": ("ع-ي-ي", "ROOT", "L8:MANUAL"),

    # ع-ش-و family (blind at night)
    "يَعْشُ": ("ع-ش-و", "ROOT", "L8:MANUAL"),

    # و-ع-د family (promise)
    "يَعِدُ": ("و-ع-د", "ROOT", "L8:MANUAL"),

    # ص-ف-و family (choose/select)
    "يَصْطَفِى": ("ص-ف-و", "ROOT", "L8:MANUAL"),
    "ٱصْطَفَيْتُكَ": ("ص-ف-و", "ROOT", "L8:MANUAL"),
    "ٱصْطَفَىٰهُ": ("ص-ف-و", "ROOT", "L8:MANUAL"),
    "ٱصْطَفَىٰكِ": ("ص-ف-و", "ROOT", "L8:MANUAL"),

    # ز-ي-غ family (deviate)
    "يَزِغْ": ("ز-ي-غ", "ROOT", "L8:MANUAL"),
    "تُزِغْ": ("ز-ي-غ", "ROOT", "L8:MANUAL"),

    # ر-م-ي family (throw)
    "يَرْمِ": ("ر-م-ي", "ROOT", "L8:MANUAL"),

    # خ-ل-و family (be alone/empty)
    "يَخْلُ": ("خ-ل-و", "ROOT", "L8:MANUAL"),

    # ح-ي-ض family (menstruate)
    "يَحِضْنَ": ("ح-ي-ض", "ROOT", "L8:MANUAL"),

    # أ-خ-ذ family (take)
    "يَتَّخِذُونَ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "وَيَتَّخِذُ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "وَيَتَّخِذَهَا": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "وَيَتَّخِذَ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "وَتَتَّخِذُونَ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "مُتَّخِذِىٓ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "مُتَّخِذَٰتِ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "مُتَّخِذَ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "لَنَتَّخِذَنَّ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "لَتَّخَذْتَ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "تَتَّخِذَ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "أَفَتَتَّخِذُونَهُۥ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "أَتَتَّخِذُنَا": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "أَتَتَّخِذُ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "ءَأَتَّخِذُ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "خُذُوهُ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "وَخُذْ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),
    "وَخُذُوهُمْ": ("ء-خ-ذ", "ROOT", "L8:MANUAL"),

    # ت-و-ب family (repent)
    "يَتُبْ": ("ت-و-ب", "ROOT", "L8:MANUAL"),
    "وَتُبْ": ("ت-و-ب", "ROOT", "L8:MANUAL"),
    "تَٰٓئِبَٰتٍ": ("ت-و-ب", "ROOT", "L8:MANUAL"),

    # و-ف-ي family (fulfil)
    "نُوَفِّ": ("و-ف-ي", "ROOT", "L8:MANUAL"),
    "أُوفِ": ("و-ف-ي", "ROOT", "L8:MANUAL"),
    "فَأَوْفِ": ("و-ف-ي", "ROOT", "L8:MANUAL"),

    # ن-ج-و family (save/rescue)
    "نُنجِ": ("ن-ج-و", "ROOT", "L8:MANUAL"),
    "نَّجَّيْنَٰهُم": ("ن-ج-و", "ROOT", "L8:MANUAL"),
    "نَاجٍ": ("ن-ج-و", "ROOT", "L8:MANUAL"),

    # و-ف-ي / و-ف-ت family (death/take in full)
    "تَوَفَّتْهُمُ": ("و-ف-ي", "ROOT", "L8:MANUAL"),
    "تَوَفَّتْهُ": ("و-ف-ي", "ROOT", "L8:MANUAL"),
    "يَتَوَفَّوْنَهُمْ": ("و-ف-ي", "ROOT", "L8:MANUAL"),

    # أ-ن-ي family (come/time)
    "يَأْنِ": ("ء-ن-ي", "ROOT", "L8:MANUAL"),

    # أ-ل-و family (swear/shorten)
    "يَأْتَلِ": ("ء-ل-و", "ROOT", "L8:MANUAL"),

    # و-ل-ي family (turn/ally)
    "يُوَلُّوكُمُ": ("و-ل-ي", "ROOT", "L8:MANUAL"),
    "وَالٍ": ("و-ل-ي", "ROOT", "L8:MANUAL"),

    # و-ح-ي family (reveal)
    "يُوحَ": ("و-ح-ي", "ROOT", "L8:MANUAL"),

    # ه-و-ن family (humiliate)
    "يُهِنِ": ("ه-و-ن", "ROOT", "L8:MANUAL"),
    "أَهَٰنَنِ": ("ه-و-ن", "ROOT", "L8:MANUAL"),

    # غ-ن-ي family (suffice/enrich)
    "يُغْنِ": ("غ-ن-ي", "ROOT", "L8:MANUAL"),
    "أَغْنَتْ": ("غ-ن-ي", "ROOT", "L8:MANUAL"),

    # ج-ز-ي family (recompense)
    "يُجْزَ": ("ج-ز-ي", "ROOT", "L8:MANUAL"),
    "سَيُجْزَوْنَ": ("ج-ز-ي", "ROOT", "L8:MANUAL"),

    # ج-و-ب family (answer)
    "يُجِبْ": ("ج-و-ب", "ROOT", "L8:MANUAL"),
    "نُّجِبْ": ("ج-و-ب", "ROOT", "L8:MANUAL"),
    "أَسْتَجِبْ": ("ج-و-ب", "ROOT", "L8:MANUAL"),

    # ع-ف-و family (pardon)
    "وَٱعْفُ": ("ع-ف-و", "ROOT", "L8:MANUAL"),
    "وَيَعْفُ": ("ع-ف-و", "ROOT", "L8:MANUAL"),
    "نَّعْفُ": ("ع-ف-و", "ROOT", "L8:MANUAL"),

    # و-ق-ي family (protect)
    "تَقِ": ("و-ق-ي", "ROOT", "L8:MANUAL"),
    "وَٱتَّقِ": ("و-ق-ي", "ROOT", "L8:MANUAL"),
    "وَيَتَّقْهِ": ("و-ق-ي", "ROOT", "L8:MANUAL"),

    # م-و-ت family (death)
    "تَمُتْ": ("م-و-ت", "ROOT", "L8:MANUAL"),
    "فَيَمُتْ": ("م-و-ت", "ROOT", "L8:MANUAL"),
    "مَّيْتَةً": ("م-و-ت", "ROOT", "L8:MANUAL"),
    "مَيْتَةً": ("م-و-ت", "ROOT", "L8:MANUAL"),
    "بِمَيِّتٍ": ("م-و-ت", "ROOT", "L8:MANUAL"),

    # و-ص-ي family (bequeath)
    "مُّوصٍ": ("و-ص-ي", "ROOT", "L8:MANUAL"),

    # ه-د-ي family (guide)
    "مُّهْتَدٍ": ("ه-د-ي", "ROOT", "L8:MANUAL"),
    "بِهَٰدِ": ("ه-د-ي", "ROOT", "L8:MANUAL"),
    "أَتَهْتَدِىٓ": ("ه-د-ي", "ROOT", "L8:MANUAL"),

    # ح-و-ط family (encompass)
    "مُّحِيطًا": ("ح-و-ط", "ROOT", "L8:MANUAL"),
    "مُحِيطًا": ("ح-و-ط", "ROOT", "L8:MANUAL"),
    "تُحِطْ": ("ح-و-ط", "ROOT", "L8:MANUAL"),
    "وَأَحَٰطَتْ": ("ح-و-ط", "ROOT", "L8:MANUAL"),
    "أَحَطتُ": ("ح-و-ط", "ROOT", "L8:MANUAL"),

    # و-ص-د family (shut/close)
    "مُّؤْصَدَةٌۢ": ("و-ص-د", "ROOT", "L8:MANUAL"),
    "مُّؤْصَدَةٌ": ("و-ص-د", "ROOT", "L8:MANUAL"),

    # ص-و-ب family (befall/hit)
    "أَصَٰبَتْهُم": ("ص-و-ب", "ROOT", "L8:MANUAL"),
    "سَيُصِيبُ": ("ص-و-ب", "ROOT", "L8:MANUAL"),
    "مُصِيبُهَا": ("ص-و-ب", "ROOT", "L8:MANUAL"),
    "أَصَبْنَٰهُم": ("ص-و-ب", "ROOT", "L8:MANUAL"),
    "كَصَيِّبٍ": ("ص-و-ب", "ROOT", "L8:MANUAL"),

    # ب-و-أ family (settle/return)
    "وَبَوَّأَكُمْ": ("ب-و-أ", "ROOT", "L8:MANUAL"),

    # ل-ي-ن family (soften)
    "لِنتَ": ("ل-ي-ن", "ROOT", "L8:MANUAL"),
    "وَأَلَنَّا": ("ل-ي-ن", "ROOT", "L8:MANUAL"),

    # ب-د-و family (appear/become manifest)
    "تُبْدَ": ("ب-د-و", "ROOT", "L8:MANUAL"),
    "فَبَدَتْ": ("ب-د-و", "ROOT", "L8:MANUAL"),
    "بَدَتْ": ("ب-د-و", "ROOT", "L8:MANUAL"),
    "بَدَتِ": ("ب-د-و", "ROOT", "L8:MANUAL"),

    # ع-د-و family (transgress/count)
    "تَعْدُ": ("ع-د-و", "ROOT", "L8:MANUAL"),
    "وَيَتَعَدَّ": ("ع-د-و", "ROOT", "L8:MANUAL"),

    # و-ص-ل family (join)
    "تَصِلُ": ("و-ص-ل", "ROOT", "L8:MANUAL"),

    # و-ص-ف family (describe)
    "تَصِفُ": ("و-ص-ف", "ROOT", "L8:MANUAL"),
    "وَتَصِفُ": ("و-ص-ف", "ROOT", "L8:MANUAL"),

    # ط-و-ع family (obey)
    "سَنُطِيعُكُمْ": ("ط-و-ع", "ROOT", "L8:MANUAL"),

    # ط-و-ف family (circle/go around)
    "طَٰٓائِفٌ": ("ط-و-ف", "ROOT", "L8:MANUAL"),
    "طَآئِفٌ": ("ط-و-ف", "ROOT", "L8:MANUAL"),

    # ط-ي-ر family (bird/fly)
    "طَٰٓائِرُهُمْ": ("ط-ي-ر", "ROOT", "L8:MANUAL"),
    "طَٰٓائِرَهُۥ": ("ط-ي-ر", "ROOT", "L8:MANUAL"),
    "طَٰٓائِرٍ": ("ط-ي-ر", "ROOT", "L8:MANUAL"),

    # ط-ي-ب family (good/pleasant)
    "طِبْنَ": ("ط-ي-ب", "ROOT", "L8:MANUAL"),
    "طُوبَىٰ": ("ط-و-ب", "ROOT", "L8:MANUAL"),

    # ط-ح-و family (spread out)
    "طَحَىٰهَا": ("ط-ح-و", "ROOT", "L8:MANUAL"),

    # د-ح-و family (spread)
    "دَحَىٰهَآ": ("د-ح-و", "ROOT", "L8:MANUAL"),

    # ص-غ-و family (incline)
    "صَغَتْ": ("ص-غ-و", "ROOT", "L8:MANUAL"),

    # ص-ل-ي family (burn/roast)
    "صَالِ": ("ص-ل-ي", "ROOT", "L8:MANUAL"),
    "تُصَلِّ": ("ص-ل-و", "ROOT", "L8:MANUAL"),  # pray

    # ق-س-و family (harden)
    "فَقَسَتْ": ("ق-س-و", "ROOT", "L8:MANUAL"),
    "قَٰسِيَةً": ("ق-س-و", "ROOT", "L8:MANUAL"),

    # ق-و-م / ق-ي-م family
    "قَيِّمَةٌ": ("ق-و-م", "ROOT", "L8:MANUAL"),

    # ق-ص-و family (far/remote)
    "قَصِيًّا": ("ق-ص-و", "ROOT", "L8:MANUAL"),

    # ف-أ family (group/faction)
    "فِئَتُكُمْ": ("ف-ي-أ", "ROOT", "L8:MANUAL"),

    # غ-ش-ي family (cover/overwhelm)
    "فَغَشِيَهُم": ("غ-ش-ي", "ROOT", "L8:MANUAL"),
    "غَشِيَهُمْ": ("غ-ش-ي", "ROOT", "L8:MANUAL"),
    "غَشِيَهُم": ("غ-ش-ي", "ROOT", "L8:MANUAL"),
    "ٱلْغَٰشِيَةِ": ("غ-ش-ي", "ROOT", "L8:MANUAL"),
    "غَٰشِيَةٌ": ("غ-ش-ي", "ROOT", "L8:MANUAL"),

    # غ-و-ي family (stray/deviate)
    "غَيًّا": ("غ-و-ي", "ROOT", "L8:MANUAL"),

    # ظ-م-أ family (thirst)
    "ظَمَأٌ": ("ظ-م-أ", "ROOT", "L8:MANUAL"),

    # ظ-ل-ل family (remain/shade)
    "ظَلْتَ": ("ظ-ل-ل", "ROOT", "L8:MANUAL"),
    "فَظَلْتُمْ": ("ظ-ل-ل", "ROOT", "L8:MANUAL"),

    # ج-ث-و family (kneel)
    "جِثِيًّا": ("ج-ث-و", "ROOT", "L8:MANUAL"),
    "جَاثِيَةً": ("ج-ث-و", "ROOT", "L8:MANUAL"),

    # خ-ط-أ family (sin/mistake)
    "خَطَٰيَٰكُمْ": ("خ-ط-أ", "ROOT", "L8:MANUAL"),
    "خَطَٰيَٰهُم": ("خ-ط-أ", "ROOT", "L8:MANUAL"),

    # د-و-م family (last/continue)
    "دُمْتُ": ("د-و-م", "ROOT", "L8:MANUAL"),
    "دُمْتَ": ("د-و-م", "ROOT", "L8:MANUAL"),
    "دَآئِمٌ": ("د-و-م", "ROOT", "L8:MANUAL"),

    # د-ع-و family (call/invite)
    "دَاعِىَ": ("د-ع-و", "ROOT", "L8:MANUAL"),
    "وَيَدْعُ": ("د-ع-و", "ROOT", "L8:MANUAL"),
    "نَدْعُ": ("د-ع-و", "ROOT", "L8:MANUAL"),
    "فَلْيَدْعُ": ("د-ع-و", "ROOT", "L8:MANUAL"),
    "نَادُوا۟": ("ن-د-و", "ROOT", "L8:MANUAL"),  # call out (n-d-w)

    # د-أ-ب family (persist/habit)
    "دَأْبِ": ("د-أ-ب", "ROOT", "L8:MANUAL"),
    "دَأَبًا": ("د-أ-ب", "ROOT", "L8:MANUAL"),

    # د-م-و family (blood)
    "وَدَمٍ": ("د-م-و", "ROOT", "L8:MANUAL"),
    "بِدَمٍ": ("د-م-و", "ROOT", "L8:MANUAL"),

    # خ-و-ف family (fear)
    "وَخِيفَةً": ("خ-و-ف", "ROOT", "L8:MANUAL"),

    # خ-ل-و family (aunt)
    "وَخَٰلَٰتُكُمْ": ("خ-و-ل", "ROOT", "L8:MANUAL"),
    "خَٰلَٰتِكُمْ": ("خ-و-ل", "ROOT", "L8:MANUAL"),
    "خَٰلَٰتِكَ": ("خ-و-ل", "ROOT", "L8:MANUAL"),

    # ر-أ-س family (head)
    "رَّأْسِهِۦ": ("ر-أ-س", "ROOT", "L8:MANUAL"),
    "ٱلرَّأْسُ": ("ر-أ-س", "ROOT", "L8:MANUAL"),
    "رَأْسِى": ("ر-أ-س", "ROOT", "L8:MANUAL"),
    "رَأْسِهِۦ": ("ر-أ-س", "ROOT", "L8:MANUAL"),
    "بِرَأْسِىٓ": ("ر-أ-س", "ROOT", "L8:MANUAL"),
    "بِرَأْسِ": ("ر-أ-س", "ROOT", "L8:MANUAL"),

    # ر-أ-ف family (compassion)
    "رَأْفَةٌ": ("ر-أ-ف", "ROOT", "L8:MANUAL"),
    "رَأْفَةً": ("ر-أ-ف", "ROOT", "L8:MANUAL"),

    # ر-ض-و family (pleased)
    "رَضِيًّا": ("ر-ض-و", "ROOT", "L8:MANUAL"),

    # ر-ق-ي family (ascend)
    "رَاقٍ": ("ر-ق-ي", "ROOT", "L8:MANUAL"),

    # ذ-و family (possessor)
    "ذَوِى": ("ذ-و", "ROOT", "L8:MANUAL"),
    "ذَوَىْ": ("ذ-و", "ROOT", "L8:MANUAL"),
    "ذَوَاتَآ": ("ذ-و", "ROOT", "L8:MANUAL"),
    "وَذِى": ("ذ-و", "ROOT", "L8:MANUAL"),
    "وَذُو": ("ذ-و", "ROOT", "L8:MANUAL"),
    "فَذُو": ("ذ-و", "ROOT", "L8:MANUAL"),
    "وَذَاتَ": ("ذ-و", "ROOT", "L8:MANUAL"),
    "وَبِذِى": ("ذ-و", "ROOT", "L8:MANUAL"),

    # ب-ن-و family (son/daughter)
    "ٱبْنَتَ": ("ب-ن-و", "ROOT", "L8:MANUAL"),
    "وَبَنَٰتٍۭ": ("ب-ن-و", "ROOT", "L8:MANUAL"),

    # ب-ص-ر family (see/perceive)
    "بَصْۜطَةً": ("ب-س-ط", "ROOT", "L8:MANUAL"),  # actually بسط
    "بَصَٰٓئِرُ": ("ب-ص-ر", "ROOT", "L8:MANUAL"),
    "وَيَبْصُۜطُ": ("ب-س-ط", "ROOT", "L8:MANUAL"),  # بسط
    "بِمُصَيْطِرٍ": ("ص-ي-ط-ر", "ROOT", "L8:MANUAL"),  # musaytir

    # ب-ق-ي family (remain)
    "بَاقٍ": ("ب-ق-ي", "ROOT", "L8:MANUAL"),

    # ب-ك-ي family (weep)
    "بَكَتْ": ("ب-ك-ي", "ROOT", "L8:MANUAL"),

    # و-ر-ث family (inherit)
    "وَيَرِثُ": ("و-ر-ث", "ROOT", "L8:MANUAL"),
    "نَرِثُ": ("و-ر-ث", "ROOT", "L8:MANUAL"),

    # ش-ر-ي family (buy/sell)
    "وَشَرَوْهُ": ("ش-ر-ي", "ROOT", "L8:MANUAL"),

    # ش-ف-ي family (heal)
    "وَيَشْفِ": ("ش-ف-ي", "ROOT", "L8:MANUAL"),

    # م-ح-و family (erase)
    "وَيَمْحُ": ("م-ح-و", "ROOT", "L8:MANUAL"),

    # ذ-و-ق family (taste)
    "وَيُذِيقَ": ("ذ-و-ق", "ROOT", "L8:MANUAL"),
    "لِّنُذِيقَهُمْ": ("ذ-و-ق", "ROOT", "L8:MANUAL"),
    "لِيُذِيقَهُم": ("ذ-و-ق", "ROOT", "L8:MANUAL"),

    # ه-ز-أ family (mock)
    "وَيُسْتَهْزَأُ": ("ه-ز-أ", "ROOT", "L8:MANUAL"),

    # ز-ج-ر family (rebuke)
    "وَٱزْدُجِرَ": ("ز-ج-ر", "ROOT", "L8:MANUAL"),

    # و-ي-ل family (woe)
    "وَيْلَكَ": ("و-ي-ل", "ROOT", "L8:MANUAL"),
    "يَٰوَيْلَتَنَا": ("و-ي-ل", "ROOT", "L8:MANUAL"),

    # س-و-ق family (drive)
    "سُقْنَٰهُ": ("س-و-ق", "ROOT", "L8:MANUAL"),

    # س-ي-ح family (travel/roam)
    "سَٰٓائِحَٰتٍ": ("س-ي-ح", "ROOT", "L8:MANUAL"),

    # س-ع-ي family (strive)
    "سَعَوْ": ("س-ع-ي", "ROOT", "L8:MANUAL"),

    # ك-ي-ل family (measure)
    "نَكْتَلْ": ("ك-ي-ل", "ROOT", "L8:MANUAL"),

    # ع-و-د family (return)
    "نَعُدْ": ("ع-و-د", "ROOT", "L8:MANUAL"),

    # ب-غ-ي family (seek/transgress)
    "نَبْغِ": ("ب-غ-ي", "ROOT", "L8:MANUAL"),
    "تَبْغِ": ("ب-غ-ي", "ROOT", "L8:MANUAL"),
    "أَيَبْتَغُونَ": ("ب-غ-ي", "ROOT", "L8:MANUAL"),

    # ز-ك-و family (purify)
    "زَكَّىٰهَا": ("ز-ك-و", "ROOT", "L8:MANUAL"),
    "زَكِيَّةًۢ": ("ز-ك-و", "ROOT", "L8:MANUAL"),
    "زَكِيًّا": ("ز-ك-و", "ROOT", "L8:MANUAL"),

    # ن-ش-أ family (create/originate)
    "أَنشَأَ": ("ن-ش-أ", "ROOT", "L8:MANUAL"),
    "أَنشَأْتُمْ": ("ن-ش-أ", "ROOT", "L8:MANUAL"),

    # ل-ج-أ family (refuge)
    "مَّلْجَإٍ": ("ل-ج-أ", "ROOT", "L8:MANUAL"),
    "مَلْجَأَ": ("ل-ج-أ", "ROOT", "L8:MANUAL"),

    # غ-و-ر family (cave)
    "مَغَٰرَٰتٍ": ("غ-و-ر", "ROOT", "L8:MANUAL"),

    # م-ض-ي family (pass)
    "مَضَتْ": ("م-ض-ي", "ROOT", "L8:MANUAL"),

    # ح-و-ل family (stratagem)
    "حِيلَةً": ("ح-و-ل", "ROOT", "L8:MANUAL"),

    # ح-م-ي family (protect)
    "حَامٍ": ("ح-م-ي", "ROOT", "L8:MANUAL"),

    # غ-د-و family (tomorrow/morning)
    "لِغَدٍ": ("غ-د-و", "ROOT", "L8:MANUAL"),

    # ل-و-م family (blame)
    "لَآئِمٍ": ("ل-و-م", "ROOT", "L8:MANUAL"),

    # ع-ت-و family (rebel)
    "عَتَتْ": ("ع-ت-و", "ROOT", "L8:MANUAL"),

    # ر-د-د / ر-و-د family (return/want)
    "أَرَدْنَٰهُ": ("ر-و-د", "ROOT", "L8:MANUAL"),
    "أَرَدْنَ": ("ر-و-د", "ROOT", "L8:MANUAL"),
    "أَرَدتُّ": ("ر-و-د", "ROOT", "L8:MANUAL"),

    # د-ر-ي family (know)
    "أَدْرِ": ("د-ر-ي", "ROOT", "L8:MANUAL"),

    # ط-و-ي family (fold)
    "كَطَىِّ": ("ط-و-ي", "ROOT", "L8:MANUAL"),

    # ك-أ-س family (cup)
    "كَأْسٍ": ("ك-أ-س", "ROOT", "L8:MANUAL"),
    "وَكَأْسٍ": ("ك-أ-س", "ROOT", "L8:MANUAL"),

    # ر-س-و family (firm/anchor)
    "رَّاسِيَٰتٍ": ("ر-س-و", "ROOT", "L8:MANUAL"),

    # ث-ن-ي family (two)
    "ٱثْنَتَىْ": ("ث-ن-ي", "ROOT", "L8:MANUAL"),

    # و-س-ق family (gather)
    "ٱتَّسَقَ": ("و-س-ق", "ROOT", "L8:MANUAL"),

    # ش-ه-و family (desire)
    "ٱشْتَهَتْ": ("ش-ه-و", "ROOT", "L8:MANUAL"),

    # ف-د-ي family (ransom)
    "ٱفْتَدَتْ": ("ف-د-ي", "ROOT", "L8:MANUAL"),

    # ق-و-ت family (time/appoint)
    "أُقِّتَتْ": ("و-ق-ت", "ROOT", "L8:MANUAL"),

    # ف-ت-ي family (decree/give opinion)
    "تَسْتَفْتِ": ("ف-ت-ي", "ROOT", "L8:MANUAL"),

    # ط-و-ع family / ط-ي-ع — obey
    "تَسْطِع": ("ط-و-ع", "ROOT", "L8:MANUAL"),
    "تَسْتَطِع": ("ط-و-ع", "ROOT", "L8:MANUAL"),

    # ت-ب-ع family (follow)
    "تَتْرَا": ("ت-ر-ي", "ROOT", "L8:MANUAL"),  # one after another — و-ت-ر

    # ق-ف-و family (follow)
    "تَقْفُ": ("ق-ف-و", "ROOT", "L8:MANUAL"),

    # ن-س-ي family (forget)
    "تَنسَ": ("ن-س-ي", "ROOT", "L8:MANUAL"),

    # و-ن-ي family (weaken)
    "تَنِيَا": ("و-ن-ي", "ROOT", "L8:MANUAL"),

    # ص-ب-و / صبأ (pour/incline)
    "أَصْبُ": ("ص-ب-و", "ROOT", "L8:MANUAL"),

    # ل-ي-ل / ل-و-ي family (twist/fold)
    "لَيًّۢا": ("ل-و-ي", "ROOT", "L8:MANUAL"),

    # ل-م-ع (glimpse/with)
    "لَمَعَ": ("م-ع-ي", "ROOT", "L8:MANUAL"),  # actually لَمَعَ is with/along

    # أ-و-ي family (shelter)
    "ءَاوَوا۟": ("ء-و-ي", "ROOT", "L8:MANUAL"),

    # أ-ذ-ي family (harm)
    "ءَاذَوْا۟": ("ء-ذ-ي", "ROOT", "L8:MANUAL"),

    # أ-س-ي family (grieve)
    "ءَاسَىٰ": ("ء-س-ي", "ROOT", "L8:MANUAL"),
    "تَأْسَ": ("ء-س-ي", "ROOT", "L8:MANUAL"),

    # ء-ن-ي family (ripe/hot)
    "ءَانٍ": ("ء-ن-ي", "ROOT", "L8:MANUAL"),

    # و-ل-د family (give birth)
    "ءَأَلِدُ": ("و-ل-د", "ROOT", "L8:MANUAL"),

    # ض-أ-ن family (sheep)
    "ٱلضَّأْنِ": ("ض-أ-ن", "ROOT", "L8:MANUAL"),

    # د-ر-ج family (advance gradually)
    "سَنَسْتَدْرِجُهُم": ("د-ر-ج", "ROOT", "L8:MANUAL"),

    # غ-ف-ر family (forgive)
    "سَأَسْتَغْفِرُ": ("غ-ف-ر", "ROOT", "L8:MANUAL"),

    # ع-ي-د / ع-و-د family (return)
    "نُّعِيدُهُۥ": ("ع-و-د", "ROOT", "L8:MANUAL"),

    # ق-و-م family (establish)
    "وَأَقِمْنَ": ("ق-و-م", "ROOT", "L8:MANUAL"),

    # ب-ل-و family (test)
    "أَتَسْتَبْدِلُونَ": ("ب-د-ل", "ROOT", "L8:MANUAL"),  # بدل substitute

    # و-ص-و family (recommend)
    "أَتَوَاصَوْا۟": ("و-ص-ي", "ROOT", "L8:MANUAL"),

    # أ-ب-و family (father)
    "أَبَاهُ": ("ء-ب-و", "ROOT", "L8:MANUAL"),
    "أَبًا": ("ء-ب-و", "ROOT", "L8:MANUAL"),

    # ك-و-ن family (be)
    "لَكُنتُم": ("ك-و-ن", "ROOT", "L8:MANUAL"),
    "أَكُ": ("ك-و-ن", "ROOT", "L8:MANUAL"),

    # و-ث-ق family (covenant)
    "بِمِيثَٰقِهِمْ": ("و-ث-ق", "ROOT", "L8:MANUAL"),

    # و-د-ي family (valley)
    "بِوَادٍ": ("و-د-ي", "ROOT", "L8:MANUAL"),
    "وَادِ": ("و-د-ي", "ROOT", "L8:MANUAL"),
    "وَادٍ": ("و-د-ي", "ROOT", "L8:MANUAL"),

    # ء-ل-و family (retinue/people)
    "بِـَٔالِ": ("ء-و-ل", "ROOT", "L8:MANUAL"),  # bi-āli

    # سبأ (Sheba — proper name but from root)
    "لِسَبَإٍ": ("س-ب-أ", "ROOT", "L8:MANUAL"),
    "سَبَإٍۭ": ("س-ب-أ", "ROOT", "L8:MANUAL"),

    # إرم (Iram — proper name)
    "إِرَمَ": ("ء-ر-م", "ROOT", "L8:MANUAL"),

    # تتر — one after another (و-ت-ر = individually, one by one)
    "تَتْرَا": ("و-ت-ر", "ROOT", "L8:MANUAL"),

    # ── PARTICLES / DEMONSTRATIVES / PRONOUNS ──
    "فَإِذْ": ("", "PARTICLE", "PARTICLE"),
    "فَأَنتَ": ("", "PARTICLE", "PARTICLE"),
    "أَوَمَن": ("", "PARTICLE", "PARTICLE"),
    "أَهَٰذَا": ("", "PARTICLE", "PARTICLE"),
    "أَفِى": ("", "PARTICLE", "PARTICLE"),
    "أَفَإِي۟ن": ("", "PARTICLE", "PARTICLE"),
    "أَذَٰلِكَ": ("", "PARTICLE", "PARTICLE"),
    "أَءِنَّكَ": ("", "PARTICLE", "PARTICLE"),
    "ٱلْـَٔانَ": ("", "PARTICLE", "PARTICLE"),
    "وَهُمَا": ("", "PARTICLE", "PARTICLE"),
    "وَهَٰذِهِ": ("", "PARTICLE", "PARTICLE"),
    "وَمَاذَا": ("", "PARTICLE", "PARTICLE"),
    "وَلِلَّذِينَ": ("", "PARTICLE", "PARTICLE"),
    "وَلِذَٰلِكَ": ("", "PARTICLE", "PARTICLE"),
    "وَذَٰلِكُمْ": ("", "PARTICLE", "PARTICLE"),
    "وَبِمَن": ("", "PARTICLE", "PARTICLE"),
    "وَإِنَّنَا": ("", "PARTICLE", "PARTICLE"),
    "هَٰذَٰنِ": ("", "PARTICLE", "PARTICLE"),
    "هَٰذَانِ": ("", "PARTICLE", "PARTICLE"),
    "رُّبَمَا": ("", "PARTICLE", "PARTICLE"),
    "مَهْمَا": ("", "PARTICLE", "PARTICLE"),
    "لَسَوْفَ": ("", "PARTICLE", "PARTICLE"),
    "فَلَسَوْفَ": ("", "PARTICLE", "PARTICLE"),
    "لَدَا": ("", "PARTICLE", "PARTICLE"),
    "كَذَٰلِكُمْ": ("", "PARTICLE", "PARTICLE"),
    "فَثَمَّ": ("", "PARTICLE", "PARTICLE"),
    "فَبِمَ": ("", "PARTICLE", "PARTICLE"),
    "فَبِذَٰلِكَ": ("", "PARTICLE", "PARTICLE"),
    "فَلِذَٰلِكَ": ("", "PARTICLE", "PARTICLE"),
    "أَفَمَا": ("", "PARTICLE", "PARTICLE"),
    "أَفَبِهَٰذَا": ("", "PARTICLE", "PARTICLE"),
    "أَنَحْنُ": ("", "PARTICLE", "PARTICLE"),
    "أَهَٰكَذَا": ("", "PARTICLE", "PARTICLE"),
    "أَئِنَّ": ("", "PARTICLE", "PARTICLE"),
    "أَئِن": ("", "PARTICLE", "PARTICLE"),
    "إِى": ("", "PARTICLE", "PARTICLE"),
    "إِلْ": ("", "PARTICLE", "PARTICLE"),  # shortened إلا or إلى
    "إِنَّهُنَّ": ("", "PARTICLE", "PARTICLE"),
    "كِلْتَا": ("", "PARTICLE", "PARTICLE"),

    # ── ISOLATED LETTERS / SPECIAL ──
    "عٓسٓقٓ": ("", "SKIP", ""),  # Muqatta'at
    "طه": ("", "SKIP", ""),  # Muqatta'at

    # ── Remaining verb forms ──
    "ءَايَٰتِهَا": ("ء-ي-ي", "ROOT", "L8:MANUAL"),  # āyāt = signs
    "ءَايَتَيْنِ": ("ء-ي-ي", "ROOT", "L8:MANUAL"),
}


def main():
    conn = _uslap_connect(DB) if _HAS_WRAPPER else sqlite3.connect(DB)
    conn.execute("PRAGMA foreign_keys = ON")
    c = conn.cursor()

    # Get all UNROOTED
    c.execute("SELECT word_id, arabic_word FROM quran_word_roots WHERE confidence = 'UNROOTED'")
    rows = c.fetchall()
    print(f"Total UNROOTED rows: {len(rows)}")

    rooted = 0
    particled = 0
    skipped = 0
    unmapped = 0
    unmapped_words = set()

    for word_id, word in rows:
        if word in MAPPING:
            root, cat, method = MAPPING[word]
            if cat == "ROOT":
                c.execute("""
                    UPDATE quran_word_roots
                    SET root = ?, confidence = 'MEDIUM_B', match_method = ?
                    WHERE word_id = ?
                """, (root, method, word_id))
                rooted += 1
            elif cat == "PARTICLE":
                c.execute("""
                    UPDATE quran_word_roots
                    SET confidence = 'PARTICLE', match_method = 'PARTICLE'
                    WHERE word_id = ?
                """, (word_id,))
                particled += 1
            elif cat == "SKIP":
                skipped += 1
        else:
            unmapped += 1
            unmapped_words.add(word)

    conn.commit()

    print(f"\nResults:")
    print(f"  Rooted → MEDIUM_B: {rooted}")
    print(f"  Reclassified → PARTICLE: {particled}")
    print(f"  Skipped (muqatta'at etc): {skipped}")
    print(f"  Unmapped (still UNROOTED): {unmapped}")

    if unmapped_words:
        print(f"\n  Unmapped unique forms ({len(unmapped_words)}):")
        for w in sorted(unmapped_words):
            print(f"    {w}")

    # Final stats
    c.execute("""
        SELECT confidence, COUNT(*)
        FROM quran_word_roots
        GROUP BY confidence
        ORDER BY COUNT(*) DESC
    """)
    print(f"\nFinal distribution:")
    for row in c.fetchall():
        print(f"  {row[0]}: {row[1]}")

    conn.close()


if __name__ == "__main__":
    main()
