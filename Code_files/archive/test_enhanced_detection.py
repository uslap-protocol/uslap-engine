#!/usr/bin/env python3
"""
Test the enhanced domain-aware pattern detection
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from uslap_forest_v3_domain_aware import SelfReader, PatternDetector

def test_enhanced_detection():
    """Test the enhanced pattern detection"""
    print("="*60)
    print("🧪 TESTING ENHANCED DOMAIN-AWARE DETECTION")
    print("="*60)
    
    filepath = "USLaP_Final_Data_Consolidated_Master.xlsx"
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    # COMPONENT 1: Read
    print("\n📖 Reading file...")
    reader = SelfReader(filepath)
    reader.read_all()
    
    print(f"\n📊 Total entries: {reader.total_entries}")
    
    # COMPONENT 2: Enhanced detection
    print("\n🔍 Running enhanced pattern detection...")
    detector = PatternDetector(reader)
    gaps, candidates = detector.detect_all()
    
    print(f"\n📊 RESULTS:")
    print(f"  Total gaps found: {len(gaps)}")
    print(f"  Total candidates: {len(candidates)}")
    
    # Analyze gaps by type
    gap_types = {}
    for gap in gaps:
        gap_type = gap['type']
        gap_types[gap_type] = gap_types.get(gap_type, 0) + 1
    
    if gap_types:
        print(f"\n  Gap types:")
        for gap_type, count in sorted(gap_types.items()):
            print(f"    {gap_type}: {count}")
    
    # Show top gaps by priority
    if gaps:
        print(f"\n  Top gaps (by priority):")
        sorted_gaps = sorted(gaps, key=lambda x: x.get('priority', 0), reverse=True)
        for i, gap in enumerate(sorted_gaps[:10]):
            gap_type = gap['type']
            if gap_type == 'missing_domain_variant':
                print(f"    {i+1}. {gap_type}: ratio {gap['ratio']} missing {gap['missing_domain']} domain")
                print(f"       Existing domains: {gap['existing_domains']}")
                print(f"       Network: {gap['network']}, Priority: {gap['priority']}")
            elif gap_type == 'network_needs_ratio':
                print(f"    {i+1}. {gap_type}: network {gap['network']} needs ratio")
                print(f"       Entry count: {gap['count']}, Priority: {gap['priority']}")
            elif gap_type == 'entry_needs_network':
                print(f"    {i+1}. {gap_type}: entry {gap['entry']} needs network")
                print(f"       Term: {gap['term']}, Score: {gap['score']}, Priority: {gap['priority']}")
            else:
                print(f"    {i+1}. {gap_type}: {gap}")
    
    # Show what would be generated
    print(f"\n🎯 WHAT WOULD BE GENERATED (highest priority):")
    if gaps:
        top_gap = sorted_gaps[0]
        if top_gap['type'] == 'missing_domain_variant':
            ratio = top_gap['ratio']
            missing_domain = top_gap['missing_domain']
            network = top_gap['network']
            
            print(f"  For ratio {ratio} missing {missing_domain} domain:")
            if missing_domain == 'maqam':
                print(f"    → maqam proportion ({ratio})")
            elif missing_domain == 'rhythmic':
                print(f"    → tempo ratio {ratio}")
            elif missing_domain == 'spiritual/geometric':
                print(f"    → sacred proportion {ratio}")
            elif missing_domain == 'musical':
                print(f"    → musical interval {ratio}")
            print(f"    Network: {network}")
    
    # Analyze ratio families
    print(f"\n📈 RATIO FAMILY ANALYSIS:")
    
    # Group entries by ratio
    ratio_groups = {}
    for node_id, node in reader.graph.items():
        term = node.get('en_term', '')
        import re
        match = re.search(r'(\d+)/(\d+)', term)
        if match:
            ratio = match.group(0)
            if ratio not in ratio_groups:
                ratio_groups[ratio] = []
            ratio_groups[ratio].append(node_id)
    
    if ratio_groups:
        print(f"  Found {len(ratio_groups)} ratio families:")
        for ratio, entries in sorted(ratio_groups.items()):
            print(f"    {ratio}: {len(entries)} entries")
    
    print(f"\n✅ Test complete.")

if __name__ == "__main__":
    test_enhanced_detection()