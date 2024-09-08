function coeffiXi=calckXi4EddyLoss(hc,bc,b,freqE,sigma,mu_c)

if nargin<5
    elec.T0.resistivity = 1.724E-8;   % 저항값 (옴·미터)
    sigma = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
    rho   = 1/sigma; 
    mu0 = 4*pi*10^-7;                 % [H/m]
    mu_c = mu0;                       % 도체와 공기 중 투자율이 같은 것으로 가정
end
coeffiXi= hc*sqrt(0.5*freq2omega(freqE)*mu_c*sigma*bc/b);

end