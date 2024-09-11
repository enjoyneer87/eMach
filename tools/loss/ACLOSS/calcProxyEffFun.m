function psiXi=calcProxyEffFun(coeffiXi,freqE)
coeffiXi=coeffiXi*sqrt(freqE);
psiXi=2*coeffiXi.*(sinh(coeffiXi)-sin(coeffiXi))./(cosh(coeffiXi)+cos(coeffiXi));

end