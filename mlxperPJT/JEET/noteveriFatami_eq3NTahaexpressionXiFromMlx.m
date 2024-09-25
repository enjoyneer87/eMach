%% 
% $$$\gamma, \gamma_w, \gamma_h, \gamma_w^{\prime}, \gamma_h^{\prime}$ Dimensionless 
% parameters:$$\gamma=\frac{d}{\delta \cdot \sqrt{2}} \quad \gamma_w=\frac{w}{\delta} 
% \quad \gamma_h=\frac{h}{\delta} \quad \gamma_w^{\prime}=\frac{w}{\delta_w^{\prime}} 
% \quad \gamma_h^{\prime}=\frac{w}{\delta_h^{\prime}}$$$$
% 
% $$$$\delta=\sqrt{\frac{2 p}{\omega \mu_0}}$$$$
% 
% 

;
syms coeff pi sigma mu_c gamma hc bc b
coeffi = latex((1 /(8 * pi * sigma * mu_c^2)) * gamma.^4)
text(1.1,0.5,chr,'Interpreter','latex')


coeffiXi= latex(hc*sqrt(0.5*2*pi*mu_c*sigma*bc/b));

%% 
% $coeffi ='\frac{\gamma ^4}{8\,{\mu _{c}}^2\,\pi \,\sigma }'$= 이거 어디서? 
% 
% $$'\mathrm{h_c}\,\sqrt{\frac{\mathrm{b_c}\,\mu _{c}\,\pi \,\sigma }{b}}'$$
% 
%