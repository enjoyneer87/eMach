function varphiXi=calcSkinEffFun(coeffXi)

varphiXi=coeffXi.*(sinh(2*coeffXi)+sin(2*coeffXi))./(cosh(2*coeffXi)-cos(2*coeffXi));

end