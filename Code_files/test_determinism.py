#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
USLaP Determinism Test
بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ

Run the same query 3 times. If ANY difference exists, the system is not deterministic.
If all three are identical, USLaP is working correctly — zero LLM in the loop.
"""

import sys
import os
import re

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from amr_dhakaa import think

# Strip timestamps from output (they will differ)
TIMESTAMP_RE = re.compile(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}')


def strip_timestamps(text):
    return TIMESTAMP_RE.sub('[TIMESTAMP]', text)


def test_query(query_text, runs=3):
    """Run a query N times and compare outputs."""
    outputs = []
    for i in range(runs):
        result = think(query_text)
        output = strip_timestamps(result['output'])
        outputs.append(output)

    # Compare
    all_same = all(o == outputs[0] for o in outputs)
    return {
        'query': query_text,
        'runs': runs,
        'deterministic': all_same,
        'outputs': outputs,
    }


def main():
    test_queries = [
        "trace silk",
        "explain R01",
        "search empire",
        "DP10",
        "state",
    ]

    print("═" * 60)
    print("USLaP DETERMINISM TEST")
    print("═" * 60)
    print()

    all_pass = True
    for q in test_queries:
        result = test_query(q)
        status = "✓ DETERMINISTIC" if result['deterministic'] else "✗ NON-DETERMINISTIC"
        print(f"  [{status}] '{q}'")

        if not result['deterministic']:
            all_pass = False
            print(f"    DIFF FOUND:")
            for i, o in enumerate(result['outputs']):
                print(f"    Run {i+1}: {o[:80]}...")

    print()
    print("─" * 60)
    if all_pass:
        print("✓ ALL QUERIES DETERMINISTIC — Zero LLM in the loop.")
    else:
        print("✗ SOME QUERIES NON-DETERMINISTIC — LLM leak detected.")
    print("═" * 60)

    return 0 if all_pass else 1


if __name__ == '__main__':
    sys.exit(main())
