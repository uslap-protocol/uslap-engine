#!/usr/bin/env python3
"""
USLaP Chronology → term_nodes Connector
=========================================
Yasin (NARRATIVE) layer — sequences the lattice in time.

Reads all 96 chronology entries, matches entity mentions to
existing term_nodes, and creates CHRONOLOGICAL dimension edges
in term_dimensions.

Usage:
  python3 uslap_chrono_connect.py scan      # show matches (dry run)
  python3 uslap_chrono_connect.py connect    # write edges to DB
  python3 uslap_chrono_connect.py status     # show current CHRONOLOGICAL edges
"""
import sqlite3, sys, os, re

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uslap_database_v3.db')


def get_term_lookup(conn):
    """Build lookup: normalized_term → list of (node_id, term, source_table, source_id)."""
    rows = conn.execute("""
        SELECT node_id, term, term_normal, source_table, source_id, root_id
        FROM term_nodes
        WHERE entry_type IN ('WORD', 'COUNTRY', 'PEOPLE', 'ROOT', 'DERIVATIVE')
    """).fetchall()

    lookup = {}
    for node_id, term, term_normal, src_tbl, src_id, root_id in rows:
        # Index by normalized term
        key = term_normal.lower().strip() if term_normal else term.lower().strip()
        if key not in lookup:
            lookup[key] = []
        lookup[key].append((node_id, term, src_tbl, src_id, root_id))

        # Also index by original term (for Arabic)
        key2 = term.lower().strip()
        if key2 != key:
            if key2 not in lookup:
                lookup[key2] = []
            lookup[key2].append((node_id, term, src_tbl, src_id, root_id))

    return lookup


# ── EXPLICIT MAPPING ──
# Chronology entries mention concepts that map to specific lattice entries.
# This is curated, not fuzzy-matched, to ensure quality.
CHRONO_NODE_MAP = {
    # C01: Yusuf treasurer of Misr
    'C01': [
        ('a6_country_names', 'CN16', 'مِصْر — location of event'),
        ('a1_entries', '13', 'MAGAZINE (خَزَائِنِ الْأَرْضِ — treasures/stores)'),
    ],
    # C02: Ya'qub enters Misr
    'C02': [
        ('a6_country_names', 'CN16', 'مِصْر — destination'),
    ],
    # C03: Hyksos period in Misr
    'C03': [
        ('a6_country_names', 'CN16', 'مِصْر — location'),
    ],
    # C05: Musa vs Fir'awn — Fir'awn drowned
    'C05': [
        ('a6_country_names', 'CN16', 'مِصْر — location'),
        ('a1_entries', '252', 'GREECE = غَرَق (drowning event)'),
    ],
    # C07: Greece named after drowning
    'C07': [
        ('a1_entries', '252', 'GREECE = غَرَق — naming origin'),
    ],
    # C08: Rome / Latin / al-Lat
    'C08': [
        ('a6_country_names', 'CN05', 'ROME — naming event'),
        ('a6_country_names', 'CN02', 'ITALY — corridor'),
        ('latin_a1_entries', '1', 'VERUS — Latin corridor'),
    ],
    # C14: Septuagint - Injil through DS04
    'C14': [],
    # C15: Babel → Bible
    'C15': [],
    # C16: Gospel = khasf
    'C16': [],
    # C19: Caesar assigns Germani = jurm to Almania = iman
    'C19': [
        ('a6_country_names', 'CN07', 'GERMANY = جُرْم — naming'),
        ('a6_country_names', 'CN10', 'ALMANIA = إِيمَان — original name'),
        ('a1_entries', '224', 'ALMANIA entry'),
    ],
    # C20: Nasara → Christians = Quraysh
    'C20': [],
    # C23: Attila = utul
    'C23': [
        ('a6_country_names', 'CN42', 'Itil/Ata-Illah — Attila same compound'),
    ],
    # C24: Radhanite slave trade, Salwa → Slavic → slave
    'C24': [],
    # C25: First Hijrah to Habasha
    'C25': [],
    # C27: Khazar conversion
    'C27': [],
    # C28: Toledo gates, Andalus
    'C28': [
        ('a6_country_names', 'CN11', 'AL-ANDALUS — location'),
        ('a6_country_names', 'CN24', 'SPAIN — modern wrapper'),
    ],
    # C32-C37: Mongol era
    'C33': [],
    # C38: England cycle, Aaron of Lincoln
    'C38': [],
    # C41: Spain 1492
    'C41': [
        ('a6_country_names', 'CN24', 'SPAIN — location'),
    ],
    # C45: Richthofen invents "Silk Road"
    'C45': [],
    # C47: Soviet 15 SSRs
    'C47': [
        ('a6_country_names', 'CN26', 'RUSSIA — operator state'),
    ],
    # C48: Latin script forced
    'C48': [],
    # C49: Holodomor
    'C49': [
        ('a6_country_names', 'CN26', 'RUSSIA / Soviet — operator state'),
    ],
    # C50: Iran renamed
    'C50': [
        ('a6_country_names', 'CN12', 'IRAN/PERSIA — renamed'),
    ],
    # C53: Palestine renamed
    'C53': [
        ('a6_country_names', 'CN16', 'مِصْر → "Egypt" — naming formalized'),
    ],
    # C54: Federal Reserve
    'C54': [],
    # C55: WWI Germany
    'C55': [
        ('a6_country_names', 'CN07', 'GERMANY — جُرْم function deployed'),
    ],
    # C56: WWII
    'C56': [
        ('a6_country_names', 'CN07', 'GERMANY — جُرْم function deployed again'),
    ],
    # C57: 9/11 chain
    'C57': [
        ('a6_country_names', 'CN20', 'IRAQ — target'),
        ('a6_country_names', 'CN28', 'LIBYA — target'),
        ('a6_country_names', 'CN21', 'SYRIA — target'),
        ('a6_country_names', 'CN12', 'IRAN — target'),
    ],
    # C58: Greece debt crisis = gharaq
    'C58': [
        ('a1_entries', '252', 'GREECE = غَرَق — still drowning'),
    ],
    # C59: Ukraine operation
    'C59': [
        ('a6_country_names', 'CN26', 'RUSSIA — Pontic-Caspian zone'),
    ],
    # C60: Iran Purim Strike
    'C60': [
        ('a6_country_names', 'CN12', 'IRAN — target'),
    ],
    # C62: Dawud received Zabur
    'C62': [],
    # C63: Sulayman peak governance
    'C63': [],
    # C65: Phoenician corridor
    'C65': [],
    # C69: Nebuchadnezzar, Babel
    'C69': [],
    # C70: Khazar destruction
    'C70': [
        ('a6_country_names', 'CN26', 'RUSSIA — Sviatoslav of Kiev'),
    ],
    # C71: Norman Conquest, England
    'C71': [],
    # C72: Kashgari Diwan
    'C72': [],
    # C76: Aaron of Lincoln
    'C76': [],
    # C80: Cromwell readmits
    'C80': [],
    # C81: Glorious Revolution
    'C81': [],
    # C82: Bank of England
    'C82': [],
    # C84: Rothschild Frankfurt
    'C84': [
        ('a6_country_names', 'CN07', 'GERMANY — Frankfurt base'),
    ],
    # C86: American Revolution
    'C86': [
        ('a6_country_names', 'CN03', 'AMERICA — financed'),
    ],
    # C87: French Revolution
    'C87': [
        ('a6_country_names', 'CN06', 'FRANCE = فِرْعَوْن function'),
    ],
    # C88: Napoleon invades Misr
    'C88': [
        ('a6_country_names', 'CN16', 'مِصْر — invaded'),
        ('a6_country_names', 'CN06', 'FRANCE — operator'),
    ],
    # C90: Opium Wars, China
    'C90': [
        ('a6_country_names', 'CN17', 'CHINA — forced open'),
    ],
    # C93: Suez Canal
    'C93': [
        ('a6_country_names', 'CN16', 'مِصْر / Suez — location'),
        ('a6_country_names', 'CN04', 'AFRICA — physically separated'),
    ],
    # C94: Aliyah to Holy Land
    'C94': [],
    # C95: Berlin Conference, Africa
    'C95': [
        ('a6_country_names', 'CN04', 'AFRICA — divided'),
        ('a6_country_names', 'CN07', 'GERMANY — Berlin Conference'),
    ],
    # C96: Cecil Rhodes, Africa
    'C96': [
        ('a6_country_names', 'CN04', 'AFRICA — extraction'),
    ],
}

# ── AUTO-MATCH: scan chronology text for known terms ──
AUTO_KEYWORDS = {
    # Country/place mentions → A6 nodes
    'مِصْر': ('a6_country_names', 'CN16'),
    'misr': ('a6_country_names', 'CN16'),
    'egypt': ('a6_country_names', 'CN16'),
    'greece': ('a1_entries', '252'),
    'غَرَق': ('a1_entries', '252'),
    'rome': ('a6_country_names', 'CN05'),
    'الرُّوم': ('a6_country_names', 'CN05'),
    'france': ('a6_country_names', 'CN06'),
    'فِرْعَوْن': ('a6_country_names', 'CN06'),
    'germany': ('a6_country_names', 'CN07'),
    'جُرْم': ('a6_country_names', 'CN07'),
    'almania': ('a6_country_names', 'CN10'),
    'إِيمَان': ('a6_country_names', 'CN10'),
    'andalus': ('a6_country_names', 'CN11'),
    'iran': ('a6_country_names', 'CN12'),
    'persia': ('a6_country_names', 'CN12'),
    'china': ('a6_country_names', 'CN17'),
    'iraq': ('a6_country_names', 'CN20'),
    'syria': ('a6_country_names', 'CN21'),
    'spain': ('a6_country_names', 'CN24'),
    'russia': ('a6_country_names', 'CN26'),
    'ukraine': ('a6_country_names', 'CN26'),
    'kiev': ('a6_country_names', 'CN26'),
    'america': ('a6_country_names', 'CN03'),
    'africa': ('a6_country_names', 'CN04'),
    'libya': ('a6_country_names', 'CN28'),
    'بَابِل': ('a1_entries', '15'),  # Babel if entry exists
    'khazar': ('a6_country_names', 'CN42'),
    'itil': ('a6_country_names', 'CN42'),
    'attila': ('a6_country_names', 'CN42'),
    'الحَبَشَة': ('a6_country_names', 'CN29'),  # Habasha → closest A6
    'treasury': ('a1_entries', '13'),  # MAGAZINE = treasury
    'خَزَائِنِ': ('a1_entries', '13'),
    'magazine': ('a1_entries', '13'),
    'empire': ('a1_entries', '1'),
    'أَمْر': ('a1_entries', '1'),
    'military': ('a1_entries', '2'),
    'sultan': ('a1_entries', '7'),
    'tariff': ('a1_entries', '15'),
    'risk': ('a1_entries', '18'),
    'algebra': ('a1_entries', '8'),
    'madrasa': ('a1_entries', '19'),
    'caliphate': ('a1_entries', '4'),
    'jihad': ('a1_entries', '5'),
    'sharia': ('a1_entries', '6'),
    'arsenal': ('a1_entries', '14'),
    'india': ('a6_country_names', 'CN08'),
    'brazil': ('a6_country_names', 'CN27'),
    'bahrain': ('a6_country_names', 'CN14'),
    'yemen': ('a6_country_names', 'CN15'),
    'jordan': ('a6_country_names', 'CN18'),
    'sudan': ('a6_country_names', 'CN19'),
    'algeria': ('a6_country_names', 'CN22'),
    'tunisia': ('a6_country_names', 'CN23'),
    'turkey': ('a6_country_names', 'CN25'),
    'somalia': ('a6_country_names', 'CN30'),
    'morocco': ('a6_country_names', 'CN13'),
    'eritrea': ('a6_country_names', 'CN29'),
}


def find_node_id(conn, source_table, source_id):
    """Find node_id for a given source_table + source_id."""
    row = conn.execute(
        "SELECT node_id FROM term_nodes WHERE source_table=? AND source_id=?",
        (source_table, str(source_id))
    ).fetchone()
    return row[0] if row else None


def auto_match_chrono(conn, chrono_id, event_text, notes_text):
    """Auto-detect entity mentions in chronology text."""
    matches = set()
    full_text = (event_text or '') + ' ' + (notes_text or '')
    full_lower = full_text.lower()

    for keyword, (src_tbl, src_id) in AUTO_KEYWORDS.items():
        if keyword.lower() in full_lower:
            node_id = find_node_id(conn, src_tbl, src_id)
            if node_id:
                matches.add((node_id, src_tbl, src_id, f'auto:{keyword}'))

    return matches


def scan_matches(conn):
    """Scan all chronology entries and show potential matches."""
    chrono_rows = conn.execute("SELECT * FROM chronology ORDER BY id").fetchall()
    cols = [d[0] for d in conn.execute("PRAGMA table_info(chronology)").fetchall()]
    col_map = {c: i for i, (_, c, *_) in enumerate(conn.execute("PRAGMA table_info(chronology)").fetchall())}

    total_edges = 0
    edge_list = []

    for row in chrono_rows:
        cid = row[0]  # id
        date = row[1]
        era = row[2]
        event = row[3]
        notes = row[13] if len(row) > 13 else ''

        matches = set()

        # 1. Curated matches
        if cid in CHRONO_NODE_MAP:
            for src_tbl, src_id, label in CHRONO_NODE_MAP[cid]:
                node_id = find_node_id(conn, src_tbl, src_id)
                if node_id:
                    matches.add((node_id, src_tbl, src_id, label))

        # 2. Auto-matches from text
        auto = auto_match_chrono(conn, cid, event, notes)
        matches.update(auto)

        if matches:
            print(f"\n  {cid} | {date} | {era}")
            print(f"  Event: {(event or '')[:90]}")
            for node_id, src_tbl, src_id, label in sorted(matches):
                print(f"    → node {node_id} ({src_tbl}/{src_id}): {label}")
                edge_list.append((node_id, cid, date, label))
            total_edges += len(matches)

    print(f"\n  ══════════════════════════════════════")
    print(f"  TOTAL CHRONOLOGICAL EDGES: {total_edges}")
    print(f"  Covering {len(set(e[1] for e in edge_list))}/{len(chrono_rows)} chronology entries")
    print(f"  Linking to {len(set(e[0] for e in edge_list))} unique term_nodes")

    return edge_list


def connect(conn):
    """Write CHRONOLOGICAL edges to term_dimensions."""
    # Get max edge_id
    max_id = conn.execute("SELECT MAX(edge_id) FROM term_dimensions").fetchone()[0] or 0

    # Check existing CHRONOLOGICAL edges
    existing = conn.execute(
        "SELECT COUNT(*) FROM term_dimensions WHERE dimension='CHRONOLOGICAL'"
    ).fetchone()[0]

    if existing > 0:
        print(f"  WARNING: {existing} CHRONOLOGICAL edges already exist.")
        print(f"  Use 'status' to view them. Skipping to avoid duplicates.")
        print(f"  To rebuild: DELETE FROM term_dimensions WHERE dimension='CHRONOLOGICAL';")
        return

    chrono_rows = conn.execute("SELECT * FROM chronology ORDER BY id").fetchall()

    edge_id = max_id + 1
    edges_written = 0

    for row in chrono_rows:
        cid = row[0]
        date = row[1]
        event = row[3]
        notes = row[13] if len(row) > 13 else ''

        matches = set()

        # Curated
        if cid in CHRONO_NODE_MAP:
            for src_tbl, src_id, label in CHRONO_NODE_MAP[cid]:
                node_id = find_node_id(conn, src_tbl, src_id)
                if node_id:
                    matches.add((node_id, src_tbl, src_id, label))

        # Auto
        auto = auto_match_chrono(conn, cid, event, notes)
        matches.update(auto)

        # Deduplicate: one edge per (node_id, chrono_id) — prefer curated label
        seen_nodes = {}
        for node_id, src_tbl, src_id, label in matches:
            if node_id not in seen_nodes or not label.startswith('auto:'):
                seen_nodes[node_id] = (src_tbl, src_id, label)

        for node_id, (src_tbl, src_id, label) in seen_nodes.items():
            conn.execute(
                "INSERT INTO term_dimensions (edge_id, node_id, dimension, target_table, target_id, label) VALUES (?,?,?,?,?,?)",
                (edge_id, node_id, 'CHRONOLOGICAL', 'chronology', cid, f"{date}: {label}")
            )
            edge_id += 1
            edges_written += 1

    conn.commit()
    print(f"\n  CHRONOLOGICAL EDGES WRITTEN: {edges_written}")
    print(f"  Edge IDs: {max_id+1} – {edge_id-1}")

    # Verify
    total = conn.execute("SELECT dimension, COUNT(*) FROM term_dimensions GROUP BY dimension ORDER BY COUNT(*) DESC").fetchall()
    print(f"\n  DIMENSION SUMMARY (post-connect):")
    for dim, cnt in total:
        marker = ' ← NEW' if dim == 'CHRONOLOGICAL' else ''
        print(f"    {dim:20s} {cnt:>6,}{marker}")


def status(conn):
    """Show current CHRONOLOGICAL edges."""
    edges = conn.execute("""
        SELECT td.edge_id, tn.term, td.target_id, td.label
        FROM term_dimensions td
        JOIN term_nodes tn ON td.node_id = tn.node_id
        WHERE td.dimension = 'CHRONOLOGICAL'
        ORDER BY td.target_id
    """).fetchall()

    if not edges:
        print("  No CHRONOLOGICAL edges exist yet. Run: python3 uslap_chrono_connect.py connect")
        return

    print(f"  CHRONOLOGICAL EDGES: {len(edges)}")
    for eid, term, target, label in edges:
        print(f"    {target:5s} → {term:20s} | {label}")


if __name__ == '__main__':
    mode = sys.argv[1] if len(sys.argv) > 1 else 'scan'
    conn = sqlite3.connect(DB_PATH)

    print(f"══ Yasin (NARRATIVE) — Chronology Connector ══\n")

    if mode == 'scan':
        scan_matches(conn)
    elif mode == 'connect':
        connect(conn)
    elif mode == 'status':
        status(conn)
    else:
        print(f"Unknown mode: {mode}. Use: scan | connect | status")

    conn.close()
