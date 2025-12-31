import numpy as np
from shapely.geometry import Polygon, MultiPolygon
import matplotlib.pyplot as plt

def check_feasibility(shapes, angle_deg, debug_plot=False):
    """
    Checks feasibility of shapes.
    shapes: list of Shape objects
    angle_deg: symmetry angle in degrees
    """
    flag = True
    angle_rad = np.deg2rad(angle_deg)
    epsilon = 1e-9

    polys = []
    
    for i, shape in enumerate(shapes):
        if shape.poly is None or shape.poly.is_empty:
            continue
            
        # 1. Check for split regions (MultiPolygon)
        # In MATLAB code, if NumRegions > 1, it warns.
        if isinstance(shape.poly, MultiPolygon):
            print(f"Warning: Shape {i} ({shape.description}) has multiple regions (split).")
            if debug_plot:
                shape.plot(color='r')
            # flag = False # Depending on strictness

        # 2. Symmetry Check
        # Check if any vertex is outside [0, angle]
        # Get all vertices
        if isinstance(shape.poly, MultiPolygon):
            geoms = shape.poly.geoms
        else:
            geoms = [shape.poly]
            
        for geom in geoms:
            x, y = geom.exterior.xy
            x = np.array(x)
            y = np.array(y)
            
            # Cartesian to Polar
            beta = np.arctan2(y, x)
            # Normalize beta to [0, 2pi) or similar if needed, but usually geometry is in Q1
            # Handle negative angles slightly below 0 due to precision
            
            # Check bounds
            # beta > angle + eps
            # beta < 0 - eps
            
            if np.any(beta > (angle_rad + epsilon)) or np.any(beta < -epsilon):
                print(f"Feasibility Fail: Shape {i} ({shape.description}) points beyond symmetry line.")
                flag = False
                if debug_plot:
                    shape.plot(color='r')

        polys.append(shape.poly)

    # 3. Overlap Check
    # Check intersection between all pairs
    n = len(polys)
    for i in range(n):
        for j in range(i + 1, n):
            p1 = polys[i]
            p2 = polys[j]
            
            # Intersection
            if p1.intersects(p2):
                intersection = p1.intersection(p2)
                # Touching is fine (line or point intersection), overlapping area is bad
                if not intersection.is_empty and intersection.area > 1e-6: # Tolerance for area
                    print(f"Feasibility Fail: Overlap detected between Shape {i} and Shape {j}.")
                    flag = False
                    if debug_plot:
                        # Plot overlap
                        fig, ax = plt.subplots()
                        shapes[i].plot(ax=ax, color='b')
                        shapes[j].plot(ax=ax, color='g')
                        # Plot intersection
                        if intersection.geom_type == 'Polygon':
                            x, y = intersection.exterior.xy
                            ax.fill(x, y, color='r', alpha=0.8)
                        plt.show()

    return flag
