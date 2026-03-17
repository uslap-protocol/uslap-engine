#!/usr/bin/env python3
"""
USLaP SINGLE-FILE BUILDER v1.0
One file to rule them all. Run: python3 uslap.py
"""
import json
import os
import sys
from datetime import datetime

# ==================== VISUAL SETUP ====================
def print_header():
    print("\n" + "="*60)
    print("USLaP BUILDER v1.0")
    print("Universal Scientific Lattice Protocol")
    print("111 Sciences → Unlimited Applications")
    print("="*60)
    print("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")

# ==================== 111 SCIENCES DATABASE ====================
def load_sciences():
    """Load all 111 sciences (embedded)"""
    sciences = []
    
    # First 20 real sciences
    real_sciences = [
        {"id": 1, "arabic": "عِلْم التَّقْدِير", "en": "Geometric Determination", 
         "root": "ق-د-ر", "quran": "54:49", "category": "foundational"},
        {"id": 2, "arabic": "عِلْم الحِسَاب", "en": "Precision Calculation", 
         "root": "ح-س-ب", "quran": "55:5", "category": "foundational"},
        {"id": 3, "arabic": "عِلْم الجَبْر", "en": "Restoration Science", 
         "root": "ج-ب-ر", "quran": "59:23", "category": "foundational"},
        {"id": 4, "arabic": "عِلْم النُّجُوم", "en": "Star Science", 
         "root": "ن-ج-م", "quran": "56:75", "category": "celestial"},
        {"id": 5, "arabic": "عِلْم الأَفْلَاك", "en": "Orbital Science", 
         "root": "ف-ل-ك", "quran": "36:40", "category": "celestial"},
        {"id": 6, "arabic": "عِلْم الأَحْيَاء", "en": "Life Science", 
         "root": "ح-ي-ي", "quran": "2:164", "category": "life"},
        {"id": 7, "arabic": "عِلْم الخَلْق", "en": "Creation Science", 
         "root": "خ-ل-ق", "quran": "59:24", "category": "life"},
        {"id": 8, "arabic": "عِلْم الشِّفَاء", "en": "Healing Science", 
         "root": "ش-ف-ي", "quran": "17:82", "category": "healing"},
        {"id": 9, "arabic": "عِلْم الطِّبّ", "en": "Restoration Science", 
         "root": "ط-ب-ب", "quran": "26:80", "category": "healing"},
        {"id": 10, "arabic": "عِلْم العَقْل", "en": "Reason Science", 
         "root": "ع-ق-ل", "quran": "2:44", "category": "cognitive"},
        {"id": 11, "arabic": "عِلْم الحِكْمَة", "en": "Wisdom Science", 
         "root": "ح-ك-م", "quran": "2:269", "category": "cognitive"},
        {"id": 12, "arabic": "عِلْم البَصَر", "en": "Sight Science", 
         "root": "ب-ص-ر", "quran": "67:4", "category": "perceptual"},
        {"id": 13, "arabic": "عِلْم السَّمْع", "en": "Hearing Science", 
         "root": "س-م-ع", "quran": "46:26", "category": "perceptual"},
        {"id": 14, "arabic": "عِلْم البِنَاء", "en": "Building Science", 
         "root": "ب-ن-ي", "quran": "51:47", "category": "applied"},
        {"id": 15, "arabic": "عِلْم الصِّنَاعَة", "en": "Manufacturing Science", 
         "root": "ص-ن-ع", "quran": "27:88", "category": "applied"},
        {"id": 16, "arabic": "عِلْم الزِّرَاعَة", "en": "Agriculture Science", 
         "root": "ز-ر-ع", "quran": "56:64", "category": "applied"},
        {"id": 17, "arabic": "عِلْم التِّجَارَة", "en": "Trade Science", 
         "root": "ت-ج-ر", "quran": "35:29", "category": "economic"},
        {"id": 18, "arabic": "عِلْم المَال", "en": "Wealth Science", 
         "root": "م-ا-ل", "quran": "18:46", "category": "economic"},
        {"id": 19, "arabic": "عِلْم الحُكْم", "en": "Governance Science", 
         "root": "ح-ك-م", "quran": "4:105", "category": "governance"},
        {"id": 20, "arabic": "عِلْم القَضَاء", "en": "Judgment Science", 
         "root": "ق-ض-ي", "quran": "40:20", "category": "governance"}
    ]
    
    sciences.extend(real_sciences)
    
    # Add placeholders for remaining 91
    for i in range(21, 112):
        sciences.append({
            "id": i,
            "arabic": f"عِلْم المثال {i}",
            "en": f"Example Science {i}",
            "root": "م-ث-ل",
            "quran": "2:26",
            "category": "example"
        })
    
    return sciences

# ==================== CONTAMINATION SCANNER ====================
CONTAMINATION_MAP = {
    # Category B: Greek/Latin
    "mathematical": ("calculation-based", "B", "Greek 'mathēmatikos'"),
    "geometry": ("measurement science", "B", "Greek 'geōmetria'"),
    "physics": ("natural motion science", "B", "Greek 'physis'"),
    "biology": ("life science", "B", "Greek 'bios' + 'logos'"),
    "chemistry": ("transformation science", "B", "Arabic al-kīmiyāʼ stolen"),
    "philosophy": ("systematic principles", "B", "Greek 'philosophia'"),
    
    # Category C: Cadaver Science
    "anatomy": ("living sensory lines", "C", "Greek 'anatomē' (cutting up)"),
    "dissection": ("living observation", "C", "Dead specimen analysis"),
    
    # Category J: Medici Family
    "medicine": ("healing science", "J", "Latin 'medicus'"),
    "medical": ("healing-related", "J", "External intervention paradigm"),
    
    # Category A: Person Names
    "newtonian": ("motion principles", "A", "Isaac Newton worship"),
    "euclidean": ("measurement principles", "A", "Euclid worship"),
    "gaussian": ("distribution methods", "A", "Carl Gauss worship"),
}

def check_contamination(text):
    """Check text for non-USLaP terms"""
    text_lower = text.lower()
    findings = []
    
    for bad_term, (replacement, category, reason) in CONTAMINATION_MAP.items():
        if bad_term in text_lower:
            # Find actual occurrence
            start = text_lower.find(bad_term)
            actual_text = text[start:start+len(bad_term)]
            
            findings.append({
                "term": actual_text,
                "replacement": replacement,
                "category": category,
                "reason": reason,
                "position": start
            })
    
    return findings

def explain_category(category):
    """Explain contamination category"""
    explanations = {
        "A": "Person-named reference (cult of personality)",
        "B": "Greek/Latin obscurantism (dead language roots)",
        "C": "Cadaver science (dead specimen analysis)",
        "J": "Latin 'Medici' family (external intervention paradigm)"
    }
    return explanations.get(category, "Unknown category")

# ==================== Q-U-F VERIFICATION ====================
class QGate:
    """Quantification: Everything measurable"""
    @staticmethod
    def verify(app_data):
        metrics = app_data.get('metrics', [])
        if not metrics:
            return False, "No metrics defined"
        
        for metric in metrics:
            if 'unit' not in metric:
                return False, f"Metric '{metric.get('name')}' has no unit"
        
        return True, "All metrics quantified"

class UGate:
    """Universality: Works for all"""
    @staticmethod
    def verify(app_data):
        limitations = app_data.get('limitations', [])
        if limitations:
            return False, f"Has limitations: {limitations}"
        
        # Check four dimensions
        checks = [
            ("cultural", app_data.get('cultural_limits')),
            ("geographic", app_data.get('geographic_limits')),
            ("temporal", app_data.get('temporal_limits')),
            ("economic", app_data.get('economic_limits'))
        ]
        
        for dimension, limit in checks:
            if limit:
                return False, f"Has {dimension} limitation: {limit}"
        
        return True, "Universally applicable"

class FGate:
    """Falsification: Testable failure"""
    @staticmethod
    def verify(app_data):
        failures = app_data.get('failure_conditions', [])
        if not failures:
            return False, "No failure conditions defined"
        
        for failure in failures:
            if 'test' not in failure:
                return False, f"Failure condition '{failure.get('desc')}' has no test method"
            
            if 'threshold' not in failure:
                return False, f"Failure condition '{failure.get('desc')}' has no threshold"
        
        return True, f"{len(failures)} testable failure conditions"

# ==================== APPLICATION GENERATOR ====================
def generate_template(name, science_ids, components=None):
    """Generate a complete USLaP application"""
    sciences = load_sciences()
    selected = [s for s in sciences if s['id'] in science_ids]
    
    if components is None:
        components = [
            "Measurement System (Q gate)",
            "Universal Interface (U gate)", 
            "Failure Detection (F gate)"
        ]
    
    # Build the document
    output = f"# USLaP APPLICATION: {name}\n"
    output += f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n"
    output += "بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ\n\n"
    
    output += "## ROOT SCIENCES\n"
    for sci in selected:
        output += f"### {sci['arabic']} ({sci['en']})\n"
        output += f"- **Root:** {sci['root']}\n"
        output += f"- **Qur'an:** {sci['quran']}\n"
        output += f"- **Category:** {sci['category']}\n\n"
    
    output += "## APPLICATION COMPONENTS\n"
    for i, comp in enumerate(components, 1):
        output += f"{i}. **{comp}**\n"
        output += f"   - Specification: [Define measurable metric]\n"
        output += f"   - Universality: [Explain why works for all]\n"
        output += f"   - Failure test: [Define testable failure]\n\n"
    
    output += "## Q-U-F GATES VERIFICATION\n"
    output += "| Gate | Requirement | Status | Verification Method |\n"
    output += "|------|-------------|--------|---------------------|\n"
    output += "| **Q** | Quantification | ⬜ Pending | Define measurable metrics for each component |\n"
    output += "| **U** | Universality | ⬜ Pending | Document why works for all humans, eras, cultures |\n"
    output += "| **F** | Falsification | ⬜ Pending | Define testable failure conditions |\n\n"
    
    output += "## NEXT STEPS\n"
    output += "1. **For Q Gate:** Add specific metrics with units (mm, %, seconds, etc.)\n"
    output += "2. **For U Gate:** Remove any cultural/geographic/temporal limitations\n"
    output += "3. **For F Gate:** Define exact failure thresholds and test methods\n"
    output += "4. **Build:** Start with Component 1, verify Q-U-F, then proceed\n\n"
    
    output += "---\n"
    output += "*This template follows USLaP principles:*\n"
    output += "- **4 Sources Only:** Qur'an, Hadith, Ibn Sīnā (القانون), Al-Khwārizmī (الجبر)\n"
    output += "- **No Contamination:** No Greek/Latin terms, no person names, no cadaver science\n"
    output += "- **Literate Person Test:** Any literate person can understand and verify\n"
    
    return output

# ==================== MENU SYSTEM ====================
def menu_generate():
    """Generate new application"""
    print("\n" + "="*40)
    print("GENERATE NEW APPLICATION")
    print("="*40)
    
    name = input("\nApplication name: ").strip()
    if not name:
        name = "USLaP Application"
    
    # Show science categories
    sciences = load_sciences()
    print("\nScience categories available:")
    categories = set(s['category'] for s in sciences[:20])
    for cat in sorted(categories):
        print(f"  - {cat}")
    
    print("\nExample science combinations:")
    print("  Medical: 1, 8, 3 (Geometric + Healing + Restoration)")
    print("  Agricultural: 16, 2, 14 (Agriculture + Calculation + Building)")
    print("  Educational: 10, 11, 13 (Reason + Wisdom + Hearing)")
    
    sci_input = input("\nScience IDs (space separated, default: 1 8 3): ").strip()
    if sci_input:
        try:
            science_ids = [int(x) for x in sci_input.split()]
        except:
            print("Invalid input, using defaults")
            science_ids = [1, 8, 3]
    else:
        science_ids = [1, 8, 3]
    
    # Get components
    print("\nDefine components (press Enter when done):")
    components = []
    i = 1
    while True:
        comp = input(f"Component {i}: ").strip()
        if not comp:
            break
        components.append(comp)
        i += 1
    
    if not components:
        components = None  # Use defaults
    
    # Generate
    result = generate_template(name, science_ids, components)
    
    # Save
    safe_name = ''.join(c for c in name if c.isalnum() or c in ' _-')
    safe_name = safe_name.replace(' ', '_')
    filename = f"{safe_name}.md"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(result)
    
    print(f"\n✅ APPLICATION GENERATED: {filename}")
    print(f"   Open it to see your template")
    print(f"   Next: Fill in metrics for Q gate, universality for U gate, failure tests for F gate")

def menu_contamination():
    """Check for contamination"""
    print("\n" + "="*40)
    print("CONTAMINATION SCANNER")
    print("="*40)
    
    print("\nEnter text to scan (Ctrl+D to finish on Mac/Linux, Ctrl+Z on Windows):")
    
    try:
        lines = []
        while True:
            line = input()
            lines.append(line)
    except EOFError:
        pass
    
    text = "\n".join(lines)
    
    if not text.strip():
        print("No text provided. Example scan:")
        text = "The anatomical structure requires mathematical analysis of physical systems."
    
    findings = check_contamination(text)
    
    if not findings:
        print("\n✅ NO CONTAMINATION FOUND")
        print("Text is pure USLaP terminology")
        return
    
    print(f"\n⚠️  CONTAMINATION FOUND: {len(findings)} issues")
    print("-" * 50)
    
    # Group by category
    by_category = {}
    for finding in findings:
        cat = finding['category']
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(finding)
    
    for category, items in by_category.items():
        print(f"\n{category} Category: {explain_category(category)}")
        print("-" * 30)
        for item in items:
            print(f"  '{item['term']}' → '{item['replacement']}'")
            print(f"     Reason: {item['reason']}")
    
    # Show cleaned version
    cleaned = text
    for finding in sorted(findings, key=lambda x: x['position'], reverse=True):
        # Simple replacement
        cleaned = cleaned.replace(finding['term'], finding['replacement'])
    
    print("\n" + "="*50)
    print("CLEANED VERSION:")
    print("="*50)
    print(cleaned)

def menu_sciences():
    """Browse 111 sciences"""
    print("\n" + "="*40)
    print("111 SCIENCES BROWSER")
    print("="*40)
    
    sciences = load_sciences()
    
    while True:
        print("\n[1] View all (first 20)")
        print("[2] Search by category")
        print("[3] Search by root")
        print("[4] View specific ID")
        print("[5] Back to main menu")
        
        choice = input("\nChoose (1-5): ").strip()
        
        if choice == "1":
            print("\nFirst 20 Sciences:")
            for sci in sciences[:20]:
                print(f"\n{sci['id']}. {sci['arabic']}")
                print(f"   English: {sci['en']}")
                print(f"   Root: {sci['root']} | Quran: {sci['quran']}")
                print(f"   Category: {sci['category']}")
        
        elif choice == "2":
            categories = set(s['category'] for s in sciences)
            print("\nCategories:", ", ".join(sorted(categories)))
            cat = input("Enter category: ").strip().lower()
            
            matches = [s for s in sciences if s['category'].lower() == cat]
            if matches:
                for sci in matches[:10]:  # Limit to 10
                    print(f"{sci['id']}. {sci['arabic']} ({sci['en']})")
                if len(matches) > 10:
                    print(f"... and {len(matches)-10} more")
            else:
                print("No sciences in that category")
        
        elif choice == "3":
            root = input("Enter 3-letter root (e.g., ق-د-ر): ").strip()
            matches = [s for s in sciences if s['root'] == root]
            
            if matches:
                for sci in matches:
                    print(f"{sci['id']}. {sci['arabic']} ({sci['en']})")
            else:
                print("No sciences with that root")
        
        elif choice == "4":
            try:
                sci_id = int(input("Science ID (1-111): ").strip())
                if 1 <= sci_id <= 111:
                    sci = sciences[sci_id-1]
                    print(f"\n{sci['id']}. {sci['arabic']}")
                    print(f"   English: {sci['en']}")
                    print(f"   Root: {sci['root']}")
                    print(f"   Quran: {sci['quran']}")
                    print(f"   Category: {sci['category']}")
                else:
                    print("ID must be between 1 and 111")
            except:
                print("Invalid ID")
        
        elif choice == "5":
            break

def menu_verify():
    """Verify Q-U-F gates"""
    print("\n" + "="*40)
    print("Q-U-F GATES VERIFICATION")
    print("="*40)
    
    print("\nQ-U-F Gates are the core of USLaP:")
    print("  **Q = Quantification**: Everything measurable")
    print("  **U = Universality**: Works for all humans, eras, cultures")
    print("  **F = Falsification**: Clear testable failure conditions")
    
    print("\nExample application data:")
    example = {
        'name': 'Surgical Robot',
        'metrics': [
            {'name': 'Precision', 'unit': 'mm', 'value': 0.1},
            {'name': 'Success rate', 'unit': '%', 'value': 99.5}
        ],
        'limitations': [],
        'failure_conditions': [
            {'desc': 'Precision loss', 'test': 'measure with calipers', 'threshold': '>0.5mm error'},
            {'desc': 'System failure', 'test': 'operational test', 'threshold': 'any component fails'}
        ]
    }
    
    print(f"\nVerifying: {example['name']}")
    
    q_ok, q_msg = QGate.verify(example)
    u_ok, u_msg = UGate.verify(example)
    f_ok, f_msg = FGate.verify(example)
    
    print("\nResults:")
    print(f"  Q Gate: {'✅' if q_ok else '❌'} {q_msg}")
    print(f"  U Gate: {'✅' if u_ok else '❌'} {u_msg}")
    print(f"  F Gate: {'✅' if f_ok else '❌'} {f_msg}")
    
    if all([q_ok, u_ok, f_ok]):
        print("\n🎉 APPLICATION PASSES ALL GATES!")
        print("Ready for implementation")
    else:
        print("\n⚠️  APPLICATION NEEDS IMPROVEMENT")
        print("Fix the issues above before proceeding")

def menu_about():
    """About USLaP"""
    print("\n" + "="*40)
    print("ABOUT USLaP")
    print("="*40)
    
    about = """
USLaP (Universal Scientific Lattice Protocol) is a pure,
contamination-free scientific framework derived from four
authorized sources only:

1. Holy Qur'an - Primary textual genesis
2. Authentic Hadith - Prophetic guidance
3. Ibn Sīnā's القانون في الطب - Medical science only
4. Al-Khwārizmī's كتاب الجبر والمقابلة - Mathematical methods only

EVERYTHING ELSE = CONTAMINATION.

The system includes:
• 111 Sciences from Qur'anic 3-letter roots
• Q-U-F Gates (Quantification, Universality, Falsification)
• Contamination scanner (removes Greek/Latin/person names)
• Application generator

PRINCIPLES:
• Any literate person can verify
• No person worship (no Newtonian, Euclidean, etc.)
• No dead language roots (Greek/Latin)
• No cadaver science (anatomy/dissection-based)
• Pure Arabic/English terminology only

This single-file version contains everything needed to
start building USLaP applications immediately.
"""
    
    print(about)
    
    print("\nFiles in your HF repo:")
    print("• USLaP_OPERATIONAL_SPEC.txt - Core protocol")
    print("• Anti-contamination protocol.txt - Purity rules")
    print("• NonScience list.txt - What to reject")
    print("• Corpus.txt - 111 sciences framework")
    print("• USLaP_Sciences_Table.xlsx - Complete table")
    
    print("\nThis builder: uslap.py")
    print("Run: python3 uslap.py")

# ==================== MAIN ====================
def main():
    print_header()
    
    while True:
        print("\n" + "="*30)
        print("MAIN MENU")
        print("="*30)
        print("[1] Generate new application")
        print("[2] Check for contamination")
        print("[3] Browse 111 sciences")
        print("[4] Verify Q-U-F gates")
        print("[5] About USLaP")
        print("[6] Exit")
        
        choice = input("\nChoose (1-6): ").strip()
        
        if choice == "1":
            menu_generate()
        elif choice == "2":
            menu_contamination()
        elif choice == "3":
            menu_sciences()
        elif choice == "4":
            menu_verify()
        elif choice == "5":
            menu_about()
        elif choice == "6":
            print("\nThank you for using USLaP Builder!")
            print("بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ")
            break
        else:
            print("Please choose 1-6")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nUSLaP Builder stopped.")
    except Exception as e:
        print(f"\nError: {e}")
        print("Please report this issue.")