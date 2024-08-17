%| Application factor, $K_A$ | 1.0 |
%| :--- | :--- |
%| Mesh load factor, $K_\gamma$ | 1.0 |
%| Internal dynamic factor, $K_V$ | - |
%| Face load factors, $K_{H \beta / F \beta}$ | - |
%| Transverse load factors, | - |
%| $K_{H \alpha / F \alpha}$ |  |
K_A = 1.0       % Application factor, $K_A$ | 1.0
K_gamma = 1.0   % Mesh load factor, $K_\gamma$ | 1.0

% Contact factor, $K_{\delta}$ | 1.0 

%\begin{tabular}{lc} 
%Contact factor (pinion), $Z_B$ & 1.0 \\
%Contact factor (wheel), $Z_D$ & 1.0 \\
%& \\
%Zone factor, $Z_H$ & - \\
%Elasticity factor, $Z_E$ & - \\
%Contact ratio factor, $Z_{\varepsilon}$ & - \\
%Helix angle factor, $Z_\beta$ & - \\
%& \\
%Life factor (reference), $Z_{N T}$ & 1.6 \\
%& \\
%Lubricant factor, $Z_L$ & - \\
%Velocity factor, $Z_V$ & - \\
%Roughness factor, $Z_R$ & - \\
%Work hardening factor, $Z_W$ & - \\
%Size factor (pitting), $Z_X$ & 2.0
%\end{tabular}

Z_B = 1.0    % Contact factor (pinion), $Z_B$ & 1.0
Z_D = 1.0   % Contact factor (wheel), $Z_D$ & 1.0
Z_NT = 1.6   % Life factor (reference), $Z_{N T}$ & 1.6
Z_H = 1     % Zone factor, $Z_H$ & -
Z_E = 1
Zepsilon = 1
beta= 20 % Helix angle, $\beta$ & 20
Z_beta= cos(beta) % Helix angle factor, $Z_\beta$ & -

% Bearing factors
%\begin{tabular}{lc}
%\hline Form factor, $Y_F$ & - \\
%Stress correction factor, $Y_S$ & - \\
%Helix angle factor, $Y_\beta$ & - \\
%Rim thickness factor, $Y_B$ & 1.0 \\
%& \\
%Deep tooth factor, $Y_{D T}$ & 1.0 \\
%& \\
%Stress correction of test gears, & 2.0 \\
%$Y_{S T}$
%\end{tabular}

Y_B = 1.0   % Rim thickness factor, $Y_B$ & 1.0
Y_DT = 1.0 % Deep tooth factor, $Y_{D T}$ & 1.0
Y_ST = 2.0 % Stress correction of test gears, $Y_{S T}$ & 2.0

%\begin{tabular}{ll}
%\hline Life factor, $Y_{N T}$ & 2.5 \\
%Relative notch sensitivity fac- & 1.0 \\
%tor, $Y_\delta$ rel $T$ \\
%Relative surface factor, & \\
%$Y_R$ rel $T$ \\
%Size factor, $Y_X$ & \\
%\end{tabular}

Y_NT = 2.5 % Life factor, $Y_{N T}$ & 2.5
Ydelta_relT= 1.0 % Relative notch sensitivity factor, $Y_\delta$ rel $T$ & 1.0
YR_relT = 1.0 % Relative surface factor, $Y_R$ rel $T$ & 1.0
Yx= 1.0 % Size factor, $Y_X$ & 1.0
