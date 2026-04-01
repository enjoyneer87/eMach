#!/usr/bin/env python3
"""
Generate PlantUML from Python source code using AST analysis
"""

import ast
import sys
import os
from pathlib import Path

# Add Pyleecan to path
sys.path.insert(0, r'd:\gitfolder\pyleecan')

class PythonToPlantUML:
    def __init__(self):
        self.classes = {}
        self.relationships = set()
    
    def parse_file(self, filepath):
        """Parse a Python file and extract class information"""
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            try:
                tree = ast.parse(f.read())
            except:
                return
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.extract_class(node, filepath)
    
    def extract_class(self, class_node, filepath):
        """Extract class definition"""
        class_name = class_node.name
        bases = [base.id if isinstance(base, ast.Name) else 
                 f"{base.value.id}.{base.attr}" if isinstance(base, ast.Attribute) 
                 else str(base) 
                 for base in class_node.bases]
        
        methods = []
        attributes = []
        
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                # Extract method signature
                args = [arg.arg for arg in item.args.args if arg.arg != 'self']
                methods.append(f"{item.name}({', '.join(args[:3])})")  # Limit to 3 args display
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attributes.append(target.id)
        
        self.classes[class_name] = {
            'bases': bases,
            'methods': methods[:5],  # Limit to 5 methods
            'attributes': attributes[:5],  # Limit to 5 attributes
            'file': filepath
        }
        
        # Record inheritance relationships
        for base in bases:
            if base and base[0].isupper():  # Only user-defined classes
                self.relationships.add((class_name, base, 'extends'))
    
    def generate_puml(self, title="Python Classes"):
        """Generate PlantUML diagram"""
        lines = [
            "@startuml auto_generated",
            "!theme plain",
            "skinparam backgroundColor #f0f0f0",
            "skinparam classBackgroundColor #e3f2fd",
            "skinparam classBorderColor #1976d2",
            "",
            f"title {title}",
            ""
        ]
        
        # Add classes
        for class_name, info in sorted(self.classes.items()):
            lines.append(f"class {class_name} {{")
            
            # Add attributes
            for attr in info['attributes'][:3]:
                lines.append(f"  {attr}")
            
            if info['attributes']:
                lines.append("  ---")
            
            # Add methods
            for method in info['methods'][:5]:
                lines.append(f"  {method}()")
            
            lines.append("}")
            lines.append("")
        
        # Add relationships
        for class_a, class_b, rel_type in self.relationships:
            if class_a in self.classes and class_b in self.classes:
                if rel_type == 'extends':
                    lines.append(f"{class_a} --|> {class_b}")
        
        lines.append("@enduml")
        return "\n".join(lines)


# Collect all Python files from Pyleecan Classes directory
pyleecan_classes_dir = r'd:\gitfolder\pyleecan\Classes'
output_file = r'd:\KangDH\Emlab_emach\Plan\UML\Auto_Pyleecan_Classes_UML_generated.puml'

parser = PythonToPlantUML()

# Parse key class files
key_files = [
    'Machine.py',
    'Stator.py', 
    'Rotor.py',
    'Lamination.py',
    'Slot.py',
    'Winding.py',
    'Simulation.py',
    'Output.py',
]

for filename in key_files:
    filepath = os.path.join(pyleecan_classes_dir, filename)
    if os.path.exists(filepath):
        print(f"Parsing {filename}...")
        parser.parse_file(filepath)
        print(f"  ✓ Found {len(parser.classes)} classes so far")
    else:
        print(f"  ✗ Not found: {filepath}")

# Generate PlantUML
print(f"\nGenerating PlantUML diagram with {len(parser.classes)} classes...")
puml_content = parser.generate_puml(title="Pyleecan: Core Classes (Auto-Generated from AST)")

# Write to file
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(puml_content)

print(f"✓ Saved to {output_file}")
print(f"\nGenerated {len(parser.classes)} classes and {len(parser.relationships)} relationships")
print("\nClasses found:")
for cls in sorted(parser.classes.keys()):
    print(f"  - {cls}")
