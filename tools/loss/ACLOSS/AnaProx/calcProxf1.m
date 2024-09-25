function coeff=calcProxf1(gamma)
%% Material
    elec.T0.resistivity = 1.724E-8;  % 주어진 저항값 (옴·미터)
    elec.T0.Conductivity = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
    sigma=elec.T0.Conductivity;                      % [S/m]
    rho  = 1/sigma    ;  % resistivity (옴·미터)
    mu0  = 4*pi*10^-7 ;      % [H/m] 
    mu_c=mu0          ; %도체와 공기중 투자율이 같은것으로 가정
    %% equation Appendix C

    coeff = (1 / (8 * pi * sigma * mu_c^2)) * gamma.^4;
end