function varphiXi=calcSkinEffFun(coeffXi,freqE)
coeffXi=coeffXi*sqrt(freqE);
varphiXi=coeffXi.*(sinh(2*coeffXi)+sin(2*coeffXi))./(cosh(2*coeffXi)-cos(2*coeffXi));

end