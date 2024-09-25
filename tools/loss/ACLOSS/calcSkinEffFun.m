function varphiXi=calcSkinEffFun(coeffixi,freqE)
if nargin>1
    coeffixi=coeffixi.*sqrt(freqE);
end
[originx,new1term,new2term]=eqHyperbolic(coeffixi);
% varphiXi=coeffixi.*(sinh(2*coeffixi)+sin(2*coeffixi))./(cosh(2*coeffixi)-cos(2*coeffixi));
varphiXi=coeffixi.*originx;
end