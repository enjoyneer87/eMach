import numpy as np
import copy

class Point:
    def __init__(self, x=0.0, y=0.0):
        self.x = x
        self.y = y
        self.R = 0.0
        self.beta = 0.0
        self.c2p()

    def c2p(self):
        """Cartesian to Polar"""
        self.R = np.hypot(self.x, self.y)
        self.beta = np.arctan2(self.y, self.x)
        return self

    def p2c(self):
        """Polar to Cartesian"""
        self.x = self.R * np.cos(self.beta)
        self.y = self.R * np.sin(self.beta)
        
        # Fix for potential precision issues at pi/2
        mask = np.isclose(self.beta, np.pi/2)
        if np.ndim(mask) == 0: # Scalar
            if mask:
                self.x = 0.0
        else: # Array
            self.x[mask] = 0.0
        return self

    def yb2xR(self):
        """Calculate x and R given y and beta"""
        self.x = self.y / np.tan(self.beta)
        self.R = np.hypot(self.x, self.y)
        return self

    def xb2yR(self):
        """Calculate y and R given x and beta"""
        self.y = self.x * np.tan(self.beta)
        self.R = np.hypot(self.x, self.y)
        return self

    def rot(self, angle):
        """Rotate point by angle (radians)"""
        self.beta += angle
        self.p2c()
        return self

    def mrr(self, angle):
        """Mirror point around line at angle (radians)"""
        m = np.tan(angle)
        factor = 1 / (1 + m**2)
        mat = np.array([[1 - m**2, 2 * m],
                        [2 * m, m**2 - 1]])
        
        vec = np.array([self.x, self.y])
        new_vec = factor * mat @ vec
        
        self.x = new_vec[0]
        self.y = new_vec[1]
        self.c2p()
        return self
    
    def copy(self):
        return copy.deepcopy(self)

class Line:
    def __init__(self, P1=None, P2=None):
        self.P1 = P1 if P1 else Point()
        self.P2 = P2 if P2 else Point()
        self.length = 0.0
        if P1 and P2:
            self.update_length()

    def def_(self, P1, P2): 
        self.P1 = P1.copy()
        self.P2 = P2.copy()
        self.update_length()
        return self
    
    def define(self, P1, P2):
        return self.def_(P1, P2)

    def update_length(self):
        self.length = np.hypot(self.P1.x - self.P2.x, self.P1.y - self.P2.y)

    def rot(self, angle):
        self.P1.rot(angle)
        self.P2.rot(angle)
        self.update_length()
        return self

    def flip(self):
        self.P1, self.P2 = self.P2, self.P1
        return self
    
    def mrr(self, angle):
        self.P1.mrr(angle)
        self.P2.mrr(angle)
        return self
    
    def plot(self, ax=None):
        pass

    def copy(self):
        return copy.deepcopy(self)

class Arc:
    def __init__(self, C1=None, C2=None, Or=None):
        self.C1 = C1 if C1 else Point()
        self.C2 = C2 if C2 else Point()
        self.Or = Or if Or else Point() # Origin
        self.r = 0.0
        self.beta_1 = 0.0
        self.beta_2 = 0.0
        if C1 and C2:
            self.update_properties()

    def def_(self, C1, C2, Or=None):
        self.C1 = C1.copy()
        self.C2 = C2.copy()
        if Or:
            self.Or = Or.copy()
        else:
            self.Or = Point(0,0)
        self.update_properties()
        return self
    
    def define(self, C1, C2, Or=None):
        return self.def_(C1, C2, Or)

    def update_properties(self):
        v1_x = self.C1.x - self.Or.x
        v1_y = self.C1.y - self.Or.y
        self.r = np.hypot(v1_x, v1_y)
        self.beta_1 = np.arctan2(v1_y, v1_x)

        v2_x = self.C2.x - self.Or.x
        v2_y = self.C2.y - self.Or.y
        self.beta_2 = np.arctan2(v2_y, v2_x)

    def discretize(self, num_points=20):
        b1 = self.beta_1
        b2 = self.beta_2
        
        # Handle wrapping if needed. 
        # If b1 > b2 and we expect CCW, we might need to add 2pi to b2?
        # Or if we just want the shortest arc?
        # MATLAB Arc usually implies CCW or specific direction.
        # Let's assume shortest path for now or check direction.
        
        angles = np.linspace(b1, b2, num_points)
        x = self.Or.x + self.r * np.cos(angles)
        y = self.Or.y + self.r * np.sin(angles)
        return x, y

    def rot(self, angle):
        self.C1.rot(angle)
        self.C2.rot(angle)
        self.Or.rot(angle)
        self.update_properties()
        return self
    
    def mrr(self, angle):
        self.C1.mrr(angle)
        self.C2.mrr(angle)
        self.Or.mrr(angle)
        self.update_properties()
        return self
    
    def flip(self):
        self.C1, self.C2 = self.C2, self.C1
        self.update_properties()
        return self

    def copy(self):
        return copy.deepcopy(self)

def fillet_L2L(P1, P2, P3, r, construction=None):
    v1 = np.array([P1.x - P2.x, P1.y - P2.y])
    v2 = np.array([P3.x - P2.x, P3.y - P2.y])
    
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    
    if norm1 == 0 or norm2 == 0:
        return Arc()
        
    n1 = v1 / norm1
    n2 = v2 / norm2
    
    dot_val = np.clip(np.dot(n1, n2), -1.0, 1.0)
    angle = np.arccos(dot_val)
    
    if np.isclose(angle, 0) or np.isclose(angle, np.pi):
        return Arc()

    d = r / np.tan(angle / 2.0)
    
    T1 = Point(P2.x + n1[0] * d, P2.y + n1[1] * d)
    T2 = Point(P2.x + n2[0] * d, P2.y + n2[1] * d)
    
    bisector = n1 + n2
    bisector_norm = np.linalg.norm(bisector)
    if bisector_norm == 0:
        return Arc()
        
    bisector = bisector / bisector_norm
    
    dist_to_center = r / np.sin(angle / 2.0)
    
    C = Point(P2.x + bisector[0] * dist_to_center, P2.y + bisector[1] * dist_to_center)
    
    return Arc(T1, T2, C)

def fillet_A2L(P_arc_far, P_corner, P_line_far, dummy, r, construction=None):
    # P_arc_far: Point on the line (end of line segment)
    # P_corner: Intersection point
    # P_line_far: Point on the arc (start of arc segment)
    # Note: The naming in function args vs usage might be swapped.
    # Usage: fillet_A2L(P_r10, P_r11, P_r12, ...)
    # P10 (OD), P11 (Corner), P12 (Notch Bottom).
    # Arc is P12 -> P11. Line is P11 -> P10.
    # So P_line_far is P12. P_corner is P11. P_arc_far is P10.
    
    v_chord = np.array([P_line_far.x - P_corner.x, P_line_far.y - P_corner.y])
    
    t1 = np.array([-P_corner.y, P_corner.x])
    t2 = np.array([P_corner.y, -P_corner.x])
    
    if np.dot(t1, v_chord) > np.dot(t2, v_chord):
        t_back = t1
    else:
        t_back = t2
        
    scale = np.linalg.norm(v_chord) 
    P_virtual_arc = Point(P_corner.x + t_back[0]/np.linalg.norm(t_back)*scale, 
                          P_corner.y + t_back[1]/np.linalg.norm(t_back)*scale)
                          
    return fillet_L2L(P_virtual_arc, P_corner, P_arc_far, r)
