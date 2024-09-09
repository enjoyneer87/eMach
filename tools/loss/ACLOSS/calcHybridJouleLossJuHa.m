function kr=calcHybridJouleLossJuHa(REFdimensions,NtCoil,freqE)

bc = mm2m(REFdimensions(1)); % 폭 [m]
hc = mm2m(REFdimensions(2)); % 높이 [m]
bm = mm2m(REFdimensions(3));  % slot widht
coeffiXi=calckXi4EddyLoss(hc,bc,bm,freqE);

% coeffiXi=calckXi4EddyLoss(hc,bc,b,freqE,sigma,mu_c);

psiXi   =calcProxyEffFun(coeffiXi);
varphiXi=calcSkinEffFun(coeffiXi);
% kr=varphiXi+(NtCoil^2-1)/3*psiXi;
kr=varphiXi+(NtCoil^2-0.2)/9.*coeffiXi.^4;


end