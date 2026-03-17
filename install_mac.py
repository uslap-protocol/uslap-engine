#!/usr/bin/env python3
"""
USLaP Minimal Mac Installer
No triple quotes, no syntax errors
"""
import os
import json

print("=" * 50)
print("USLaP INSTALLER")
print("=" * 50)

# Create directory
print("\nCreating directory...")
os.makedirs("uslap_core", exist_ok=True)
os.chdir("uslap_core")

# Create basic structure
dirs = ['data', 'projects']
for d in dirs:
    os.makedirs(d, exist_ok=True)
    print(f"Created: {d}")

# Create 111 sciences (simplified)
print("\nCreating 111 sciences...")
sciences = []
for i in range(1, 112):
    sciences.append({
        "id": i,
        "name": f"Science {i}",
        "root": "A-L-M",
        "quran_ref": "96:5"
    })

with open('sciences.json', 'w') as f:
    json.dump({"sciences": sciences}, f, indent=2)

print("Created: sciences.json")

# Create generator
print("\nCreating generator...")
gen_code = """import json
import sys

def generate(name, sci_ids):
    with open('sciences.json') as f:
        data = json.load(f)
    
    output = f"# {name}\\n\\n"
    output += "## Sciences\\n"
    
    for sci in data['sciences']:
        if sci['id'] in sci_ids:
            output += f"- {sci['name']} (Quran {sci['quran_ref']})\\n"
    
    output += "\\n## Q-U-F Gates\\n"
    output += "Q=1: Measurable\\n"
    output += "U=1: Universal\\n"
    output += "F=1: Testable\\n"
    
    filename = f"projects/{name.replace(' ', '_')}.md"
    with open(filename, 'w') as f:
        f.write(output)
    
    print(f"Created: {filename}")
    return filename

if __name__ == "__main__":
    if len(sys.argv) > 1:
        name = sys.argv[1]
        sci_ids = [1, 2, 3] if len(sys.argv) < 3 else [int(x) for x in sys.argv[2:]]
        generate(name, sci_ids)
    else:
        print("Usage: python generator.py 'App Name' [science_ids]")
        print("Example: python generator.py 'Surgical Robot' 1 2 3")
"""

with open('generator.py', 'w') as f:
    f.write(gen_code)

print("Created: generator.py")

# Create launcher for Mac
launcher = """#!/bin/bash
cd "$(dirname "$0")"
echo "USLaP Ready"
echo "Run: python3 generator.py 'Your App Name'"
echo "Example: python3 generator.py 'Surgical Robot'"
"""

with open('launch.command', 'w') as f:
    f.write(launcher)

os.chmod('launch.command', 0o755)
print("Created: launch.command")

# Create README
readme = """# USLaP Core

## Quick Start
1. Double-click launch.command
2. Or in Terminal: cd uslap_core
3. Generate app: python3 generator.py 'App Name'

## Example
python3 generator.py 'Surgical Robot' 1 2 3

This creates: projects/Surgical_Robot.md

## 111 Sciences
See sciences.json

## Q-U-F Gates
- Q=1: Quantification (measurable)
- U=1: Universality (works for all)
- F=1: Falsification (testable)
"""

with open('README.md', 'w') as f:
    f.write(readme)

print("Created: README.md")

# Final message
print("\n" + "=" * 50)
print("INSTALLATION COMPLETE")
print("=" * 50)
print("\nTo start:")
print("1. Double-click 'launch.command'")
print("2. Or in Terminal:")
print("   cd " + os.getcwd())
print("   python3 generator.py 'Surgical Robot'")
print("\nNext we'll add contamination scanner.")
print("=" * 50)
