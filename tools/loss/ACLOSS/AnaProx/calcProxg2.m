function coeffi = calcProxg2(gamma_w, gamma_h)
%% Material
    elec.T0.resistivity = 1.724E-8;  % 주어진 저항값 (옴·미터)
    elec.T0.Conductivity = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
    sigma=elec.T0.Conductivity;                      % [S/m]
    rho  = 1/sigma    ;  % resistivity (옴·미터)
    mu0  = 4*pi*10^-7 ;      % [H/m] 
    mu_c=mu0          ; %도체와 공기중 투자율이 같은것으로 가정

%% Appendix g2 - preliminary for
% xi
    [originx,new1term,new2term]=eqHyperbolic(gamma_h);
      % coeffi= (gamma_w / (sigma * mu_c^2)) * (sinh(gamma_h) - sin(gamma_h)) / (cosh(gamma_h) + cos(gamma_h));  
     coeffi=(gamma_w / (sigma * mu_c^2)) *new2term *2;
end