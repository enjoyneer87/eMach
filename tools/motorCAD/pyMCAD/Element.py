class Element:
    """Data for a 1st order triangular element and its associated stress and strain

    Parameters
    ----------
    tri_index : int
        The triangle element index number
    node_1 : int
        The ID of the first node in this element
    node_2 : int
        The ID of the second node in this element
    node_3 : int
        The ID of the third node in this element
    x : float
        The X position in mm of the element
    y : float
        The Y position in mm of the element
    Bx : float
        The Bx matrix value for this element    
    By : float
        The By matrix value for this element
    A : float
        The Magnetic vector potential for this element
    J : float
        The Current density for this element


    Attributes
    ----------
    tri_index : int
        The triangle element index number
    node_1 : int
        The ID of the first node in this element
    node_2 : int
        The ID of the second node in this element
    node_3 : int
        The ID of the third node in this element
    x : float
        The X position in mm of the element
    y : float
        The Y position in mm of the element
    Bx : float
        The Bx matrix value for this element
    By : float
        The By matrix value for this element
    A : float
        The Magnetic vector potential for this element
    J : float
        The Current density for this element
            
    """

    def __init__(
        self, tri_index, node_1, node_2, node_3, x, y, Bx, By, A, J
    ):
        self.tri_index = tri_index
        self.node_1 = node_1
        self.node_2 = node_2
        self.node_3 = node_3

        self.x = x
        self.y = y

        self.Bx = Bx
        self.By = By
        self.A = A
        self.J = J
 


