 % hybridACLossModelStr=devCalcHybridACLossModelwithSlotB()
function [P_total, P_frequencies] = calcHarmonicHybridACLoss(dimensions, frequencies)
    % 총 손실과 주파수별 손실을 초기화
    [P1,P2]=getFFT1Dset(sigData);
    P_total = 0;
    P_frequencies = zeros(size(frequencies)); % 주파수별 손실을 저장할 배열
    
    % 각 주파수 별로 반복
    for i = 1:length(frequencies)
        % 현재 주파수
        f_i = frequencies(i);
        
        % 현재 주파수에서의 B_r 및 B_theta_m
        B_r_i = B_r_array(i);
        B_theta_m_i = B_theta_m_array(i);
        
        % 현재 주파수에서의 손실 계산
        P_i = calcHybridACConductorLoss(conductorType, dimensions, sigma, mu_c, f_i, B_r_i, B_theta_m_i, l);
        
        % 주파수별 손실에 저장
        P_frequencies(i) = P_i;
        
        % 총 손실에 더함
        P_total = P_total + P_i;
    end
end


% $$$\gamma, \gamma_w, \gamma_h, \gamma_w^{\prime}, \gamma_h^{\prime}$ Dimensionless parameters:$$\gamma=\frac{d}{\delta \cdot \sqrt{2}} \quad \gamma_w=\frac{w}{\delta} \quad \gamma_h=\frac{h}{\delta} \quad \gamma_w^{\prime}=\frac{w}{\delta_w^{\prime}} \quad \gamma_h^{\prime}=\frac{w}{\delta_h^{\prime}}$$$$
% $$$\gamma_i, \gamma_{w, i}, \gamma_{h, i} \quad$ Dimensionless parameters 
% at $f_i$,$$
% 
% 
% $$$g_2\left(\gamma_w, \gamma_h\right)=\left[\frac{\gamma_w}{\sigma \cdot \mu^2} \cdot \frac{\sinh \left(\gamma_h\right)-\sin \left(\gamma_h\right)}{\cosh \left(\gamma_h\right)+\cos \left(\gamma_h\right)}\right]$$$
% $$$P_{\text {rect }}=g_{1,2}\left(\gamma_w, \gamma_h\right) l B_r^2+g_{1,2}\left(\gamma_h, \gamma_w\right) l B_{\theta_m}^2$$$
% 
% 
% Skin depth for frequency
% 
% $$$\delta=1 / \sqrt{\pi \mu_c \sigma f}$$$
% 
% $$\delta_w^{\prime}, \delta_h^{\prime}$$ Skin Depth for rectangular conductors
% 
% $$$\delta_w^{\prime}=\delta \cdot \sqrt{(w+h) /(2 h),} \quad \delta_h^{\prime}=\delta 
% \cdot \sqrt{(w+h) /(2 w)}$$$
% 
% 
% Stranded
% $P_{\alpha} = L_a \left( \frac{\pi d_c^4 \sigma (\omega B)^2}{128} \right) 
% $ 2019 volpe
% 
% 
% 
% 2*pi*f =omega???
% 
% 
% 
% 
% Rectangular
% 
% 
% $P_{ac} = \left( L_a\frac{ w_c h_c^3 \sigma (\omega B)^2}{24} \right) $  2019 
% volpe
% 
% ExpCalcHybridACLossModelwithSlotB
% 
% 
% 
% $$\mathrm{T}=\frac{\mathrm{V} \cdot \mathrm{s}}{\mathrm{m}^2}$$,$$\mathrm{T}=\frac{\mathrm{Wb}}{\mathrm{m}^2}$$