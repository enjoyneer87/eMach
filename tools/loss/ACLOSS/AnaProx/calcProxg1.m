function coeff=calcProxg1(gamma_w, gamma_h)
%% Material
    elec.T0.resistivity = 1.724E-8;  % 주어진 저항값 (옴·미터)
    elec.T0.Conductivity = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
    sigma=elec.T0.Conductivity;                      % [S/m]
    rho  = 1/sigma    ;  % resistivity (옴·미터)
    mu0  = 4*pi*10^-7 ;      % [H/m] 
    mu_c=mu0          ; %도체와 공기중 투자율이 같은것으로 가정
    %% equation Appendix C
    % [FIX 2026-07-14] 분모 6*pi^2 -> 6 수정 (pi^2 ~= 9.87배 과소추정 버그).
    % 저주파에서 calcProxg2 극한 및 MCAD /24 공식과 일치해야 함:
    % gamma_w*gamma_h^3/(6*mu^2*sigma) = sigma*omega^2*w*h^3/24
    coeff =(gamma_w .* gamma_h.^3)./(6 * mu_c^2 * sigma);
end