function alpha=calcLayerAlphaMellor(bc,b,freqE,Nl)
% all input shoule be in meter
if nargin<4
    elec.T0.resistivity = 1.724E-8;   % 저항값 (옴·미터)
    sigma = 1 / elec.T0.resistivity;  % 전기전도도 (S/m)
    rho   = 1/sigma; 
    mu0 = 4*pi*10^-7;                 % [H/m]
    mu_c = mu0;                       % 도체와 공기 중 투자율이 같은 것으로 가정
end

%% default value
diffusionFactor=mu_c*sigma;
omeagE=freq2omega(freqE);

%%
% coeffiXi= hc*sqrt(0.5*freq2omega(freqE)*mu_c*sigma*bc/b);
epL= Nl*(bc/b);
% % sqrt(epL)== sqrt(bc/b)
% eta= sqrt(epL)*(hc/delta)


SkinDepth_delta_inmm  = calcSkinDepth(freqE);
skinDepth_delta_inm   = mm2m(SkinDepth_delta_inmm);
% PeneteDepth= 1/sqrt(0.5*diffusionFactor*omeagE*bc/b);
PeneteDepth= skinDepth_delta_inm/sqrt(bc/b);
alpha      = 1/PeneteDepth;   %  sqrt(bc/b)/skinDepth_delta_inm

end