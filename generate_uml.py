#!/usr/bin/env python3
"""
Auto-generate PlantUML diagrams from Pyleecan OOP structure
using py2puml
"""

import sys
sys.path.insert(0, r'd:\gitfolder\pyleecan')

from py2puml.py2puml import py2puml

# Generate UML for key Pyleecan classes
classes_to_generate = [
    ('pyleecan.Classes', 'Machine'),
    ('pyleecan.Classes', 'Lamination'),
    ('pyleecan.Classes', 'Stator'),
    ('pyleecan.Classes', 'Rotor'),
    ('pyleecan.Classes', 'Slot'),
    ('pyleecan.Classes', 'Winding'),
    ('pyleecan.Classes', 'Simulation'),
]

output_dir = r'd:\KangDH\Emlab_emach\Plan\UML'

for module_name, class_name in classes_to_generate:
    try:
        full_name = f"{module_name}.{class_name}"
        output_file = f"{output_dir}\\Auto_{class_name}_UML_generated.puml"
        
        print(f"Generating UML for {full_name}...")
        py2puml(full_name, output_file)
        print(f"  ✓ Saved to {output_file}")
    except Exception as e:
        print(f"  ✗ Error: {e}")

print("\nUML generation complete!")
