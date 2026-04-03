#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
أَمْر ALPHABET I18N EXPORT — Generate multilingual letter data via tarjama pipeline.

Flow: amr_alphabet (letter → top roots) → amr_tarjama (root → all siblings) → JSON

This ensures ALL translations come from the DB, routed through AMR AI. Zero weights.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amr_alphabet import ALPHABET, ABJAD, all_letters_28, compute_root_meaning_text
from amr_tarjama import مُتَرْجِم


def extract_letter_siblings():
    """
    For each of the 28 letters, take its top roots from amr_alphabet,
    run each through tarjama expansion, collect EN/RU/DE/UZ siblings.
    """
    translator = مُتَرْجِم()
    result = {}

    for letter in all_letters_28():
        data = ALPHABET.get(letter)
        if not data:
            continue

        qs = data.get('quranic_stats', {})
        # Collect all top roots from all positions
        top_roots = set()
        for key in ('top5_first', 'top5_second', 'top5_third'):
            for root_tuple in (qs.get(key) or []):
                if root_tuple and len(root_tuple) >= 1:
                    top_roots.add(root_tuple[0])  # root_letters string like 'ك-ت-ب'

        # Expand each root through tarjama
        en_words = []
        ru_words = []
        de_words = []
        uz_words = []
        root_meanings = []

        for root_str in sorted(top_roots):
            try:
                # Get AMR meaning from alphabet
                amr_meaning = compute_root_meaning_text(root_str)
                if amr_meaning:
                    root_meanings.append({'root': root_str, 'amr': amr_meaning})

                # Try recognition by root letters directly
                expansion = translator.وَسِّعْ(
                    root_id=None,
                    root_letters=root_str,
                )

                # Also try finding root_id from roots table
                root_bare = root_str.replace('-', '')
                root_row = translator._q1(
                    'SELECT root_id FROM roots WHERE root_letters = ? OR root_bare = ?',
                    (root_str, root_bare)
                )
                if root_row:
                    expansion2 = translator.وَسِّعْ(
                        root_id=root_row['root_id'],
                        root_letters=root_str,
                    )
                    # Merge
                    for key in expansion2:
                        if isinstance(expansion2[key], list) and expansion2[key]:
                            existing = expansion.get(key, [])
                            if isinstance(existing, list):
                                for item in expansion2[key]:
                                    if item not in existing:
                                        existing.append(item)
                                expansion[key] = existing

                # Collect siblings from tarjama expansion
                for w in (expansion.get('إِنْجِلِيزِي') or []):
                    if w and w not in en_words:
                        en_words.append(w)
                for w in (expansion.get('رُوسِي') or []):
                    if w and w not in ru_words:
                        ru_words.append(w)
                for w in (expansion.get('أَلْمَانِي') or []):
                    if w and w not in de_words:
                        de_words.append(w)
                for w in (expansion.get('أُزْبَكِي') or []):
                    if w and w not in uz_words:
                        uz_words.append(w)

                # Direct DB query for EN/RU from entries table
                root_bare = root_str.replace('-', '')
                try:
                    rows = translator._q(
                        "SELECT en_term, ru_term FROM entries "
                        "WHERE root_letters = ? OR root_letters = ?",
                        (root_str, root_bare)
                    )
                    for r in rows:
                        en = (r.get('en_term') or '').strip()
                        ru = (r.get('ru_term') or '').strip()
                        if en and en not in en_words:
                            en_words.append(en)
                        if ru and ru not in ru_words:
                            ru_words.append(ru)
                except Exception:
                    pass

                # Direct DB query for UZ from uzbek_vocabulary
                try:
                    uz_rows = translator._q(
                        "SELECT uz_latin FROM uzbek_vocabulary WHERE aa_root = ?",
                        (root_str,)
                    )
                    for r in uz_rows:
                        uz = (r.get('uz_latin') or '').strip()
                        if uz and uz not in uz_words:
                            uz_words.append(uz)
                except Exception:
                    pass

            except Exception as e:
                print(f"  Warning: {root_str} → {e}", file=sys.stderr)

        # Also check uzbek_vocabulary for roots starting with this letter
        try:
            uz_extra = translator._q(
                "SELECT uz_latin, uz_meaning, aa_root FROM uzbek_vocabulary "
                "WHERE aa_root LIKE ? LIMIT 10",
                (f'{letter}-%',)
            )
            for r in uz_extra:
                entry = r.get('uz_latin', '')
                if entry and entry not in uz_words:
                    uz_words.append(entry)
        except Exception:
            pass

        result[letter] = {
            'name': data['name'],
            'transliteration': data['transliteration'],
            'abjad': data['abjad'],
            'top_roots': [{'root': rm['root'], 'amr': rm['amr']} for rm in root_meanings[:5]],
            'en': en_words[:15],
            'ru': ru_words[:15],
            'de': de_words[:15],
            'uz': uz_words[:15],
        }

        count = f"EN:{len(en_words)} RU:{len(ru_words)} DE:{len(de_words)} UZ:{len(uz_words)}"
        print(f"  {letter} ({data['name']}) — roots:{len(top_roots)} — {count}")

    return result


if __name__ == '__main__':
    print("أَمْر ALPHABET I18N EXPORT")
    print("=" * 50)
    print("Pipeline: amr_alphabet → amr_tarjama → DB → JSON")
    print()

    data = extract_letter_siblings()

    output_path = os.path.join(os.path.dirname(__file__), 'amr_alphabet_i18n.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    total_en = sum(len(v['en']) for v in data.values())
    total_ru = sum(len(v['ru']) for v in data.values())
    total_de = sum(len(v['de']) for v in data.values())
    total_uz = sum(len(v['uz']) for v in data.values())

    print()
    print(f"Output: {output_path}")
    print(f"Letters: {len(data)}")
    print(f"Total siblings — EN:{total_en} RU:{total_ru} DE:{total_de} UZ:{total_uz}")
