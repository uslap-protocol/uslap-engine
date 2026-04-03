# ═══════════════════════════════════════════════════════════════════════════════
# DOMAIN VALIDATORS — RETIRED (2026-03-28)
# QUF validation now lives in AMR AI modules (amr_quf.py router).
# System 2 domain propagation has been replaced by:
#   amr_aql.py       → linguistic_quf, divine_quf, bitig_quf, sibling_quf, etc.
#   amr_istakhbarat.py → behaviour_quf
#   amr_hisab.py     → formula_quf
#   amr_jism.py      → body_quf
#   amr_tarikh.py    → history_quf
#   amr_basar.py     → detection_quf
#   amr_keywords.py  → keyword_quf
#
# The phonetic engine above (validate_q_gate, validate_u_gate, validate_f_gate)
# is KEPT — it's the real consonant alignment work, imported by amr_aql.py.
#
# To run QUF validation, use: python3 amr_quf.py validate --table TABLE --id ID
# ═══════════════════════════════════════════════════════════════════════════════

def _dquf_roots(row, ctx):
    r = QUFResult()
    rid = row.get('root_id', '')
    rtype = row.get('root_type', '')
    tokens = row.get('quran_tokens', 0) or 0
    letters = row.get('root_letters', '')
    bare = row.get('root_bare', '')
    bitig = row.get('bitig_attested', False)
    bitig_src = row.get('bitig_source', '')

    is_orig2 = 'ORIG2' in (rtype or '') or (rid or '').startswith('T')

    # Q — L1-Root: countable attestation
    if is_orig2:
        if bitig and bitig_src:
            r.q_grade = 'HIGH'
            r.q_evidence.append(f'ORIG2 bitig-attested, source: {str(bitig_src)[:30]}')
        elif bitig:
            r.q_grade = 'MEDIUM'
            r.q_evidence.append('ORIG2 bitig-attested, no source detail')
        else:
            r.q_grade = 'PENDING'
            r.q_evidence.append('ORIG2 awaiting Kashgari/bitig attestation')
    else:
        if tokens >= 50:
            r.q_grade = 'HIGH'
            r.q_evidence.append(f'{tokens} Quranic tokens')
        elif tokens > 0:
            r.q_grade = 'HIGH'
            r.q_evidence.append(f'{tokens} Quranic tokens')
        else:
            r.q_grade = 'PENDING'
            r.q_evidence.append('AA root, 0 tokens — pre-Quranic or compound')

    # U — L1-Root: surah spread + sibling coverage
    spread = ctx.surah_spread.get(letters, 0)
    siblings = ctx.sibling_counts.get(rid, {})
    sib_count = len(siblings)

    if is_orig2:
        if sib_count >= 2:
            r.u_grade = 'HIGH'
            r.u_evidence.append(f'ORIG2 in {sib_count} sibling tables')
        elif sib_count >= 1:
            r.u_grade = 'MEDIUM'
            r.u_evidence.append(f'ORIG2 in {sib_count} sibling table')
        else:
            r.u_grade = 'PENDING'
            r.u_evidence.append('ORIG2 no sibling entries yet')
    else:
        if spread >= 20:
            r.u_grade = 'HIGH'
            r.u_evidence.append(f'Across {spread} surahs, {sib_count} siblings')
        elif spread >= 5 or sib_count >= 3:
            r.u_grade = 'HIGH'
            r.u_evidence.append(f'{spread} surahs, {sib_count} siblings')
        elif spread >= 1 or sib_count >= 1:
            r.u_grade = 'MEDIUM'
            r.u_evidence.append(f'{spread} surahs, {sib_count} siblings')
        else:
            r.u_grade = 'PENDING'
            r.u_evidence.append('No surah/sibling attestation yet')

    # F — L1-Root: consistency + not blacklisted
    if is_orig2:
        if any(t in ctx.bl_terms for t in [str(bare).lower(), str(letters).lower()]):
            r.f_grade = 'FAIL'
            r.f_evidence.append('In contamination blacklist')
        elif bitig and bitig_src:
            r.f_grade = 'HIGH'
            r.f_evidence.append('ORIG2 attested, not blacklisted')
        else:
            r.f_grade = 'MEDIUM'
            r.f_evidence.append('ORIG2 not blacklisted')
    else:
        if tokens > 0:
            r.f_grade = 'HIGH'
            r.f_evidence.append('Empirically attested in Quran')
        elif bare and letters:
            r.f_grade = 'MEDIUM'
            r.f_evidence.append('Root defined, awaiting token linkage')
        else:
            r.f_grade = 'LOW'
            r.f_evidence.append('No empirical attestation')
    return r


def _dquf_quran_word_roots(row, ctx):
    r = QUFResult()
    root = row.get('root', '')
    word = row.get('arabic_word', '')
    surah = row.get('surah', 0)
    conf = row.get('confidence', '')

    # Q — L4-QuranicForms: data present + valid surah
    if root and word and surah and 1 <= (surah or 0) <= 114:
        r.q_grade = 'HIGH'
        r.q_evidence.append(f'Q{surah}, root={root}')
    elif root and word:
        r.q_grade = 'MEDIUM'
        r.q_evidence.append(f'Root+word present')
    else:
        r.q_grade = 'LOW'
        r.q_evidence.append('Missing root or word')

    # U — L4-QuranicForms: root matches roots table
    if root and (root in ctx.letters_to_id or root in ctx.root_tokens):
        r.u_grade = 'HIGH'
        r.u_evidence.append('Root linked to roots table')
    elif root and root != 'None':
        r.u_grade = 'MEDIUM'
        r.u_evidence.append('Root populated but no exact match in roots table')
    else:
        r.u_grade = 'LOW'
        r.u_evidence.append('No root linkage')

    # F — L4-QuranicForms: confidence grade
    conf_str = str(conf).upper() if conf else ''
    if conf_str in ('HIGH', 'MEDIUM_A'):
        r.f_grade = 'HIGH'
    elif conf_str in ('MEDIUM_B', 'MEDIUM_C', 'MEDIUM'):
        r.f_grade = 'MEDIUM'
    elif conf_str:
        r.f_grade = 'LOW'
    else:
        r.f_grade = 'MEDIUM'  # No confidence = default MEDIUM (Quran data)
    r.f_evidence.append(f'Compiler confidence: {conf_str or "ungraded"}')
    return r


def _dquf_quran_known_forms(row, ctx):
    r = QUFResult()
    form = row.get('arabic_form', '')
    root_un = row.get('root_unhyphenated', '')
    wtype = row.get('word_type', '')

    r.q_grade = 'HIGH' if (form and root_un and wtype) else ('MEDIUM' if form else 'LOW')
    r.q_evidence.append(f'form={bool(form)}, root={bool(root_un)}, type={wtype}')

    if root_un and root_un in ctx.bare_to_id:
        r.u_grade = 'HIGH'
        r.u_evidence.append(f'Root {root_un} → {ctx.bare_to_id[root_un]}')
    elif root_un:
        r.u_grade = 'MEDIUM'
        r.u_evidence.append(f'Root {root_un} not matched to root_id')
    else:
        r.u_grade = 'LOW'

    valid_types = {'NAME', 'NOUN', 'VERB', 'PARTICLE', 'PRONOUN', 'PREPOSITION', 'CONJUNCTION', 'ADJECTIVE'}
    if wtype and wtype.upper() in valid_types:
        r.f_grade = 'HIGH'
    elif wtype:
        r.f_grade = 'MEDIUM'
    else:
        r.f_grade = 'LOW'
    r.f_evidence.append(f'word_type={wtype}')
    return r


def _dquf_names_of_allah(row, ctx):
    r = QUFResult()
    rid = row.get('root_id', '')
    qref = row.get('qur_ref', '')
    name = row.get('arabic_name', '')
    aid = row.get('allah_id', '')

    r.q_grade = 'HIGH' if (rid and qref and name) else ('MEDIUM' if name else 'LOW')
    r.q_evidence.append(f'root={rid}, qur_ref={bool(qref)}')

    tokens = ctx.root_tokens.get(rid, 0)
    has_entries = bool(ctx.allah_entry_refs.get(aid))
    if tokens > 0 and has_entries:
        r.u_grade = 'HIGH'
    elif tokens > 0:
        r.u_grade = 'HIGH'  # Name of Allah with Quranic root = universal
    else:
        r.u_grade = 'MEDIUM'
    r.u_evidence.append(f'tokens={tokens}, entry_refs={has_entries}')

    r.f_grade = 'HIGH'  # Names of Allah are axiomatic
    r.f_evidence.append('Divine name — axiomatic')
    return r


def _dquf_entries(row, ctx):
    r = QUFResult()
    rid = row.get('root_id', '')
    chain = row.get('phonetic_chain', '')
    score = row.get('score', 0) or 0
    eid = row.get('entry_id', '')
    inv = row.get('inversion_type', '')
    dp = row.get('dp_codes', '')

    # Q — L5-Entries: attestation
    root_valid = rid in ctx.root_tokens
    chain_ok = bool(chain and len(str(chain)) > 2)
    score_ok = score > 0
    q_count = sum([root_valid, chain_ok, score_ok])
    r.q_grade = 'HIGH' if q_count >= 3 else ('MEDIUM' if q_count >= 2 else ('LOW' if q_count >= 1 else 'FAIL'))
    r.q_evidence.append(f'root={root_valid}, chain={chain_ok}, score={score}')

    # U — L5-Entries: root universality
    tokens = ctx.root_tokens.get(rid, 0)
    siblings = ctx.sibling_counts.get(rid, {})
    sib_count = len(siblings)
    if tokens > 0 and sib_count >= 2:
        r.u_grade = 'HIGH'
    elif tokens > 0 or sib_count >= 1:
        r.u_grade = 'MEDIUM'
    else:
        r.u_grade = 'PENDING'
    r.u_evidence.append(f'tokens={tokens}, siblings={sib_count}')

    # F — L5-Entries: shift chain validity
    if chain:
        shifts_in_chain = re.findall(r'S\d{2}', str(chain))
        unknowns = [s for s in shifts_in_chain if s not in ctx.known_shifts]
        if not unknowns and shifts_in_chain:
            r.f_grade = 'HIGH'
            r.f_evidence.append(f'{len(shifts_in_chain)} shifts, all known')
        elif unknowns:
            r.f_grade = 'LOW'
            r.f_evidence.append(f'Unknown shifts: {unknowns}')
        else:
            r.f_grade = 'MEDIUM'
            r.f_evidence.append('Chain present, no shift IDs extracted')
    else:
        r.f_grade = 'LOW'
        r.f_evidence.append('No phonetic chain')

    if inv and not dp:
        r.f_grade = 'LOW'
        r.f_evidence.append(f'Inversion {inv} but no DP codes')
    return r


def _dquf_european(row, ctx):
    r = QUFResult()
    rid = row.get('root_id', '')
    chain = row.get('phonetic_chain', '')
    score = row.get('score', 0) or 0

    root_valid = rid in ctx.root_tokens
    r.q_grade = 'HIGH' if (root_valid and chain and score > 0) else ('MEDIUM' if root_valid else 'LOW')
    r.q_evidence.append(f'root={root_valid}, chain={bool(chain)}, score={score}')

    tokens = ctx.root_tokens.get(rid, 0)
    en_exists = rid in ctx.sibling_counts and 'en' in ctx.sibling_counts[rid]
    if tokens > 0 and en_exists:
        r.u_grade = 'HIGH'
    elif tokens > 0:
        r.u_grade = 'MEDIUM'
    else:
        r.u_grade = 'PENDING'
    r.u_evidence.append(f'tokens={tokens}, EN parent={en_exists}')

    if chain:
        shifts = re.findall(r'S\d{2}', str(chain))
        unknowns = [s for s in shifts if s not in ctx.known_shifts]
        r.f_grade = 'HIGH' if (not unknowns and shifts) else ('MEDIUM' if not unknowns else 'LOW')
    else:
        r.f_grade = 'MEDIUM'
    r.f_evidence.append(f'chain={bool(chain)}')
    return r


def _dquf_latin(row, ctx):
    return _dquf_european(row, ctx)  # Same logic


def _dquf_bitig(row, ctx):
    r = QUFResult()
    kash = row.get('kashgari_attestation', '')
    ibn = row.get('ibn_sina_attestation', '')
    navoi = row.get('navoi_attestation', '')
    rid = row.get('root_id', '')
    disp = row.get('dispersal_range', '')

    # Q — L6-Bitig: dated attestation
    if kash:
        r.q_grade = 'HIGH'
        r.q_evidence.append(f'Kashgari 1072: {str(kash)[:30]}')
    elif ibn or navoi:
        r.q_grade = 'MEDIUM'
        r.q_evidence.append(f'Ibn Sina/Navoi attested')
    else:
        r.q_grade = 'PENDING'
        r.q_evidence.append('No historical attestation')

    # U — L6-Bitig: dispersal + root linkage
    if rid and rid in ctx.root_tokens:
        r.u_grade = 'HIGH' if disp else 'MEDIUM'
    elif rid:
        r.u_grade = 'MEDIUM'
    else:
        r.u_grade = 'PENDING'
    r.u_evidence.append(f'root={rid}, dispersal={bool(disp)}')

    # F — not laundered AA, not blacklisted
    orig2_term = str(row.get('orig2_term', '')).lower()
    if orig2_term in ctx.bl_terms:
        r.f_grade = 'FAIL'
        r.f_evidence.append('In contamination blacklist')
    elif kash:
        r.f_grade = 'HIGH'
        r.f_evidence.append('Kashgari-attested, not blacklisted')
    else:
        r.f_grade = 'MEDIUM'
        r.f_evidence.append('Not blacklisted')
    return r


def _dquf_uzbek(row, ctx):
    r = QUFResult()
    otype = row.get('orig_type', '')
    aa_rid = row.get('aa_root_id', '')
    bitig_eid = row.get('bitig_entry_id', '')
    kash = row.get('kashgari_form', '')

    if otype == 'ORIG1':
        valid = aa_rid and aa_rid in ctx.root_tokens
        tokens = ctx.root_tokens.get(aa_rid, 0)
        r.q_grade = 'HIGH' if (valid and tokens > 0) else ('MEDIUM' if valid else 'PENDING')
        r.q_evidence.append(f'ORIG1: root={aa_rid}, tokens={tokens}')
        r.u_grade = 'HIGH' if tokens > 0 else 'PENDING'
        r.u_evidence.append(f'Quranic tokens={tokens}')
        r.f_grade = 'HIGH' if tokens > 0 else 'MEDIUM'
        r.f_evidence.append('ORIG1 traceable to Quran')
    else:  # ORIG2
        r.q_grade = 'HIGH' if (bitig_eid or kash) else 'PENDING'
        r.q_evidence.append(f'ORIG2: bitig={bool(bitig_eid)}, kashgari={bool(kash)}')
        r.u_grade = 'HIGH' if kash else ('MEDIUM' if bitig_eid else 'PENDING')
        r.u_evidence.append(f'Kashgari={bool(kash)}')
        r.f_grade = 'MEDIUM' if not any(str(row.get('uz_latin','')).lower() in ctx.bl_terms for _ in [1]) else 'FAIL'
        r.f_evidence.append('ORIG2 not blacklisted' if r.f_grade != 'FAIL' else 'Blacklisted')
    return r


def _dquf_derivatives(row, ctx):
    r = QUFResult()
    eid = row.get('entry_id')
    link = row.get('link_type', '')

    # Q — L7-Derivatives: parent exists + link type
    parent_exists = eid in ctx.valid_entries
    link_ok = link and link.upper() in ctx.permitted_links
    r.q_grade = 'HIGH' if (parent_exists and link_ok) else ('MEDIUM' if parent_exists else 'LOW')
    r.q_evidence.append(f'parent={parent_exists}, link={link}')

    # U — parent root has tokens
    if parent_exists:
        # Get parent's root_id
        parent_root = None
        for rid, sibs in ctx.sibling_counts.items():
            if 'en' in sibs:
                parent_root = rid
                break
        tokens = ctx.root_tokens.get(str(eid), 0) if not parent_root else 0
        r.u_grade = 'MEDIUM' if parent_exists else 'LOW'
        r.u_evidence.append(f'Parent entry exists')
    else:
        r.u_grade = 'LOW'
        r.u_evidence.append('No parent entry')

    # F — no banned link type
    if link and link.upper() in ctx.banned_links:
        r.f_grade = 'FAIL'
        r.f_evidence.append(f'Banned link type: {link}')
    elif link_ok:
        r.f_grade = 'HIGH'
        r.f_evidence.append(f'Permitted link: {link}')
    else:
        r.f_grade = 'LOW'
        r.f_evidence.append(f'No link type')
    return r


def _dquf_cross_refs(row, ctx):
    r = QUFResult()
    fid = row.get('from_id')
    tid = row.get('to_id')
    link = row.get('link_type', '')

    # Q — L7-CrossRefs: both endpoints exist
    f_exists = fid in ctx.valid_entries if fid else False
    t_exists = tid in ctx.valid_entries if tid else False
    r.q_grade = 'HIGH' if (f_exists and t_exists and link) else ('MEDIUM' if (f_exists or t_exists) else 'LOW')
    r.q_evidence.append(f'from={f_exists}, to={t_exists}, link={link}')

    # U — L7-CrossRefs: bidirectional?
    reverse_exists = (tid, fid) in ctx.xref_pairs if (fid and tid) else False
    if reverse_exists:
        r.u_grade = 'HIGH'
        r.u_evidence.append('Bidirectional cross-ref')
    elif f_exists and t_exists:
        r.u_grade = 'MEDIUM'
        r.u_evidence.append('Unidirectional but both endpoints exist')
    else:
        r.u_grade = 'LOW'

    # F — L7-CrossRefs: link type valid
    if link and link.upper() in ctx.permitted_links:
        r.f_grade = 'HIGH'
    elif link:
        r.f_grade = 'MEDIUM'
    else:
        r.f_grade = 'LOW'
    r.f_evidence.append(f'link_type={link}')
    return r


def _dquf_qv_register(row, ctx):
    r = QUFResult()
    root = row.get('ROOT', '')
    ctype = row.get('CORRUPTION_TYPE', '')
    correct = row.get('CORRECT_TRANSLATION', '')
    wrong = row.get('COMMON_MISTRANSLATION', '')
    ayat_count = row.get('AYAT_COUNT', 0) or 0

    # Q — L8-Detection: evidence quantified
    root_found = root in ctx.letters_to_id or root in ctx.bare_to_id
    r.q_grade = 'HIGH' if (root_found and ayat_count > 0 and ctype) else ('MEDIUM' if root_found else 'LOW')
    r.q_evidence.append(f'root={root_found}, ayat={ayat_count}, type={ctype}')

    # U — L8-Detection: corruption type valid + applies universally
    valid_type = ctype and any(ct in str(ctype).upper() for ct in ['ROOT_FLATTENED', 'ACTION', 'ATTRIBUTE', 'SCOPE', 'REPLACED', 'INVERTED'])
    r.u_grade = 'HIGH' if (valid_type and correct) else ('MEDIUM' if valid_type else 'LOW')
    r.u_evidence.append(f'valid_type={valid_type}, corrected={bool(correct)}')

    # F — L8-Detection: washed ≠ corrupted
    if correct and wrong and str(correct).strip() != str(wrong).strip():
        r.f_grade = 'HIGH'
        r.f_evidence.append('Washed ≠ corrupted')
    elif correct:
        r.f_grade = 'MEDIUM'
        r.f_evidence.append('Washed exists, no comparison')
    else:
        r.f_grade = 'LOW'
        r.f_evidence.append('No washed translation')
    return r


def _dquf_dp_register(row, ctx):
    r = QUFResult()
    dp = row.get('dp_code', '')
    mech = row.get('mechanism', '')
    qanc = row.get('qur_anchor', '')
    ex = row.get('example', '')
    status = row.get('status', '')
    distinct = row.get('distinct_from', '')

    r.q_grade = 'HIGH' if (mech and qanc and ex) else ('MEDIUM' if mech else 'LOW')
    r.q_evidence.append(f'mechanism={bool(mech)}, qur_anchor={bool(qanc)}, example={bool(ex)}')

    usage = ctx.dp_counts.get(dp, 0)
    if usage >= 3 and str(status).upper() == 'CONFIRMED':
        r.u_grade = 'HIGH'
    elif usage >= 1:
        r.u_grade = 'MEDIUM'
    else:
        r.u_grade = 'PENDING'
    r.u_evidence.append(f'Used in {usage} entries, status={status}')

    r.f_grade = 'HIGH' if distinct else 'MEDIUM'
    r.f_evidence.append(f'distinct_from={bool(distinct)}')
    return r


def _dquf_disputed_words(row, ctx):
    """KEY FIX: disputed words must NOT pass unless dispute is resolved."""
    r = QUFResult()
    lemma = row.get('lemma', '')
    root_assigned = row.get('root_assigned', '')
    root_hyp = row.get('root_hyphenated', '')
    derivation = row.get('derivation', '')
    token_count = row.get('token_count', 0) or 0
    falsification = row.get('falsification_condition', '')

    # Q — L8-Disputed: evidence quantity for assigned root
    if token_count > 10:
        r.q_grade = 'HIGH'
    elif token_count > 0:
        r.q_grade = 'MEDIUM'
    else:
        r.q_grade = 'LOW'
    r.q_evidence.append(f'Assigned root tokens: {token_count}')

    # U — L8-Disputed: does assignment explain ALL occurrences?
    spread = ctx.surah_spread.get(root_hyp, 0)
    if spread >= 5:
        r.u_grade = 'HIGH'
        r.u_evidence.append(f'Root covers {spread} surahs')
    elif spread >= 1:
        r.u_grade = 'MEDIUM'
        r.u_evidence.append(f'Root in {spread} surahs')
    else:
        r.u_grade = 'LOW'
        r.u_evidence.append('Root not found in compiler surah data')

    # F — L8-Disputed: MUST state falsification + derivation must be substantive
    derivation_ok = derivation and len(str(derivation)) > 20
    falsification_ok = falsification and len(str(falsification)) > 20

    if derivation_ok and falsification_ok:
        r.f_grade = 'HIGH'
        r.f_evidence.append('Derivation + falsification documented')
    elif derivation_ok:
        r.f_grade = 'MEDIUM'
        r.f_evidence.append('Derivation documented, no explicit falsification condition')
    else:
        r.f_grade = 'LOW'
        r.f_evidence.append('Insufficient derivation documentation')
    return r


def _dquf_blacklist(row, ctx):
    r = QUFResult()
    correct = row.get('correct_translation', '')
    source = row.get('source_of_correction', '')
    why = row.get('why_contaminated', '')

    r.q_grade = 'HIGH' if (correct and source) else ('MEDIUM' if correct else 'LOW')
    r.q_evidence.append(f'correction={bool(correct)}, source={bool(source)}')
    r.u_grade = 'HIGH' if source else 'MEDIUM'
    r.u_evidence.append(f'Source cited: {bool(source)}')
    r.f_grade = 'HIGH' if (why and len(str(why)) > 10) else 'MEDIUM'
    r.f_evidence.append(f'why_contaminated={bool(why)}')
    return r


def _dquf_phonetic_rev(row, ctx):
    r = QUFResult()
    frm = row.get('from_modern', '')
    to = row.get('to_orig', '')
    mech = row.get('mechanism', '')
    eref = row.get('entry_ref', '')
    status = row.get('status', '')
    rel = row.get('reliability', '')

    r.q_grade = 'HIGH' if (frm and to and mech) else ('MEDIUM' if frm and to else 'LOW')
    r.q_evidence.append(f'from={bool(frm)}, to={bool(to)}, mechanism={bool(mech)}')

    if eref and str(eref) in [str(e) for e in ctx.valid_entries]:
        r.u_grade = 'HIGH'
    elif eref:
        r.u_grade = 'MEDIUM'
    else:
        r.u_grade = 'LOW'
    r.u_evidence.append(f'entry_ref={eref}')

    r.f_grade = 'HIGH' if str(status).upper() == 'CONFIRMED' else ('MEDIUM' if status else 'LOW')
    r.f_evidence.append(f'status={status}, reliability={rel}')
    return r


def _dquf_morpheme(row, ctx):
    r = QUFResult()
    morph = row.get('morpheme', '')
    root = row.get('aa_root', '')
    qref = row.get('qur_ref', '')
    tokens = row.get('token_count', 0) or 0

    r.q_grade = 'HIGH' if (morph and root and qref and tokens > 0) else ('MEDIUM' if morph and root else 'LOW')
    r.q_evidence.append(f'morpheme={morph}, tokens={tokens}')
    r.u_grade = 'HIGH' if tokens >= 2 else ('MEDIUM' if tokens > 0 else 'PENDING')
    r.u_evidence.append(f'Token count: {tokens}')
    r.f_grade = 'HIGH' if qref else 'MEDIUM'
    r.f_evidence.append(f'Quran ref: {bool(qref)}')
    return r


def _dquf_child_entries(row, ctx):
    r = QUFResult()
    orig_root = row.get('orig_root', '')
    chain = row.get('phonetic_chain', '')
    qanc = row.get('qur_anchors', '')
    gate = row.get('gate_status', '')
    dp = row.get('dp_codes', '')
    nt = row.get('nt_code', '')
    inv = row.get('inversion_direction', '')
    orig_m = row.get('orig_meaning', '')
    shell_m = row.get('shell_meaning', '')

    r.q_grade = 'HIGH' if (orig_root and chain and qanc) else ('MEDIUM' if orig_root else 'LOW')
    r.q_evidence.append(f'root={bool(orig_root)}, chain={bool(chain)}, qur={bool(qanc)}')

    confirmed = str(gate).upper() == 'CONFIRMED'
    has_dp = bool(dp)
    has_nt = bool(nt)
    r.u_grade = 'HIGH' if (confirmed and has_dp and has_nt) else ('MEDIUM' if confirmed else 'LOW')
    r.u_evidence.append(f'gate={gate}, dp={has_dp}, nt={has_nt}')

    inv_ok = bool(inv)
    meaning_diff = orig_m and shell_m and str(orig_m) != str(shell_m)
    r.f_grade = 'HIGH' if (inv_ok and meaning_diff) else ('MEDIUM' if inv_ok else 'LOW')
    r.f_evidence.append(f'inversion={inv_ok}, meaning_differs={meaning_diff}')
    return r


def _dquf_bitig_conv(row, ctx):
    r = QUFResult()
    o2r = row.get('orig2_root', '')
    o1r = row.get('orig1_root', '')
    qref = row.get('quranic_ref', '')
    status = row.get('status', '')

    r.q_grade = 'HIGH' if (o2r and o1r and qref) else ('MEDIUM' if o2r and o1r else 'LOW')
    r.q_evidence.append(f'orig2={bool(o2r)}, orig1={bool(o1r)}, qref={bool(qref)}')

    o1_in_roots = o1r in ctx.root_tokens if o1r else False
    r.u_grade = 'HIGH' if (str(status).upper() == 'CONFIRMED' and o1_in_roots) else ('MEDIUM' if status else 'LOW')
    r.u_evidence.append(f'status={status}, orig1_in_roots={o1_in_roots}')

    r.f_grade = 'HIGH' if (o2r != o1r and str(status).upper() == 'CONFIRMED') else 'MEDIUM'
    r.f_evidence.append(f'Distinct roots: {o2r != o1r}')
    return r


def _dquf_bitig_deg(row, ctx):
    r = QUFResult()
    orig = row.get('bitig_original', '')
    ds = row.get('downstream_form', '')
    dtype = row.get('degradation_type', '')
    src = row.get('lattice_source', '')
    kash = row.get('kashgari_ref', '')
    dp = row.get('dp_codes', '')
    orig_m = row.get('original_meaning', '')
    deg_m = row.get('degraded_meaning', '')

    r.q_grade = 'HIGH' if (orig and ds and dtype) else ('MEDIUM' if orig else 'LOW')
    r.q_evidence.append(f'original={bool(orig)}, downstream={bool(ds)}, type={dtype}')

    r.u_grade = 'HIGH' if (src and kash) else ('MEDIUM' if src or kash else 'LOW')
    r.u_evidence.append(f'lattice_source={bool(src)}, kashgari={bool(kash)}')

    meaning_diff = orig_m and deg_m and str(orig_m) != str(deg_m)
    r.f_grade = 'HIGH' if (dp and meaning_diff) else ('MEDIUM' if meaning_diff else 'LOW')
    r.f_evidence.append(f'dp={bool(dp)}, meaning_differs={meaning_diff}')
    return r


def _dquf_chronology(row, ctx):
    r = QUFResult()
    date = row.get('date', '')
    event = row.get('event', '')
    source = row.get('source', '')
    conf = row.get('confidence', '')
    qref = row.get('qur_ref', '')

    r.q_grade = 'HIGH' if (date and event and source) else ('MEDIUM' if date and event else 'LOW')
    r.q_evidence.append(f'date={bool(date)}, event={bool(event)}, source={bool(source)}')

    r.u_grade = 'HIGH' if qref else 'MEDIUM'
    r.u_evidence.append(f'Quran ref: {bool(qref)}')

    conf_ok = str(conf).upper() == 'HIGH'
    source_ok = source and len(str(source)) > 3 and str(source).upper() not in ('UNKNOWN', 'TBD', '')
    r.f_grade = 'HIGH' if (conf_ok and source_ok) else ('MEDIUM' if source_ok else 'LOW')
    r.f_evidence.append(f'confidence={conf}, source_traceable={source_ok}')
    return r


def _dquf_deployment(row, ctx):
    r = QUFResult()
    words = row.get('deployed_words', '')
    roots = row.get('aa_roots', '')
    mech = row.get('mechanism', '')
    cref = row.get('chronology_ref', '')
    dp = row.get('dp_codes', '')

    r.q_grade = 'HIGH' if (words and roots and mech) else ('MEDIUM' if words else 'LOW')
    r.q_evidence.append(f'words={bool(words)}, roots={bool(roots)}, mechanism={bool(mech)}')

    cref_valid = cref and str(cref) in ctx.chrono_ids
    r.u_grade = 'HIGH' if (cref_valid and dp) else ('MEDIUM' if cref_valid else 'LOW')
    r.u_evidence.append(f'chrono_ref={cref_valid}, dp={bool(dp)}')

    mech_ok = mech and len(str(mech)) > 10
    r.f_grade = 'HIGH' if mech_ok else ('MEDIUM' if mech else 'LOW')
    r.f_evidence.append(f'Mechanism length: {len(str(mech)) if mech else 0}')
    return r


def _dquf_shift_lookup(row, ctx):
    r = QUFResult()
    en = row.get('en_consonant', '')
    aa = row.get('aa_letter', '')
    sid = row.get('shift_id', '')

    # Q — always HIGH (definition exists by nature)
    r.q_grade = 'HIGH'
    r.q_evidence.append(f'{en}→{aa} via {sid}')

    # U — L0-Alphabet: is this shift USED?
    usage = ctx.shift_usage.get(sid, 0)
    if usage > 10:
        r.u_grade = 'HIGH'
        r.u_evidence.append(f'Used {usage} times')
    elif usage > 0:
        r.u_grade = 'MEDIUM'
        r.u_evidence.append(f'Used {usage} times')
    else:
        r.u_grade = 'PENDING'
        r.u_evidence.append('Defined but not yet used in any entry')

    # F — no duplicate mapping
    r.f_grade = 'HIGH'  # Shifts are definitional
    r.f_evidence.append('Shift definition')
    return r


def _dquf_name_root_hub(row, ctx):
    r = QUFResult()
    tokens = row.get('token_count', 0) or 0
    abjad = row.get('abjad_total', '')
    en_ids = row.get('downstream_en_ids', '')
    corr = row.get('corrected_meaning', '')
    curr = row.get('current_meaning', '')

    r.q_grade = 'HIGH' if (tokens > 0 and abjad) else 'MEDIUM'
    r.q_evidence.append(f'tokens={tokens}, abjad={bool(abjad)}')
    r.u_grade = 'HIGH' if en_ids else 'MEDIUM'
    r.u_evidence.append(f'downstream_ids={bool(en_ids)}')
    r.f_grade = 'HIGH' if (corr and curr and str(corr) != str(curr)) else 'MEDIUM'
    r.f_evidence.append(f'correction documented: {corr != curr if corr and curr else False}')
    return r


def _dquf_isnad(row, ctx):
    r = QUFResult()
    md = row.get('md_file', '')
    rule = row.get('traces_to_rule', '')
    chain = row.get('chain', '')
    root = row.get('traces_to_root', '')

    r.q_grade = 'HIGH' if (md and rule and chain) else ('MEDIUM' if chain else 'LOW')
    r.q_evidence.append(f'file={bool(md)}, rule={bool(rule)}, chain={bool(chain)}')

    chain_links = len(str(chain).split('→')) if chain else 0
    rule_valid = rule and str(rule) in ctx.protocol_rules
    r.u_grade = 'HIGH' if (chain_links >= 2 and rule_valid) else ('MEDIUM' if chain_links >= 2 else 'LOW')
    r.u_evidence.append(f'Chain links: {chain_links}, rule valid: {rule_valid}')

    r.f_grade = 'HIGH' if root else 'MEDIUM'
    r.f_evidence.append(f'Traces to root: {bool(root)}')
    return r


def _dquf_structural(row, ctx):
    """Generic structural (languages, op_codes) — MEDIUM baseline."""
    r = QUFResult()
    # Count populated fields
    populated = sum(1 for v in row.values() if v is not None and str(v).strip() and not str(v).startswith('quf'))
    total = len([k for k in row.keys() if not k.startswith('quf')])
    ratio = populated / max(total, 1)

    r.q_grade = 'HIGH' if ratio >= 0.7 else ('MEDIUM' if ratio >= 0.4 else 'LOW')
    r.q_evidence.append(f'{populated}/{total} fields populated')
    r.u_grade = 'MEDIUM'
    r.u_evidence.append('L0-Alphabet config table — MEDIUM baseline')
    r.f_grade = 'MEDIUM'
    r.f_evidence.append('L0-Alphabet config — MEDIUM baseline')
    return r


# ═══════════════════════════════════════════════════════════════════════════════
# HYBRID DOMAIN VALIDATORS — consolidated tables
# Each routes on subsystem/subtable/layer for table-specific logic
# ═══════════════════════════════════════════════════════════════════════════════

def _dquf_body_data(row, ctx):
    """Hybrid validator for body_data — routes on subsystem for specific checks."""
    r = QUFResult()
    subsystem = row.get('subsystem', '')
    arabic = row.get('arabic', '') or ''
    qur_ref = row.get('quranic_ref', '') or ''
    root_letters = row.get('root_letters', '') or ''
    aa_root = row.get('aa_root_id', '') or ''
    score = row.get('score', 0) or 0
    status = row.get('status', '') or ''
    specific = row.get('specific_data', '') or ''

    # ── Q: Qur'anic attestation + root presence ──
    has_arabic = bool(arabic.strip())
    has_qur = bool(qur_ref.strip())
    root_in_db = aa_root in ctx.root_tokens if aa_root else False
    root_tokens = ctx.root_tokens.get(aa_root, 0) if aa_root else 0

    q_score = 0
    if has_arabic: q_score += 2
    if has_qur: q_score += 3
    if root_in_db: q_score += 3
    if root_tokens > 0: q_score += 2

    r.q_grade = 'HIGH' if q_score >= 8 else ('MEDIUM' if q_score >= 5 else ('LOW' if q_score >= 2 else 'FAIL'))
    r.q_evidence.append(f'arabic={has_arabic} qur={has_qur} root={root_in_db} tokens={root_tokens}')

    # ── U: cross-subsystem coverage ──
    # Check if this root appears in other body subsystems
    cross_subsystem = 0
    if aa_root:
        try:
            cross_subsystem = ctx.conn.execute(
                "SELECT COUNT(DISTINCT subsystem) FROM body_data WHERE aa_root_id = ?",
                (aa_root,)
            ).fetchone()[0]
        except Exception:
            pass

    # Subsystem-specific boosts
    is_confirmed = status.upper() == 'CONFIRMED' if status else False

    r.u_grade = (
        'HIGH' if cross_subsystem >= 3 or (is_confirmed and has_qur) else
        'MEDIUM' if cross_subsystem >= 2 or is_confirmed or has_qur else
        'LOW' if cross_subsystem >= 1 or has_arabic else
        'FAIL'
    )
    r.u_evidence.append(f'cross_subsystem={cross_subsystem} confirmed={is_confirmed}')

    # ── F: data completeness + subsystem-specific checks ──
    populated = sum(1 for k, v in row.items()
                   if v is not None and str(v).strip()
                   and not k.startswith('quf') and k not in ('body_id', 'subsystem', 'subtable'))
    total_fields = len([k for k in row.keys()
                       if not k.startswith('quf') and k not in ('body_id', 'subsystem', 'subtable')])
    ratio = populated / max(total_fields, 1)

    # Subsystem-specific: architecture/diagnostics need higher completeness
    high_threshold = 0.6
    if subsystem in ('architecture', 'diagnostics', 'technical'):
        high_threshold = 0.7

    r.f_grade = (
        'HIGH' if ratio >= high_threshold and has_arabic else
        'MEDIUM' if ratio >= 0.4 and (has_arabic or has_qur) else
        'LOW' if ratio >= 0.2 else
        'FAIL'
    )
    r.f_evidence.append(f'completeness={ratio:.0%} subsystem={subsystem}')
    return r


def _dquf_body_xref(row, ctx):
    """Validator for body_cross_refs_unified."""
    r = QUFResult()
    relationship = row.get('relationship', '') or ''
    source_id = row.get('source_id', '') or ''
    target_id = row.get('target_id', '') or ''
    aa_root = row.get('aa_root_id', '') or ''

    # Q: both ends exist?
    has_source = bool(source_id.strip())
    has_target = bool(target_id.strip())
    has_rel = bool(relationship.strip())

    r.q_grade = (
        'HIGH' if has_source and has_target and has_rel else
        'MEDIUM' if has_source and has_target else
        'LOW' if has_source or has_target else 'FAIL'
    )
    r.q_evidence.append(f'src={has_source} tgt={has_target} rel={has_rel}')

    # U: root-linked?
    root_in_db = aa_root in ctx.root_tokens if aa_root else False
    r.u_grade = 'HIGH' if root_in_db else ('MEDIUM' if has_rel else 'LOW')
    r.u_evidence.append(f'root_linked={root_in_db}')

    # F: relationship is valid type?
    banned = any(b in relationship.upper() for b in ctx.banned_links) if relationship else False
    r.f_grade = 'FAIL' if banned else ('HIGH' if has_rel and has_source and has_target else 'MEDIUM')
    r.f_evidence.append(f'banned={banned}')
    return r


def _dquf_body_prayer(row, ctx):
    """Validator for body_prayer_map_unified."""
    r = QUFResult()
    prayer_state = row.get('prayer_state', '') or ''
    specific = row.get('specific_data', '') or ''

    has_state = bool(prayer_state.strip())
    has_data = bool(specific.strip())

    r.q_grade = 'HIGH' if has_state and has_data else ('MEDIUM' if has_state else 'LOW')
    r.q_evidence.append(f'state={has_state} data={has_data}')
    r.u_grade = 'MEDIUM'  # prayer maps are structural
    r.u_evidence.append('prayer map — MEDIUM baseline')
    r.f_grade = 'HIGH' if has_state and has_data else 'MEDIUM'
    r.f_evidence.append(f'complete={has_state and has_data}')
    return r


def _dquf_formula(row, ctx):
    """Hybrid validator for formula tables (direct columns, NOT consolidated).
    Formula tables: concealment, ratios, restoration, scholars, undiscovered, cross_refs.
    Columns vary but all have: category/content + q_gate/u_gate/f_gate + score + status + QUF.
    """
    r = QUFResult()

    # Count populated non-QUF, non-system fields
    skip = {'rowid', 'rowid_pk', 'quf_q', 'quf_u', 'quf_f', 'quf_pass', 'quf_date', 'quf_token'}
    populated = sum(1 for k, v in row.items()
                   if k not in skip and v is not None and str(v).strip())
    total_fields = len([k for k in row.keys() if k not in skip])
    ratio = populated / max(total_fields, 1)

    # Q: existing q_gate + data completeness
    q_gate = (row.get('q_gate', '') or '').upper()
    has_content = bool((row.get('content', '') or row.get('category', '') or '').strip())
    status = (row.get('status', '') or '').upper()
    is_confirmed = status == 'CONFIRMED'

    r.q_grade = (
        'HIGH' if (q_gate in ('Q-DIRECT', 'Q-DERIVED') or is_confirmed) and ratio >= 0.5 else
        'MEDIUM' if has_content and ratio >= 0.3 else
        'LOW' if has_content else 'FAIL'
    )
    r.q_evidence.append(f'q_gate={q_gate} content={has_content} ratio={ratio:.0%}')

    # U: u_gate + cross-table presence
    u_gate = (row.get('u_gate', '') or '').upper()
    r.u_grade = (
        'HIGH' if u_gate == 'PASS' and is_confirmed else
        'MEDIUM' if u_gate == 'PASS' or is_confirmed or ratio >= 0.4 else
        'LOW' if has_content else 'FAIL'
    )
    r.u_evidence.append(f'u_gate={u_gate} confirmed={is_confirmed}')

    # F: f_gate + completeness
    f_gate = (row.get('f_gate', '') or '').upper()
    r.f_grade = (
        'HIGH' if ratio >= 0.6 and (f_gate in ('PASS', 'STRUCTURAL') or is_confirmed) else
        'MEDIUM' if ratio >= 0.3 and has_content else
        'LOW' if has_content else 'FAIL'
    )
    r.f_evidence.append(f'f_gate={f_gate} completeness={ratio:.0%}')
    return r


def _dquf_foundation(row, ctx):
    """Hybrid validator for foundation_data — routes on layer."""
    r = QUFResult()
    layer = row.get('layer', '') or ''
    specific = row.get('specific_data', '') or ''
    try:
        data = json.loads(specific) if specific else {}
    except (json.JSONDecodeError, TypeError):
        data = {}

    # Q: has core evidence?
    has_ref = bool(data.get('qur_ref', '') or data.get('lattice_ref', ''))
    has_evidence = bool(data.get('evidence', '') or data.get('proof_type', '')
                       or data.get('measurable_test', ''))
    populated = len([v for v in data.values() if v is not None and str(v).strip()])

    r.q_grade = 'HIGH' if has_ref and has_evidence else ('MEDIUM' if has_ref or has_evidence else ('LOW' if populated > 0 else 'FAIL'))
    r.q_evidence.append(f'ref={has_ref} evidence={has_evidence} fields={populated}')

    # U: applicable across layers?
    r.u_grade = 'HIGH' if has_ref else 'MEDIUM'
    r.u_evidence.append(f'layer={layer}')

    # F: completeness
    ratio = populated / max(len(data), 1)
    r.f_grade = 'HIGH' if ratio >= 0.6 else ('MEDIUM' if ratio >= 0.3 else 'LOW')
    r.f_evidence.append(f'completeness={ratio:.0%}')
    return r


def _dquf_mechanism(row, ctx):
    """Hybrid validator for mechanism_data — routes on layer."""
    r = QUFResult()
    layer = row.get('layer', '') or ''
    specific = row.get('specific_data', '') or ''
    try:
        data = json.loads(specific) if specific else {}
    except (json.JSONDecodeError, TypeError):
        data = {}

    # Layer-specific Q checks
    if layer in ('M1', 'M1_BITIG'):
        # Shift data: need aa_letter + shift_id
        has_letter = bool(data.get('aa_letter', '') or data.get('ар_буква', ''))
        has_shift = bool(data.get('shift_id', '') or data.get('сдвиг_id', '') or data.get('en_consonant', ''))
        r.q_grade = 'HIGH' if has_letter and has_shift else ('MEDIUM' if has_letter or has_shift else 'LOW')
        r.q_evidence.append(f'letter={has_letter} shift={has_shift}')
    else:
        # General mechanism: populated fields
        populated = len([v for v in data.values() if v is not None and str(v).strip()])
        r.q_grade = 'HIGH' if populated >= 4 else ('MEDIUM' if populated >= 2 else ('LOW' if populated > 0 else 'FAIL'))
        r.q_evidence.append(f'fields={populated}')

    # U: mechanism is documented with examples?
    has_examples = bool(data.get('examples', '') or data.get('примеры', '') or data.get('markers', ''))
    r.u_grade = 'HIGH' if has_examples else 'MEDIUM'
    r.u_evidence.append(f'examples={has_examples}')

    # F: completeness
    populated = len([v for v in data.values() if v is not None and str(v).strip()])
    ratio = populated / max(len(data), 1)
    r.f_grade = 'HIGH' if ratio >= 0.6 else ('MEDIUM' if ratio >= 0.3 else 'LOW')
    r.f_evidence.append(f'completeness={ratio:.0%}')
    return r


# ─── DISPATCHER ────────────────────────────────────────────────────────────────

DOMAIN_VALIDATORS = {
    # 12 DOMAINS — topological order (core → edge)
    #
    # D1: FOUNDATION + MECHANISM (consolidated)
    'foundation_data': _dquf_foundation,           # D1
    'mechanism_data': _dquf_mechanism,             # D1
    #
    # D2: ROOT — letter combinations → meaning
    'roots': _dquf_roots,                          # D2
    #
    # D3: DIVINE NAMES — أَسْمَاء اللَّه
    'names_of_allah': _dquf_names_of_allah,        # D3
    'name_root_hub': _dquf_name_root_hub,          # D3
    #
    # D4: QUR'AN COMPILER — verified forms
    'quran_word_roots': _dquf_quran_word_roots,    # D4
    'quran_known_forms': _dquf_quran_known_forms,  # D4
    #
    # D5: ENTRIES — AA→downstream via shifts
    'entries': _dquf_entries,                       # D5
    #
    # D6: SIBLINGS — mirrors
    'european_a1_entries': _dquf_european,          # D6
    'latin_a1_entries': _dquf_latin,                # D6
    'bitig_a1_entries': _dquf_bitig,                # D6
    'uzbek_vocabulary': _dquf_uzbek,                # D6
    #
    # D7: DERIVATIVES + CROSS-REFS
    'a4_derivatives': _dquf_derivatives,            # D7
    'a5_cross_refs': _dquf_cross_refs,              # D7
    #
    # D8: DETECTION — erasure patterns
    'disputed_words': _dquf_disputed_words,         # D8
    'contamination_blacklist': _dquf_blacklist,     # D8
    'dp_register': _dquf_dp_register,               # D8
    'phonetic_reversal': _dquf_phonetic_rev,        # D8
    'qv_translation_register': _dquf_qv_register,  # D8
    #
    # D9: BODY / HEALTH (consolidated)
    'body_data': _dquf_body_data,                   # D9
    'body_cross_refs_unified': _dquf_body_xref,    # D9
    'body_prayer_map_unified': _dquf_body_prayer,  # D9
    #
    # D10: FORMULA (ḥisāb)
    'formula_concealment': _dquf_formula,           # D10
    'formula_ratios': _dquf_formula,                # D10
    'formula_restoration': _dquf_formula,           # D10
    'formula_scholars': _dquf_formula,              # D10
    'formula_undiscovered': _dquf_formula,          # D10
    'formula_cross_refs': _dquf_body_xref,          # D10 (cross-ref structure)
    #
    # D11: HISTORY — chronology, deployment, peoples
    'child_entries': _dquf_child_entries,            # D11
    'chronology': _dquf_chronology,                 # D11
    'word_deployment_map': _dquf_deployment,         # D11
    'bitig_convergence_register': _dquf_bitig_conv, # D11
    'bitig_degradation_register': _dquf_bitig_deg,  # D11
    #
    # D12: INTELLIGENCE
    'isnad': _dquf_isnad,                           # D12
}

# Topological order — 12 domains, core → edge
PROPAGATION_ORDER = [
    # D1: FOUNDATION + MECHANISM
    'foundation_data', 'mechanism_data',
    # D2: ROOT
    'roots',
    # D3: DIVINE NAMES
    'names_of_allah', 'name_root_hub',
    # D4: QUR'AN COMPILER
    'quran_word_roots', 'quran_known_forms',
    # D5: ENTRIES
    'entries',
    # D6: SIBLINGS
    'european_a1_entries', 'latin_a1_entries', 'bitig_a1_entries', 'uzbek_vocabulary',
    # D7: DERIVATIVES
    'a4_derivatives', 'a5_cross_refs',
    # D8: DETECTION
    'disputed_words', 'contamination_blacklist', 'dp_register', 'phonetic_reversal',
    'qv_translation_register',
    # D9: BODY
    'body_data', 'body_cross_refs_unified', 'body_prayer_map_unified',
    # D10: FORMULA
    'formula_concealment', 'formula_ratios', 'formula_restoration',
    'formula_scholars', 'formula_undiscovered', 'formula_cross_refs',
    # D11: HISTORY
    'child_entries', 'chronology', 'word_deployment_map',
    'bitig_convergence_register', 'bitig_degradation_register',
    # D12: INTELLIGENCE
    'isnad',
]


def domain_propagate_all(dry_run=False):
    """Run domain-specific QUF across all 27 tables in topological order."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    print("Building context maps...")
    ctx = QUFContext(conn)

    # Generate tokens — batch insert for speed
    now = datetime.now().isoformat()
    needed = 105000
    available = conn.execute("SELECT COUNT(*) FROM quf_tokens WHERE used=0").fetchone()[0]
    if available < needed:
        gen = needed - available
        print(f"Generating {gen} QUF tokens (batch)...")
        batch = [(str(uuid.uuid4()), 0, 'DOMAIN_QUF', 'domain_propagate', now, 0) for _ in range(gen)]
        conn.executemany("INSERT INTO quf_tokens (token, entry_id, root_letters, generated_by, generated_at, used) VALUES (?, ?, ?, ?, ?, ?)", batch)
        conn.commit()
        print(f"  Tokens generated.")

    tokens = [r[0] for r in conn.execute(f"SELECT token FROM quf_tokens WHERE used=0 LIMIT {needed}").fetchall()]
    tidx = [0]  # Mutable counter

    used_tokens = []  # Mark used AFTER update, not before

    def consume_token():
        if tidx[0] < len(tokens):
            t = tokens[tidx[0]]
            tidx[0] += 1
            used_tokens.append(t)
            return t
        return str(uuid.uuid4())

    results = {}

    for tbl in PROPAGATION_ORDER:
        validator = DOMAIN_VALIDATORS.get(tbl)
        if not validator:
            continue

        cols = [r[1] for r in conn.execute(f"PRAGMA table_info('{tbl}')").fetchall()]
        has_token = 'quf_token' in cols
        has_quf = 'quf_pass' in cols

        if not has_quf:
            continue

        rows = conn.execute(f'SELECT rowid, * FROM "{tbl}"').fetchall()
        total = len(rows)
        passed = 0

        for row in rows:
            rowid = row['rowid'] if 'rowid' in row.keys() else row[0]
            row_dict = dict(row)

            result = validator(row_dict, ctx)
            overall = result.overall

            if overall == 'TRUE':
                passed += 1

            if not dry_run:
                try:
                    if has_token:
                        tok = consume_token()
                        conn.execute(f'UPDATE "{tbl}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, quf_date=?, quf_token=? WHERE rowid=?',
                                    (result.q_grade, result.u_grade, result.f_grade, overall, now, tok, rowid))
                    else:
                        conn.execute(f'UPDATE "{tbl}" SET quf_q=?, quf_u=?, quf_f=?, quf_pass=?, quf_date=? WHERE rowid=?',
                                    (result.q_grade, result.u_grade, result.f_grade, overall, now, rowid))
                except sqlite3.IntegrityError:
                    pass  # Skip rows blocked by contamination shield (pre-existing data)

        rate = passed * 100 // max(total, 1)
        results[tbl] = {'total': total, 'pass': passed, 'rate': rate}
        print(f"  {tbl:<40} {total:>6} rows → {passed:>6} pass ({rate}%)")

        if not dry_run:
            # Mark tokens as used AFTER all updates for this table
            for t in used_tokens:
                conn.execute("UPDATE quf_tokens SET used=1 WHERE token=?", (t,))
            used_tokens.clear()
            conn.commit()

    conn.close()

    # Summary
    print("\n" + "=" * 65)
    print(f"{'TABLE':<40} {'TOTAL':>6} {'PASS':>6} {'RATE':>6}")
    print("-" * 60)
    gt = gp = 0
    for tbl in PROPAGATION_ORDER:
        if tbl in results:
            d = results[tbl]
            gt += d['total']
            gp += d['pass']
            print(f"{tbl:<40} {d['total']:>6} {d['pass']:>6} {d['rate']:>5}%")
    print("-" * 60)
    print(f"{'TOTAL':<40} {gt:>6} {gp:>6} {gp*100//max(gt,1):>5}%")
    print(f"\nTokens consumed: {tidx[0]}")
    return results


def domain_quf_report():
    """Show domain QUF status with gate breakdown."""
    conn = sqlite3.connect(DB_PATH)
    print(f"\n{'TABLE':<35} {'TOTAL':>6} {'PASS':>6} {'PEND':>6} {'FAIL':>6} {'RATE':>6} | {'Q_H':>4} {'U_H':>4} {'F_H':>4}")
    print("=" * 95)
    gt = gp = 0
    for tbl in PROPAGATION_ORDER:
        try:
            total = conn.execute(f'SELECT COUNT(*) FROM "{tbl}"').fetchone()[0]
            passed = conn.execute(f"SELECT COUNT(*) FROM \"{tbl}\" WHERE quf_pass='TRUE'").fetchone()[0]
            pending = conn.execute(f"SELECT COUNT(*) FROM \"{tbl}\" WHERE quf_pass='PENDING'").fetchone()[0]
            failed = total - passed - pending
            q_h = conn.execute(f"SELECT COUNT(*) FROM \"{tbl}\" WHERE quf_q='HIGH'").fetchone()[0]
            u_h = conn.execute(f"SELECT COUNT(*) FROM \"{tbl}\" WHERE quf_u='HIGH'").fetchone()[0]
            f_h = conn.execute(f"SELECT COUNT(*) FROM \"{tbl}\" WHERE quf_f='HIGH'").fetchone()[0]
            rate = passed * 100 // max(total, 1)
            gt += total
            gp += passed
            print(f"{tbl:<35} {total:>6} {passed:>6} {pending:>6} {failed:>6} {rate:>5}% | {q_h:>4} {u_h:>4} {f_h:>4}")
        except:
            pass
    print("-" * 95)
    print(f"{'TOTAL':<35} {gt:>6} {gp:>6} {'':>6} {'':>6} {gp*100//max(gt,1):>5}%")
    conn.close()


def main():
    args = sys.argv[1:]
    if not args:
        print_usage()
        return

    cmd = args[0].lower()

    if cmd == 'domain_propagate':
        dry = '--dry-run' in args
        domain_propagate_all(dry_run=dry)

    elif cmd == 'domain_report':
        domain_quf_report()

    elif cmd == 'propagate':
        target = args[1].lower() if len(args) > 1 else 'all'
        dry_run = '--dry-run' in args
        if target == 'all':
            propagate_all(dry_run=dry_run)
        else:
            propagate_domain(target, dry_run=dry_run)

    elif cmd == 'propagation_status':
        propagation_status()

    elif cmd == 'domains':
        print(f"\nRegistered QUF domains ({len(DOMAIN_REGISTRY)}):\n")
        for name in sorted(DOMAIN_REGISTRY.keys()):
            d = DOMAIN_REGISTRY[name]
            print(f"  {name:25s} → {d.table}")
        print()

    else:
        _original_main()


if __name__ == '__main__':
    main()
