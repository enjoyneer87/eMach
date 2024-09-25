function [originx,new1term,new2term]=eqHyperbolic(x)

originx= (sinh(2*x) + sin(2*x)) / (cosh(2*x) - cos(2*x));

new1term=1/2*...
    ((sinh(x) + sin(x)) / (cosh(x) - cos(x)));
new2term=1/2*...
    ((sinh(x) - sin(x)) / (cosh(x) + cos(x)));


end