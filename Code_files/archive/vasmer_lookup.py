"""
Vasmer Dictionary Integration Module for USLaP Russian Engine.

Pre-processing layer that provides corridor, era, morpheme, and prefix data
for Russian words BEFORE phonetic tracing. Data sourced from Vasmer's
Etymological Dictionary (vasmer_articles.csv, 18,279 entries).

Usage:
    from vasmer_lookup import VasmerLookup
    vl = VasmerLookup('/path/to/vasmer_articles.csv')
    result = vl.lookup('банк')
    # Returns dict with corridor, era, morphemes, prefix, r14_corridor, etc.

Integration with USLaP Engine:
    Called by the RU pipeline InputRouter BEFORE PhoneticReversal.
    The r14_corridor value determines which corridor to trace through (R14 rule).
    The prefix_detected value triggers OP_RU_PREFIX stripping (R12 rule).
"""

import csv
import re
import unicodedata
from collections import defaultdict
from typing import Optional


def _strip_accents(text: str) -> str:
    """Strip Unicode accent marks from text, preserving base Cyrillic characters.

    Uses NFD normalization to decompose characters, then removes all
    combining marks (category 'Mn'). Result is lowercased.

    Example: бары́ш -> барыш, у́тро -> утро
    """
    normalized = unicodedata.normalize('NFD', text)
    stripped = ''.join(c for c in normalized if unicodedata.category(c) != 'Mn')
    return stripped.lower()


def _strip_html(text: str) -> str:
    """Remove HTML tags like <i>...</i> from text."""
    return re.sub(r'</?[^>]+>', '', text)


class VasmerLookup:
    """Pre-processing layer for Russian etymological data from Vasmer's dictionary.

    Loads Vasmer CSV into memory on init. Provides lookup by accent-stripped
    word, corridor detection (R14-compatible), era detection, prefix detection,
    morpheme extraction, word family search, and batch processing.
    """

    # Known Russian prefixes (OP_RU_PREFIX, R12)
    PREFIXES = [
        'пере', 'пред', 'рас', 'раз', 'вос', 'воз', 'над', 'под', 'при',
        'про', 'пре', 'вы', 'до', 'за', 'из', 'на', 'об', 'от', 'по', 'с', 'у',
    ]

    # Corridor detection markers — order matters: more specific before less specific
    CORRIDOR_MARKERS = {
        'turkic': [
            r'др\.-тюрк\b', r'тюрк\.',  r'чагат\.', r'крым\.-тат\b',
            r'(?<!\w)тур\.', r'(?<!\w)тат\.', r'кирг\.', r'(?<!\w)каз\.',
            r'узб\.', r'кыпч\.', r'алт\.', r'уйг\.', r'башк\.', r'якут\.',
            r'монг\.', r'калм\.',
        ],
        'arabic': [
            r'(?<!\w)араб\.', r'\(араб\.\)',
        ],
        'greek': [
            r'(?<!\w)греч\.', r'ср\.-греч\.', r'нов\.-греч\.',
            r'визант\.',
        ],
        'church_slavonic': [
            r'ст\.-слав\.', r'цслав\.', r'церк\.-слав\.',
        ],
        'latin': [
            r'(?<!\w)лат\.', r'ср\.-лат\.', r'позднелат\.',
        ],
        'german': [
            r'(?<!\w)нем\.', r'д\.-в\.-н\.', r'ср\.-в\.-н\.',
            r'ср\.-нж\.-н\.', r'голл\.', r'нж\.-нем\.',
        ],
        'french': [
            r'франц\.',
        ],
        'italian': [
            r'(?<!\w)ит\.',
        ],
        'persian': [
            r'нов\.-перс\.', r'(?<!\w)перс\.', r'ср\.-перс\.',
        ],
        'slavic': [
            r'праслав\.', r'др\.-русск\.',
        ],
    }

    # Era detection markers
    ERA_MARKERS = {
        'proto_slavic': [
            r'праслав\.',
            # Asterisk for reconstructed proto-Slavic forms only:
            # Must be preceded by "праслав." or Slavic-context markers within ~50 chars
            # The bare *word pattern is handled specially in detect_era()
        ],
        'old_russian': [
            r'др\.-русск\.',
        ],
        'church_slavonic': [
            r'ст\.-слав\.', r'цслав\.', r'церк\.-слав\.',
        ],
        '17th_century': [
            r'XVII\s*в\.', r'XVI\s*в\.',
            r'1[56]\d\d\s*г\.',
        ],
        '18th_century': [
            r'XVIII\s*в\.', r'XIX\s*в\.',
            r'1[78]\d\d\s*г\.',
        ],
        'modern': [
            r'XX\s*в\.', r'19[0-9]{2}\s*г\.', r'20[0-9]{2}\s*г\.',
        ],
    }

    # Corridor priority for R14 classification when multiple corridors detected.
    # Lower index = higher priority (direct borrowing source takes precedence).
    CORRIDOR_PRIORITY = [
        'turkic', 'arabic', 'persian', 'italian', 'french',
        'german', 'latin', 'greek', 'church_slavonic', 'slavic',
    ]

    def __init__(self, csv_path: str):
        """Load Vasmer CSV into memory. Strip accents from all words for lookup.

        Args:
            csv_path: Path to vasmer_articles.csv (tab-separated).

        Stores entries in a dict keyed by accent-stripped lowercase word.
        Multiple entries for the same word are stored as a list.
        """
        self._entries: dict[str, list[dict]] = defaultdict(list)
        self._raw_entries: list[dict] = []
        self._csv_path = csv_path
        self._load(csv_path)

    def _load(self, csv_path: str) -> None:
        """Parse the CSV file and populate the lookup dictionary."""
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter='\t')
            for row in reader:
                word_raw = row.get('word', '').strip()
                if not word_raw:
                    continue

                entry = {
                    'word_raw': word_raw,
                    'forms': row.get('forms', '') or '',
                    'general': row.get('general', '') or '',
                    'origin': row.get('origin', '') or '',
                    'trubachev': row.get('trubachev', '') or '',
                    'editorial': row.get('editorial', '') or '',
                    'pages': row.get('pages', '') or '',
                }

                key = _strip_accents(word_raw)
                self._entries[key].append(entry)
                self._raw_entries.append(entry)

    def lookup(self, word: str) -> list[dict] | None:
        """Look up a Russian word. Returns None if not found.

        Accent marks in the query are stripped automatically.
        Returns a list of result dicts (one per Vasmer entry for the word).

        Each result dict contains:
            word_raw: str           - Original word with accents
            corridor: str           - Detected corridor code
            corridor_detail: str    - Raw text snippet showing corridor evidence
            era: str                - Detected era code
            era_detail: str         - Raw text showing era evidence
            morphemes: list         - Related forms found
            prefix_detected: str|None - Detected prefix, if any
            vasmer_origin: str      - Full origin text (truncated to 500 chars)
            vasmer_general: str     - Full general text (truncated to 500 chars)
            r14_corridor: str       - R14-classified corridor
        """
        key = _strip_accents(word)
        entries = self._entries.get(key)
        if not entries:
            return None

        results = []
        for entry in entries:
            general = entry['general']
            origin = entry['origin']
            combined_text = general + ' ' + origin

            corridor, corridor_detail = self.detect_corridor(origin, general)
            era, era_detail = self.detect_era(combined_text)
            morphemes = self._extract_morphemes(word, general)
            prefix = self.detect_prefix(word, general)
            r14 = self.map_to_r14(corridor, era)

            results.append({
                'word_raw': entry['word_raw'],
                'corridor': corridor,
                'corridor_detail': corridor_detail,
                'era': era,
                'era_detail': era_detail,
                'morphemes': morphemes,
                'prefix_detected': prefix,
                'vasmer_origin': origin[:500] if origin else '',
                'vasmer_general': general[:500] if general else '',
                'r14_corridor': r14,
            })

        return results

    def detect_corridor(self, origin_text: str, general_text: str) -> tuple[str, str]:
        """Parse Vasmer origin/general fields to detect the primary borrowing corridor.

        Uses a three-phase approach:
        1. Check for EXPLICIT borrowing phrases in general_text (highest confidence):
           "заимств. из X", "из X ... из Y", "через X из Y"
        2. Check for language markers in general_text ONLY (medium confidence):
           general_text contains the borrowing/definition context.
        3. Check origin_text ONLY if it contains a borrowing phrase (lowest confidence):
           origin_text is usually comparative etymology (IE comparanda), NOT
           borrowing sources. Markers in origin without "заимств." or "из" are
           comparative mentions and should NOT determine corridor.

        This prevents false positives where Vasmer compares a word with Old High
        German, Sanskrit, etc. for etymology but the word was never borrowed from
        those languages.

        Args:
            origin_text: The 'origin' column text from Vasmer.
            general_text: The 'general' column text from Vasmer.

        Returns:
            (corridor_code, evidence_snippet) where corridor_code is one of:
            'turkic', 'greek', 'latin', 'arabic', 'german', 'french',
            'italian', 'persian', 'slavic', 'church_slavonic', 'unknown'
        """
        # ── Phase 1: Explicit borrowing phrases ──────────────────────
        # These are the strongest signals: "заимств. из X", "из X ...",
        # "через X из Y", "восходит к X"
        borrow_patterns = [
            # "заимствовано из тур." / "заимств. из нем."
            r'заимств(?:\w*)?\.?\s+из\s+(\S+)',
            # "из франц. abordage" at start
            r'^из\s+(\S+)',
            # "через нем. Bank из ит. banco" — captures the deeper source
            r'через\s+\S+\s+\S+\s+из\s+(\S+)',
            # "восходит к лат."
            r'восходит\s+(?:к|через\s+\S+\s+к)\s+(\S+)',
        ]

        for bp in borrow_patterns:
            match = re.search(bp, general_text, re.IGNORECASE)
            if match:
                lang_token = match.group(1).lower().rstrip('.,;:')
                for corridor, patterns in self.CORRIDOR_MARKERS.items():
                    for pattern in patterns:
                        if re.search(pattern, lang_token):
                            start = max(0, match.start() - 30)
                            end = min(len(general_text), match.end() + 50)
                            snippet = general_text[start:end].strip()
                            return (corridor, snippet)

        # Also check for chains: "из нем. X из ит. Y" — find ALL "из <lang>"
        chain_matches = re.findall(
            r'из\s+(\S+)', general_text, re.IGNORECASE
        )
        for lang_token in chain_matches:
            lang_clean = lang_token.lower().rstrip('.,;:')
            for corridor, patterns in self.CORRIDOR_MARKERS.items():
                for pattern in patterns:
                    if re.search(pattern, lang_clean):
                        # Find position for snippet
                        pos = general_text.lower().find(lang_clean)
                        if pos >= 0:
                            start = max(0, pos - 40)
                            end = min(len(general_text), pos + 60)
                            snippet = general_text[start:end].strip()
                            return (corridor, snippet)

        # ── Phase 2: Language markers in general_text only ───────────
        # general_text describes the word's history and borrowing context.
        detected_general = []
        for corridor, patterns in self.CORRIDOR_MARKERS.items():
            for pattern in patterns:
                match = re.search(pattern, general_text)
                if match:
                    start = max(0, match.start() - 50)
                    end = min(len(general_text), match.end() + 50)
                    snippet = general_text[start:end].strip()
                    detected_general.append((corridor, snippet, match.start()))
                    break

        if detected_general:
            # Use corridor priority
            for priority_corridor in self.CORRIDOR_PRIORITY:
                for d in detected_general:
                    if d[0] == priority_corridor:
                        return (d[0], d[1])
            return (detected_general[0][0], detected_general[0][1])

        # ── Phase 3: Origin text — ONLY if it has a borrowing phrase ──
        # origin_text is comparative etymology. We only check it if it
        # contains an explicit borrowing statement.
        origin_has_borrowing = bool(re.search(
            r'(?:заимств|из\s+(?:тур|тюрк|араб|перс|нем|франц|ит\.|лат|греч|голл))',
            origin_text,
            re.IGNORECASE,
        ))

        if origin_has_borrowing:
            for corridor, patterns in self.CORRIDOR_MARKERS.items():
                for pattern in patterns:
                    match = re.search(pattern, origin_text)
                    if match:
                        start = max(0, match.start() - 50)
                        end = min(len(origin_text), match.end() + 50)
                        snippet = origin_text[start:end].strip()
                        return (corridor, snippet)

        return ('unknown', '')

    def detect_era(self, text: str) -> tuple[str, str]:
        """Parse for era indicators in the combined general+origin text.

        Uses a two-phase approach:
        1. Check for explicit era markers (праслав., др.-русск., etc.)
        2. For proto_slavic, also check for reconstructed forms (*word) but
           ONLY when preceded by a Slavic-context marker within ~80 chars.
           This prevents false positives from non-Slavic reconstructions
           (e.g., Chuvash *parǝš, Proto-Germanic *jaukiþô).

        Args:
            text: Combined general and origin text from Vasmer entry.

        Returns:
            (era_code, evidence_snippet) where era_code is one of:
            'proto_slavic', 'old_russian', 'church_slavonic',
            '17th_century', '18th_century', 'modern', 'unknown'
        """
        # Priority order: most specific/earliest era first
        era_priority = [
            'proto_slavic', 'old_russian', 'church_slavonic',
            '17th_century', '18th_century', 'modern',
        ]

        for era in era_priority:
            for pattern in self.ERA_MARKERS[era]:
                match = re.search(pattern, text)
                if match:
                    start = max(0, match.start() - 30)
                    end = min(len(text), match.end() + 30)
                    snippet = text[start:end].strip()
                    return (era, snippet)

        # Additional check for proto_slavic: reconstructed *word forms
        # Only valid if preceded by Slavic context within ~80 chars
        slavic_context = re.compile(
            r'(?:праслав|слав|др\.-русск|ст\.-слав|польск|чеш|болг|сербохорв|словен|в\.-луж|н\.-луж)\.'
        )
        for m in re.finditer(r'(?:праслав\.\s+)\*[а-яА-Яa-zA-Z]', text):
            start = max(0, m.start() - 30)
            end = min(len(text), m.end() + 30)
            snippet = text[start:end].strip()
            return ('proto_slavic', snippet)

        return ('unknown', '')

    def detect_prefix(self, word: str, general_text: str) -> Optional[str]:
        """Check if Vasmer shows this word as prefixed.

        Two detection methods:
        1. Cross-reference: if Vasmer general_text contains "см. <base_word>"
           and the word starts with a known prefix + that base_word.
        2. Direct prefix check: if the word starts with a known prefix and
           the remaining stem appears as a separate Vasmer entry.

        Args:
            word: The Russian word to check (accent-stripped).
            general_text: The 'general' column text from Vasmer.

        Returns:
            The prefix string if detected, None otherwise.
        """
        word_clean = _strip_accents(word)
        general_clean = _strip_html(general_text).lower()

        # Method 1: Check if general_text has a "см. <root_word>" reference
        # that corresponds to our word minus a prefix
        see_refs = re.findall(r'см\.\s+([а-яё]+)', general_clean)

        for ref_word in see_refs:
            ref_stripped = _strip_accents(ref_word)
            # Check if our word = prefix + ref_word
            for prefix in self.PREFIXES:
                if word_clean == prefix + ref_stripped:
                    return prefix
                # Handle consonant assimilation at prefix boundary
                # e.g., рас+сказать -> рассказать
                if word_clean.startswith(prefix) and ref_stripped and \
                   word_clean[len(prefix):].startswith(ref_stripped[0]) and \
                   word_clean[len(prefix) + 1:] == ref_stripped[1:]:
                    # Possible gemination at boundary
                    return prefix

        # Method 2: Direct prefix detection — check if word starts with a known
        # prefix AND the stem is a known Vasmer entry
        for prefix in sorted(self.PREFIXES, key=len, reverse=True):
            if word_clean.startswith(prefix) and len(word_clean) > len(prefix) + 1:
                stem = word_clean[len(prefix):]
                if stem in self._entries:
                    return prefix

        # Method 3: Check if the general_text lists related prefixed forms,
        # implying the current word IS the root
        # e.g., казать lists "выказать, показать, сказать, отказать, приказать"
        prefixed_forms = re.findall(r'([а-яё]+а́?ть)', general_clean)
        for form in prefixed_forms:
            form_stripped = _strip_accents(form)
            for prefix in self.PREFIXES:
                if form_stripped.startswith(prefix):
                    stem = form_stripped[len(prefix):]
                    if word_clean.endswith(stem) and word_clean == stem:
                        # The current word IS the root, and the listed forms are
                        # prefixed derivatives. Return None (no prefix on THIS word).
                        return None

        return None

    def _extract_morphemes(self, word: str, general_text: str) -> list[str]:
        """Extract related morphological forms from Vasmer's general field.

        Searches for Cyrillic words in the general_text that share the same
        root stem (last 3+ characters), plus any explicitly cross-referenced
        forms (italicized words, "сюда же", "см." references).

        Args:
            word: The lookup word (will be accent-stripped).
            general_text: The 'general' column text.

        Returns:
            List of related Russian word forms (accent-stripped, deduplicated).
        """
        word_clean = _strip_accents(word)
        general_clean = _strip_html(general_text)

        # Extract all Cyrillic words from the text
        all_words = re.findall(r'[а-яёА-ЯЁ][а-яёА-ЯЁ]+', general_clean)

        morphemes = set()
        for w in all_words:
            w_stripped = _strip_accents(w)
            # Skip the word itself, very short words, and non-Russian
            if w_stripped == word_clean or len(w_stripped) < 3:
                continue
            # Keep words that share a root stem (3+ chars of the base)
            # Only for words that look like Russian (not OCS or other Slavic)
            if len(word_clean) >= 3:
                root_stem = word_clean[-3:]
                # Check if this word contains our root stem
                if root_stem in w_stripped:
                    morphemes.add(w_stripped)

        # Also extract explicitly referenced forms
        # Pattern: "сюда же X, Y, Z" or explicit cross-references
        syuda_match = re.search(r'сюда\s+же\s+(.+?)(?:\.|$)', general_clean)
        if syuda_match:
            refs = re.findall(r'[а-яёА-ЯЁ][а-яёА-ЯЁ]+', syuda_match.group(1))
            for r in refs:
                r_stripped = _strip_accents(r)
                if r_stripped != word_clean and len(r_stripped) >= 3:
                    morphemes.add(r_stripped)

        return sorted(morphemes)

    def map_to_r14(self, corridor: str, era: str) -> str:
        """Map corridor + era combination to R14 classification.

        R14 (Era-Based Corridor Rule for Russian) determines which corridor
        to trace through based on WHEN the word entered Russian.

        Rules (from CLAUDE.md R14):
            1. turkic corridor -> ORIG2_bitig (primary Russian corridor)
            2. arabic corridor -> DIRECT_AA (Islamic terms entered directly)
            3. greek corridor + church_slavonic/old_russian era -> DS04_greek
            4. latin/italian/french/german corridor -> DS05_latin (post-Andalus)
            5. persian corridor -> DS09_persian
            6. proto_slavic era (regardless of corridor) -> SLAVIC_substrate
            7. church_slavonic corridor (even without explicit era) -> DS04_greek
            8. Otherwise -> UNKNOWN

        Args:
            corridor: Detected corridor code from detect_corridor().
            era: Detected era code from detect_era().

        Returns:
            R14 classification string.
        """
        # Rules 1 & 2 FIRST: explicit Turkic or Arabic borrowing overrides
        # any era classification. A word borrowed from Turkic is ORIG2_bitig
        # even if the text also mentions proto-Slavic comparanda.
        # Rule 1: Turkic corridor = ORIG2
        if corridor == 'turkic':
            return 'ORIG2_bitig'

        # Rule 2: Arabic corridor = direct AA contact
        if corridor == 'arabic':
            return 'DIRECT_AA'

        # Rule 6: Proto-Slavic era = deepest layer (only after ruling out
        # explicit borrowing corridors above)
        if era == 'proto_slavic':
            return 'SLAVIC_substrate'

        # Rule 3: Greek corridor (especially with Church Slavonic or Old Russian era)
        if corridor == 'greek':
            return 'DS04_greek'

        # Rule 7: Church Slavonic corridor implies Greek via Orthodox Church
        if corridor == 'church_slavonic':
            return 'DS04_greek'

        # Rule 4: Latin/Romance/Germanic corridors = DS05 (post-Andalus Western)
        if corridor in ('latin', 'italian', 'french', 'german'):
            return 'DS05_latin'

        # Rule 5: Persian corridor
        if corridor == 'persian':
            return 'DS09_persian'

        # Rule for Slavic substrate (without proto_slavic era marker)
        if corridor == 'slavic':
            if era in ('old_russian', 'church_slavonic'):
                return 'SLAVIC_substrate'
            return 'SLAVIC_substrate'

        return 'UNKNOWN'

    def get_word_family(self, word: str) -> dict[str, list[str]]:
        """Return all words sharing the same root by searching cross-references.

        Searches all Vasmer entries for references to the given word (via
        "см." cross-references and shared root stems). Groups results into:
        - 'prefixed': words that add a prefix to the root
        - 'derived': words derived from the root (suffixed/compounded)
        - 'cross_ref': words explicitly cross-referenced by Vasmer

        Args:
            word: The root word to search for (accent-stripped).

        Returns:
            Dict with keys 'prefixed', 'derived', 'cross_ref', each a list of words.
        """
        word_clean = _strip_accents(word)
        family = {
            'prefixed': [],
            'derived': [],
            'cross_ref': [],
        }

        # Method 1: Search for cross-references TO this word across all entries
        see_pattern = re.compile(
            r'см\.\s+' + re.escape(word_clean),
            re.IGNORECASE,
        )
        # Also search with accent variants
        for key, entries in self._entries.items():
            if key == word_clean:
                continue
            for entry in entries:
                general_stripped = _strip_accents(_strip_html(entry['general']))
                # Check for cross-reference
                if see_pattern.search(general_stripped):
                    if key not in family['cross_ref']:
                        family['cross_ref'].append(key)
                    break

        # Method 2: Find prefixed forms
        for prefix in self.PREFIXES:
            prefixed = prefix + word_clean
            if prefixed in self._entries and prefixed not in family['prefixed']:
                family['prefixed'].append(prefixed)
            # Handle verbs: prefix + root with possible stem vowel changes
            # e.g., казать -> показать, сказать, указать
            for stem_variant in [word_clean, word_clean[:-2] + 'ать' if len(word_clean) > 3 else '']:
                if not stem_variant:
                    continue
                pv = prefix + stem_variant
                if pv in self._entries and pv not in family['prefixed']:
                    family['prefixed'].append(pv)

        # Method 3: Check the root entry's own general_text for listed derivatives
        root_entries = self._entries.get(word_clean, [])
        for entry in root_entries:
            general_clean = _strip_accents(_strip_html(entry['general']))
            # Extract Cyrillic words that start with any known prefix + root stem
            all_words = re.findall(r'[а-яё]+', general_clean)
            for w in all_words:
                if w == word_clean or len(w) < 4:
                    continue
                for prefix in self.PREFIXES:
                    if w.startswith(prefix):
                        stem = w[len(prefix):]
                        # Check if stem relates to root (shares 3+ chars)
                        if len(word_clean) >= 3 and word_clean[:3] in stem:
                            if w not in family['prefixed']:
                                family['prefixed'].append(w)
                            break

        # Deduplicate and sort
        for key in family:
            family[key] = sorted(set(family[key]))

        return family

    def batch_lookup(self, words: list[str]) -> dict[str, list[dict] | None]:
        """Look up multiple words efficiently.

        Args:
            words: List of Russian words to look up.

        Returns:
            Dict mapping each word to its lookup result (list of dicts or None).
        """
        results = {}
        for word in words:
            results[word] = self.lookup(word)
        return results

    def stats(self) -> dict:
        """Return basic statistics about the loaded Vasmer data.

        Returns:
            Dict with:
                total_entries: int - Total number of entries loaded
                unique_words: int - Number of unique (accent-stripped) words
                multi_entry_words: int - Words with multiple entries
                corridor_distribution: dict - Count per corridor
                era_distribution: dict - Count per era
                r14_distribution: dict - Count per R14 classification
        """
        corridor_dist = defaultdict(int)
        era_dist = defaultdict(int)
        r14_dist = defaultdict(int)

        for key, entries in self._entries.items():
            for entry in entries:
                general = entry['general']
                origin = entry['origin']
                combined = general + ' ' + origin

                corridor, _ = self.detect_corridor(origin, general)
                era, _ = self.detect_era(combined)
                r14 = self.map_to_r14(corridor, era)

                corridor_dist[corridor] += 1
                era_dist[era] += 1
                r14_dist[r14] += 1

        multi = sum(1 for v in self._entries.values() if len(v) > 1)

        return {
            'total_entries': len(self._raw_entries),
            'unique_words': len(self._entries),
            'multi_entry_words': multi,
            'corridor_distribution': dict(sorted(
                corridor_dist.items(), key=lambda x: -x[1]
            )),
            'era_distribution': dict(sorted(
                era_dist.items(), key=lambda x: -x[1]
            )),
            'r14_distribution': dict(sorted(
                r14_dist.items(), key=lambda x: -x[1]
            )),
        }

    def search_text(self, query: str, field: str = 'general',
                    max_results: int = 20) -> list[dict]:
        """Search across all entries for a text pattern in a specific field.

        Useful for finding entries that mention a specific language, concept,
        or cross-reference.

        Args:
            query: Regex pattern to search for.
            field: Which field to search ('general', 'origin', 'trubachev', 'editorial').
            max_results: Maximum number of results to return.

        Returns:
            List of entry dicts matching the query.
        """
        pattern = re.compile(query, re.IGNORECASE)
        results = []
        for entry in self._raw_entries:
            text = entry.get(field, '')
            if text and pattern.search(text):
                results.append({
                    'word': entry['word_raw'],
                    'word_clean': _strip_accents(entry['word_raw']),
                    'match_field': field,
                    'text': text[:300],
                })
                if len(results) >= max_results:
                    break
        return results


# ─────────────────────────────────────────────────────────────────────
# Self-test when run directly
# ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    import os
    import sys

    CSV_PATH = os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        '..', 'Reference Data', 'vasmer_articles.csv'
    )
    if not os.path.exists(CSV_PATH):
        print(f'CSV not found at: {CSV_PATH}')
        sys.exit(1)

    print('Loading Vasmer dictionary...')
    vl = VasmerLookup(CSV_PATH)
    print(f'Loaded. {vl.stats()["total_entries"]} entries, '
          f'{vl.stats()["unique_words"]} unique words.\n')

    # ── Test suite ──────────────────────────────────────────────────
    tests_passed = 0
    tests_total = 0

    def test(name, condition, detail=''):
        global tests_passed, tests_total
        tests_total += 1
        status = 'PASS' if condition else 'FAIL'
        if condition:
            tests_passed += 1
        print(f'  [{status}] {name}')
        if detail:
            print(f'         {detail}')
        if not condition:
            print(f'         ^^^ EXPECTED TO PASS')

    # ── Test 1: БАНК ──
    print('=== TEST: БАНК ===')
    result = vl.lookup('банк')
    assert result is not None, 'БАНК not found'
    r = result[0]
    print(f'  corridor={r["corridor"]}, r14={r["r14_corridor"]}')
    print(f'  corridor_detail: {r["corridor_detail"][:100]}')
    print(f'  vasmer_general: {r["vasmer_general"][:150]}')
    test('БАНК found', result is not None)
    test('БАНК corridor=italian', r['corridor'] == 'italian',
         f'got: {r["corridor"]}')
    test('БАНК r14=DS05_latin', r['r14_corridor'] == 'DS05_latin',
         f'got: {r["r14_corridor"]}')
    print()

    # ── Test 2: БАРЫШ ──
    print('=== TEST: БАРЫШ ===')
    result = vl.lookup('барыш')
    assert result is not None, 'БАРЫШ not found'
    r = result[0]
    print(f'  corridor={r["corridor"]}, r14={r["r14_corridor"]}')
    print(f'  corridor_detail: {r["corridor_detail"][:100]}')
    test('БАРЫШ found', result is not None)
    test('БАРЫШ corridor=turkic', r['corridor'] == 'turkic',
         f'got: {r["corridor"]}')
    test('БАРЫШ r14=ORIG2_bitig', r['r14_corridor'] == 'ORIG2_bitig',
         f'got: {r["r14_corridor"]}')
    print()

    # ── Test 3: ДЕНЬ ──
    print('=== TEST: ДЕНЬ ===')
    result = vl.lookup('день')
    assert result is not None, 'ДЕНЬ not found'
    r = result[0]
    print(f'  era={r["era"]}, era_detail: {r["era_detail"][:100]}')
    test('ДЕНЬ found', result is not None)
    # ДЕНЬ has "ст.-слав." marker in general text, which maps to church_slavonic
    # era, plus origin has deeper IE comparanda. The era should pick up the
    # Old Russian or Church Slavonic era from the general text.
    test('ДЕНЬ era is proto_slavic or church_slavonic or old_russian',
         r['era'] in ('proto_slavic', 'church_slavonic', 'old_russian'),
         f'got: {r["era"]}')
    print()

    # ── Test 4: УТРО ──
    print('=== TEST: УТРО ===')
    result = vl.lookup('утро')
    assert result is not None, 'УТРО not found'
    r = result[0]
    print(f'  corridor={r["corridor"]}, r14={r["r14_corridor"]}')
    print(f'  vasmer_origin: {r["vasmer_origin"][:150]}')
    test('УТРО found', result is not None)
    # Vasmer says "Этимология затруднительна" — no clear corridor
    # But the entry mentions "праслав. *jutro" which gives era=proto_slavic
    test('УТРО era=proto_slavic',
         r['era'] == 'proto_slavic',
         f'got: {r["era"]}')
    # The corridor could be 'slavic' or 'unknown' depending on marker detection
    # Since it mentions "др.-русск." and "ст.-слав." but no borrowing source
    test('УТРО corridor is slavic or church_slavonic or unknown',
         r['corridor'] in ('slavic', 'church_slavonic', 'unknown'),
         f'got: {r["corridor"]}')
    print()

    # ── Test 5: КАЗАТЬ ──
    print('=== TEST: КАЗАТЬ (word family) ===')
    result = vl.lookup('казать')
    assert result is not None, 'КАЗАТЬ not found'
    r = result[0]
    print(f'  morphemes: {r["morphemes"]}')
    family = vl.get_word_family('казать')
    print(f'  word family prefixed: {family["prefixed"]}')
    print(f'  word family cross_ref: {family["cross_ref"]}')
    test('КАЗАТЬ found', result is not None)

    # The general text explicitly lists: выказать, показать, сказать, отказать,
    # приказать, указ, приказ, рассказ
    expected_family = ['указ', 'приказ', 'рассказ', 'сказать', 'показать']
    morphemes_set = set(r['morphemes'])
    family_all = set(family['prefixed'] + family['cross_ref'])
    combined = morphemes_set | family_all

    found_targets = []
    for target in expected_family:
        target_clean = _strip_accents(target)
        if target_clean in combined:
            found_targets.append(target)
    test(f'КАЗАТЬ family includes expected words',
         len(found_targets) >= 3,
         f'found: {found_targets} out of {expected_family}')
    print()

    # ── Test 6: Multi-entry word ──
    print('=== TEST: Multi-entry handling ===')
    result = vl.lookup('а')
    test('Multi-entry word "а" returns list',
         result is not None and len(result) >= 2,
         f'got {len(result) if result else 0} entries')
    print()

    # ── Test 7: Batch lookup ──
    print('=== TEST: Batch lookup ===')
    batch = vl.batch_lookup(['банк', 'барыш', 'несуществующее'])
    test('Batch returns all keys',
         set(batch.keys()) == {'банк', 'барыш', 'несуществующее'})
    test('Batch: missing word returns None',
         batch['несуществующее'] is None)
    test('Batch: found words have results',
         batch['банк'] is not None and batch['барыш'] is not None)
    print()

    # ── Test 8: Stats ──
    print('=== TEST: Stats ===')
    s = vl.stats()
    print(f'  Total entries: {s["total_entries"]}')
    print(f'  Unique words: {s["unique_words"]}')
    print(f'  Multi-entry: {s["multi_entry_words"]}')
    print(f'  Corridor dist: {s["corridor_distribution"]}')
    print(f'  Era dist: {s["era_distribution"]}')
    print(f'  R14 dist: {s["r14_distribution"]}')
    test('Stats total_entries ~18279',
         17000 < s['total_entries'] < 20000,
         f'got: {s["total_entries"]}')
    test('Stats has corridor distribution',
         len(s['corridor_distribution']) > 0)
    print()

    # ── Test 9: Additional corridor tests ──
    print('=== TEST: Additional corridor checks ===')
    # КАЗНА — should be turkic (from тур.)
    result = vl.lookup('казна')
    if result:
        r = result[0]
        print(f'  КАЗНА: corridor={r["corridor"]}, r14={r["r14_corridor"]}')
        test('КАЗНА corridor=turkic', r['corridor'] == 'turkic',
             f'got: {r["corridor"]}')

    # АБАЖУР — should be french
    result = vl.lookup('абажур')
    if result:
        r = result[0]
        print(f'  АБАЖУР: corridor={r["corridor"]}, r14={r["r14_corridor"]}')
        test('АБАЖУР corridor=french', r['corridor'] == 'french',
             f'got: {r["corridor"]}')

    # АБЗАЦ — should be german
    result = vl.lookup('абзац')
    if result:
        r = result[0]
        print(f'  АБЗАЦ: corridor={r["corridor"]}, r14={r["r14_corridor"]}')
        test('АБЗАЦ corridor=german', r['corridor'] == 'german',
             f'got: {r["corridor"]}')

    # АБДАЛ — from (араб.) тур. → should detect turkic or arabic
    result = vl.lookup('абдал')
    if result:
        r = result[0]
        print(f'  АБДАЛ: corridor={r["corridor"]}, r14={r["r14_corridor"]}')
        test('АБДАЛ corridor is turkic or arabic',
             r['corridor'] in ('turkic', 'arabic'),
             f'got: {r["corridor"]}')
    print()

    # ── Test 10: Prefix detection ──
    print('=== TEST: Prefix detection ===')
    result = vl.lookup('сказать')
    if result:
        r = result[0]
        print(f'  СКАЗАТЬ: prefix={r["prefix_detected"]}')
        test('СКАЗАТЬ prefix detected as "с"',
             r['prefix_detected'] == 'с',
             f'got: {r["prefix_detected"]}')
    print()

    # ── Summary ──
    print(f'\n{"="*50}')
    print(f'TESTS: {tests_passed}/{tests_total} passed')
    if tests_passed == tests_total:
        print('ALL TESTS PASSED.')
    else:
        print(f'{tests_total - tests_passed} test(s) FAILED.')
    print(f'{"="*50}')
