function [kr,varphiXi,coeffixi,psiXi]=calcHybridJouleLossJuHa(REFdimensions,NtCoil,freqE)

bc = mm2m(REFdimensions(1)); % 폭 [m]
hc = mm2m(REFdimensions(2)); % 높이 [m]
bm = mm2m(REFdimensions(3));  % slot widht

% freqE=1200
coeffixi=calckXi4EddyLoss(hc,bc,bm);
varphiXi=calcSkinEffFun(coeffixi,freqE)
psiXi   =calcProxyEffFun(coeffixi,freqE)
% 
% coeffixi=calckXi4EddyLoss(hc,bc,bm,freqE)
% varphiXi=calcSkinEffFun(coeffixi)
% psiXi   =calcProxyEffFun(coeffixi)
% 
% % coeffiXi=calckXi4EddyLoss(hc,bc,b,freqE,sigma,mu_c);
%
% psiXi   =calcProxyEffFun(coeffixi,freqE);
% [FIX 2026-07-14] 기존식 kr=varphiXi+(NtCoil^2-0.2)/9.*coeffixi.^4 버그 수정:
%   coeffixi는 주파수 미포함(calckXi4EddyLoss 3인자 호출)이라 proximity 항이
%   주파수 무관 상수가 되고, Dowell 계층식 (m^2-1)/3*psi(xi)가 ad-hoc /9*xi^4로
%   대체되어 있었음. 표준 Dowell: kR = varphi(xi) + (Nt^2-1)/3 * psi(xi)
%   (psiXi는 위에서 freqE 포함으로 이미 계산됨)
kr=varphiXi+(NtCoil^2-1)/3.*psiXi;


end