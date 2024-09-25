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
% kr=varphiXi+(NtCoil^2-1)/3*psiXi;
kr=varphiXi+(NtCoil^2-0.2)/9.*coeffixi.^4;


end