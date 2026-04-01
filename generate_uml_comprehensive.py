#!/usr/bin/env python3
"""
Generate comprehensive PlantUML from all Pyleecan Classes
using AST analysis of actual Python source files
"""

import ast
import os
from pathlib import Path
from collections import defaultdict

class PyleecanUMLGenerator:
    def __init__(self):
        self.classes = {}
        self.relationships = {}
    
    def parse_directory(self, directory):
        """Parse all Python files in directory"""
        files = [f for f in os.listdir(directory) 
                if f.endswith('.py') and f[0].isupper() and f != '__init__.py']
        
        for filename in sorted(files):
            filepath = os.path.join(directory, filename)
            self.parse_file(filepath, filename[:-3])  # Remove .py
    
    def parse_file(self, filepath, class_hint=None):
        """Parse a Python file"""
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                tree = ast.parse(f.read())
        except:
            return
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                self.extract_class(node)
    
    def extract_class(self, class_node):
        """Extract class definition"""
        name = class_node.name
        
        # Get base classes
        bases = []
        for base in class_node.bases:
            if isinstance(base, ast.Name):
                bases.append(base.id)
            elif isinstance(base, ast.Attribute):
                bases.append(f"{base.attr}")
            elif isinstance(base, ast.Subscript):
                # Handle generic types
                pass
        
        # Get attributes and methods
        attrs = []
        methods = []
        
        for item in class_node.body:
            if isinstance(item, ast.FunctionDef):
                if item.name not in ['__init__', '__str__', '__eq__', '__repr__']:
                    methods.append(item.name)
            elif isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name):
                attrs.append(item.target.id)
            elif isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        attrs.append(target.id)
        
        self.classes[name] = {
            'bases': bases,
            'methods': methods[:5],  # Limit display
            'attributes': attrs[:5],
        }
    
    def generate_puml(self, title="Pyleecan: All Classes (Auto-Generated)"):
        """Generate PlantUML code"""
        lines = [
            "@startuml pyleecan_allclasses_generated",
            "!theme plain  ",
            "skinparam backgroundColor #f0f0f0",
            "skinparam classBackgroundColor #e3f2fd",
            "skinparam classBorderColor #1976d2",
            "",
            f"title {title}",
            f"note \"Auto-generated from {len(self.classes)} Pyleecan classes\" as N0",
            "",
        ]
        
        # Group classes by category (simple heuristic)
        machine_classes = [c for c in self.classes if 'Machine' in c]
        lamination_classes = [c for c in self.classes if 'Lam' in c]
        slot_classes = [c for c in self.classes if 'Slot' in c]
        bore_classes = [c for c in self.classes if 'Bore' in c]
        geometry_classes = [c for c in self.classes if any(x in c for x in ['Arc', 'Line', 'Circle', 'Surface'])]
        other_classes = [c for c in self.classes 
                        if c not in machine_classes + lamination_classes + slot_classes + bore_classes + geometry_classes]
        
        # Add classes by group
        def add_class_group(classes, package_name=None):
            if not classes:
                return
            if package_name:
                lines.append(f"package \"{package_name}\" {{")
            for class_name in sorted(classes):
                info = self.classes[class_name]
                lines.append(f"class {class_name} {{")
                
                # Attributes
                for attr in info['attributes'][:2]:
                    lines.append(f"  {attr}: type")
                
                if info['attributes'] or info['methods']:
                    lines.append("  ---")
                
                # Methods
                for method in info['methods'][:3]:
                    lines.append(f"  {method}()")
                
                lines.append("}")
            if package_name:
                lines.append("}")
            lines.append("")
        
        add_class_group(machine_classes, "Machine Types (12)")
        add_class_group(lamination_classes, "Lamination & Layers")
        add_class_group(slot_classes, "Slot Types (50+)")
        add_class_group(bore_classes, "Bore Geometries")
        add_class_group(geometry_classes, "Geometric Primitives")
        add_class_group(other_classes, "Other Classes")
        
        # Add relationships
        for class_name, info in self.classes.items():
            for base in info['bases']:
                if base in self.classes and base != 'object':
                    lines.append(f"{class_name} --|> {base}")
        
        lines.append("")
        lines.append("@enduml")
        
        return "\n".join(lines)


# Main execution
if __name__ == '__main__':
    classes_dir = r'd:\gitfolder\pyleecan\Classes'
    output_file = r'd:\KangDH\Emlab_emach\Plan\UML\Auto_Pyleecan_AllClasses_UML.puml'
    
    print(f"Analyzing {classes_dir}...")
    print(f"Found {len([f for f in os.listdir(classes_dir) if f.endswith('.py')])} Python files")
    
    generator = PyleecanUMLGenerator()
    generator.parse_directory(classes_dir)
    
    print(f"Extracted {len(generator.classes)} classes")
    print(f"\nTop classes found:")
    for cls in sorted(list(generator.classes.keys())[:20]):
        bases = generator.classes[cls]['bases']
        if bases:
            print(f"  {cls} extends {bases}")
        else:
            print(f"  {cls}")
    
    # Generate and save
    puml = generator.generate_puml()
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(puml)
    
    print(f"\n✓ Generated PlantUML saved to:")
    print(f"  {output_file}")
    print(f"\nStatistics:")
    print(f"  - Total classes: {len(generator.classes)}")
    print(f"  - Lines of PlantUML: {len(puml.split(chr(10)))}")
