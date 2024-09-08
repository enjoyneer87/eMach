function psiXi=calcProxyEffFun(coeffiXi)

psiXi=2*coeffiXi.*(sinh(coeffiXi)-sin(coeffiXi))./(cosh(coeffiXi)+cos(coeffiXi));

end