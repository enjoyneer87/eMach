function SkinDepth_delta_inmm = calcSkinDepth(freqE)
%% From taha2020 & 
elec.T0.resistivity = 1.724E-8;  % 주어진 저항값 (옴·미터)
elec.T0.Conductivity = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
sigma=elec.T0.Conductivity;                      % [S/m]
rho  = 1/sigma    ;  % resistivity (옴·미터)
mu0  = 4*pi*10^-7 ;      % [H/m]
% freqE = omega2freq(omegaE);
%% delta - ref calcHybridACConductorLoss.mlx 
SkinDepth_delta_taha=1./sqrt(pi*freqE*mu0*sigma);    % [m]from [Taha2020] Section III. A eq (6)
% SkinDepth_delta=sqrt((2*rho)./(omegaE.*mu0))  ;     % [m]
SkinDepth_delta_inmm=m2mm(SkinDepth_delta_taha)  ;
end