from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import numpy as np
import matplotlib.pyplot as plt
import copy

class Shape:
    def __init__(self, vertices=None):
        self.description = ""
        self.poly = None
        if vertices is not None:
            self.poly = Polygon(vertices)
        
        self.layer = 0
        self.number = 0
        self.density = 0.0
        self.mass = 0.0
        self.length = 0.0
        self.volume = 0.0
        self.shape_area = 0.0
        self.output_string = "" # ost

    def create_from_vertices(self, x, y):
        """Create polygon from x and y arrays"""
        # Flatten if necessary
        x = np.array(x).flatten()
        y = np.array(y).flatten()
        points = list(zip(x, y))
        self.poly = Polygon(points)
        
        # Ensure validity
        if not self.poly.is_valid:
            self.poly = self.poly.buffer(0)
            
        self.update_area()
        return self

    def ply(self, x, y, dummy=None):
        """Alias for create_from_vertices to match MATLAB"""
        return self.create_from_vertices(x, y)

    def update_area(self):
        if self.poly:
            self.shape_area = self.poly.area 

    def dec(self, tolerance):
        if self.poly:
            self.poly = self.poly.simplify(tolerance, preserve_topology=True)
            self.update_area()
        return self


    def set_layer_number(self, layer, number):
        self.layer = layer
        self.number = number
        return self
    
    def lay(self, layer, number):
        return self.set_layer_number(layer, number)

    def set_weight(self, length, density):
        self.update_area()
        area_m2 = self.shape_area / 1e6
        length_m = length / 1e3
        self.volume = area_m2 * length_m
        self.mass = self.volume * density
        self.length = length
        self.density = density
        return self

    def set_description(self, desc):
        self.description = desc
        return self
    
    def des(self, desc):
        return self.set_description(desc)

    def ost(self, s):
        self.output_string = s
        return self

    def rgn(self, plot_regions, tau_pole, poleVangle):
        # Placeholder for region plotting or assignment
        pass

    def plot(self, ax=None, color='b', alpha=0.5):
        if self.poly is None or self.poly.is_empty:
            return
        
        # If ax is a list/array (like MATLAB handles), pick one or ignore
        if isinstance(ax, (list, np.ndarray)):
             # Try to pick the last one or first one? MATLAB code uses h(2)
             if len(ax) > 1:
                 ax = ax[-1] # Assume the shape plot is the last one
             elif len(ax) > 0:
                 ax = ax[0]
             else:
                 return

        if ax:
            if self.poly.geom_type == 'Polygon':
                x, y = self.poly.exterior.xy
                ax.fill(x, y, color=color, alpha=alpha, label=self.description)
                ax.plot(x, y, color='k', linewidth=1)
            elif self.poly.geom_type == 'MultiPolygon':
                for geom in self.poly.geoms:
                    x, y = geom.exterior.xy
                    ax.fill(x, y, color=color, alpha=alpha)
                    ax.plot(x, y, color='k', linewidth=1)
        return ax

    def copy(self):
        return copy.deepcopy(self)

def subtract(shape1_poly, shape2_poly):
    if shape1_poly is None: return None
    if shape2_poly is None: return shape1_poly
    
    s1 = shape1_poly
    s2 = shape2_poly
    
    if not s1.is_valid: s1 = s1.buffer(0)
    if not s2.is_valid: s2 = s2.buffer(0)
    
    try:
        return s1.difference(s2)
    except Exception:
        # Fallback for topology errors
        return s1.buffer(0).difference(s2.buffer(0))

def union(shapes_list):
    polys = []
    for s in shapes_list:
        if s.poly is not None:
            p = s.poly
            if not p.is_valid: p = p.buffer(0)
            polys.append(p)
            
    if not polys:
        return None
    try:
        return unary_union(polys)
    except Exception:
        return unary_union([p.buffer(0) for p in polys])
