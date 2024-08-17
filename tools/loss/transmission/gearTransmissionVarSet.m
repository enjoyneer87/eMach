
%\begin{tabular}{lcl}
%\hline Variable parameters & Symbol & Selected values \\
%\hline Normal module & $m_n$ & $0.5,0.55 \ldots 3.0$ \\
%Number of teeth (pinion) & $z_p$ & $z_{\min }, z_{\min }+1 \ldots$ \\
%& & $z_{\max } / U^*$ \\
%Face width coefficient & $b_0$ & $10,11 \ldots 20$ \\
%Helix angle & $\beta$ & $10,11 \ldots 30$ \\
%Pressure angle & $\alpha_n$ & $15,16 \ldots 25$ \\
%Profile shift coefficient (pinion) & $x_{0, p}$ & $-0.7,-0.6 \ldots 0.7$ \\
%Profile shift coefficient (wheel) & $x_{0, w}$ & $-0.7,-0.6 \ldots 0.7$ \\
%\hline Constant parameters & & \\
%\hline Addendum coefficient & $h_{a P}$ & 1.00 \\
%Dedendum coefficient & $h_{f P}$ & 1.25 \\
%Root radius coefficient & $\rho_{f P}$ & 0.35
%\end{tabular}

m_n=0.5;  % Normal module
z_p=12;  % Number of teeth (pinion)
b_0=10;  % Face width coefficient
beta=20;  % Helix angle
alpha_n=20;  % Pressure angle
x_0_p=0;  % Profile shift coefficient (pinion)
x_0_w=0;  % Profile shift coefficient (wheel)

h_ap=1.00;  % Addendum coefficient
h_fp=1.25;  % Dedendum coefficient
rho_fp=0.35;  % Root radius coefficient

% Calculate the basic rack parameters
m_t=m_n/cosd(beta);  % Transverse module
m_r=m_n*sind(beta);  % Normal module
alpha_t=atand(tand(alpha_n)/cosd(beta));  % Transverse pressure angle
alpha_r=atand(tand(alpha_n)*cosd(beta));  % Normal pressure angle
h_at=h_ap*cosd(alpha_t);  % Transverse addendum coefficient
h_ft=h_fp*cosd(alpha_t);  % Transverse dedendum coefficient
rho_ft=rho_fp*m_t;  % Transverse root radius coefficient
    


