function psiXi=calcProxyEffFun(coeffixi,freqE)
if nargin>1
    coeffixi=coeffixi.*sqrt(freqE);
end
[originx,new1term,new2term]=eqHyperbolic(coeffixi);
% freqE=1200
% psiXi=2*coeffixi.*((sinh(coeffixi)-sin(coeffixi))/(cosh(coeffixi)+cos(coeffixi)))
psiXi=2*coeffixi.*new2term*2;
end