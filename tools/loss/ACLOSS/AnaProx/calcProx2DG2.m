function [coeffiRadial,coeffiTheta]=calcProx2DG2(dimensions,freqE)
    w = mm2m(dimensions(1)); % 폭 [m]
    h = mm2m(dimensions(2)); % 높이 [m]
    delta         =mm2m(calcSkinDepth(freqE));           % 스킨 깊이 [m]
    [delta_w_prime,~] = calcSkinDepthModi(w,h,freqE);  % w' > 나누기 2h
    [delta_h_prime,~] = calcSkinDepthModi(h,w,freqE);  % h' > 나누기 2w
    % 무차원 형상 파라미터 계산
    gamma_w=calcNonDimParaGamma(w,delta);
    gamma_h=calcNonDimParaGamma(h,delta);
    % ** 무차원 형상파라미터 by 수정된 skinDepth
    gamma_w_prime=calcNonDimParaGamma(w,delta_w_prime);
    gamma_h_prime=calcNonDimParaGamma(h,delta_h_prime);
    %% g2 fun  Harmonic order, > layer, slot, subline ,rpm,id,iq  
    
    coeffiRadial = calcProxg2(gamma_w, gamma_h);
    coeffiTheta  = calcProxg2(gamma_h,gamma_w);
end