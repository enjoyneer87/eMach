import numpy as np
from shapely.geometry import Polygon, MultiPolygon
import matplotlib.pyplot as plt
from .geometry import Region, Line, Arc

def region_to_shapely(region, discretization_step=2.0):
    """
    Convert a Motor-CAD Region object to a Shapely Polygon.
    Arcs are discretized into line segments.
    
    Parameters
    ----------
    region : Region
        The region to convert.
    discretization_step : float
        Angle in degrees to discretize arcs.
        
    Returns
    -------
    shapely.geometry.Polygon
    """
    points = []
    
    if not region.entities:
        return None

    # Assume entities are ordered and connected
    # Start with the start point of the first entity
    first_entity = region.entities[0]
    points.append((first_entity.start.x, first_entity.start.y))
    
    for entity in region.entities:
        if isinstance(entity, Line):
            points.append((entity.end.x, entity.end.y))
        elif isinstance(entity, Arc):
            # Discretize arc
            total_angle = entity.total_angle
            num_segments = int(np.ceil(total_angle / discretization_step))
            if num_segments < 1:
                num_segments = 1
                
            for i in range(1, num_segments + 1):
                fraction = i / num_segments
                coord = entity.get_coordinate_from_distance(entity.start, fraction=fraction)
                points.append((coord.x, coord.y))
                
    # Create Polygon
    poly = Polygon(points)
    
    # Fix invalid topology (e.g. self-intersection)
    if not poly.is_valid:
        poly = poly.buffer(0)
        
    return poly

def check_feasibility(regions, angle_deg, debug_plot=False):
    """
    Checks feasibility of regions (Motor-CAD geometry).
    
    Parameters
    ----------
    regions : list of Region
        List of Motor-CAD Region objects.
    angle_deg : float
        Symmetry angle in degrees (e.g., 45 for 8 pole).
    debug_plot : bool
        Whether to plot failures.
        
    Returns
    -------
    bool
        True if feasible, False otherwise.
    """
    flag = True
    angle_rad = np.deg2rad(angle_deg)
    epsilon = 1e-9

    polys = []
    
    for i, region in enumerate(regions):
        poly = region_to_shapely(region)
        
        if poly is None or poly.is_empty:
            continue
            
        # 1. Check for split regions (MultiPolygon)
        if isinstance(poly, MultiPolygon):
            print(f"Warning: Region {i} ({region.name}) has multiple parts (split).")
            if debug_plot:
                # Simple plot for debug
                x, y = poly.convex_hull.exterior.xy
                plt.plot(x, y, 'r-')
            # flag = False # Optional strictness

        # 2. Symmetry Check
        # Check if any vertex is outside [0, angle]
        if isinstance(poly, MultiPolygon):
            geoms = poly.geoms
        else:
            geoms = [poly]
            
        for geom in geoms:
            x, y = geom.exterior.xy
            x = np.array(x)
            y = np.array(y)
            
            # Cartesian to Polar
            beta = np.arctan2(y, x)
            
            # Check bounds
            # beta > angle + eps
            # beta < 0 - eps
            
            if np.any(beta > (angle_rad + epsilon)) or np.any(beta < -epsilon):
                print(f"Feasibility Fail: Region {i} ({region.name}) points beyond symmetry line.")
                flag = False
                if debug_plot:
                    plt.figure()
                    plt.plot(x, y, 'r-')
                    plt.title(f"Fail: Region {i} Symmetry")
                    plt.show()

        polys.append(poly)

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
                    print(f"Feasibility Fail: Overlap detected between Region {i} and Region {j}.")
                    flag = False
                    if debug_plot:
                        # Plot overlap
                        fig, ax = plt.subplots()
                        # Plot p1
                        x1, y1 = p1.convex_hull.exterior.xy
                        ax.plot(x1, y1, 'b', label=f'Region {i}')
                        # Plot p2
                        x2, y2 = p2.convex_hull.exterior.xy
                        ax.plot(x2, y2, 'g', label=f'Region {j}')
                        
                        # Plot intersection
                        if intersection.geom_type == 'Polygon':
                            xi, yi = intersection.exterior.xy
                            ax.fill(xi, yi, color='r', alpha=0.5, label='Overlap')
                        elif intersection.geom_type == 'MultiPolygon':
                            for geom in intersection.geoms:
                                xi, yi = geom.exterior.xy
                                ax.fill(xi, yi, color='r', alpha=0.5)
                                
                        ax.legend()
                        plt.title(f"Fail: Overlap {i}-{j}")
                        plt.show()

    return flag
