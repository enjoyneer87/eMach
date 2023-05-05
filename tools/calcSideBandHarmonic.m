%% eq 2.10
% Define variables
u_s = 50; % example value
Udc = 500; % example value
u_d = -25; % example value
u_q = 43; % example value

% Calculate modulation index and angle
M = 2*u_s/Udc;
delta = atan2(-u_d, u_q);

%%  3.2 sideband voltage harmonic model
% Define constants
a=0.9
M = 2*a/sqrt(3); % Modulation Index
xi = 3*sqrt(3)/(8*pi);
Udc = 500; % example value
omega_s = 2*pi*10000; % carrier frequency 
omega_e = 2*pi*50; % electrical frequency of modulation wave


% Calculate coefficients
C10 = (4/pi) * besselj(0, M*pi/2) * besselj(0, M*pi*xi/2);
C12 = (4/pi) * (besselj(2, M*pi/2)*besselj(0,M*pi*xi/2) - besselj(1,M*pi/2)*besselj(1,M*pi*xi/2));
C14 = (4/pi) * besselj(1,M*pi/2) * besselj(1,M*pi*xi/2);
C21 = -(2/pi) * (besselj(1,M*pi)*besselj(0,M*pi*xi) + besselj(2,M*pi)*besselj(1,M*pi*xi) - besselj(4,M*pi)*besselj(1,M*pi*xi));
C23 = -(2/pi) * (besselj(3,M*pi)*besselj(0,M*pi*xi) + besselj(0,M*pi)*besselj(1,M*pi*xi));
C25 = -(2/pi) * besselj(2,M*pi) * besselj(1,M*pi*xi);
C27 = -(2/pi) * besselj(4,M*pi) * besselj(1,M*pi*xi);

% Calculate signals
t = linspace(0,0.03, 100000); % example time vector
% fundamental term
a0 = 2*M*(sin(omega_e*t) + xi*sin(3*omega_e*t));
u_fund=(Udc/2) * (a0/2 );


% a1 = C10 + 2*C12*cos(2*omega_e*t) + 2*C14*cos(4*omega_e*t);
H1 = (Udc/2) * (C10*cos(omega_s*t) + C12*cos((omega_s+2*omega_e)*t) + C14*cos((omega_s+4*omega_e)*t));
% a2 = 2*C21*sin(omega_e*t) + 2*C23*sin(3*omega_e*t) + 2*C25*sin(5*omega_e*t) + 2*C27*sin(7*omega_e*t);

H2 = (Udc/2) * (C21 * sin((omega_e + 2*omega_s)*t) ...
                + C23 * sin((3*omega_e + 2*omega_s)*t) ...
                + C25 * sin((5*omega_e + 2*omega_s)*t) ...
                + C27 * sin((7*omega_e + 2*omega_s)*t));

u_a = (Udc/2) * (a0/2 )+H1+H2;

% Plot signals
figure;
plot(t, u_fund, 'LineWidth', 2);
hold on;
plot(t, H1, 'LineWidth', 2);
plot(t, H2, 'LineWidth', 2);
xlabel('Time');
ylabel('Voltage');
title('PWM Signal Components');
legend('Fundamental', 'Harmonic 1', 'Harmonic 2');
%% 3.2.2 

%  sideband current harmonic model




%% 3.5 
% Define constants
w_c = 2*pi*60; % Carrier frequency
w_e = 2*pi*120; % Extended carrier frequency
w_s = 2*pi*600; % Switching frequency
sigma_M = 0.1; % Modulation index
U_dc = 1000; % DC voltage


C_12 = 1; % Define C12
C_14 = 2; % Define C14
C_25 = 3; % Define C25
C_27 = 4; % Define C27
M_dq = 5; % Define M_dq
L_d = 6; % Define Ld
L_q = 7; % Define Lq
R_12 = 8; % Define R12
R_14 = 9; % Define R14
R_25 = 10; % Define R25
R_27 = 11; % Define R27
delta = pi/4; % Define delta

% Calculate Cm values
Cm_d13 = (M_dq^2*(C_12^2+C_14^2-2*C_12*C_14*cos(2*delta))-4*C_12*C_14*M_dq*L_q*sin(2*delta))/L_q^2;
Cm_q13 = (M_dq^2*(C_12^2+C_14^2+2*C_12*C_14*cos(2*delta))-4*C_12*C_14*M_dq*L_d*sin(2*delta))/L_d^2;
Cm_d26 = (M_dq^2*(C_25^2+C_27^2-2*C_25*C_27*cos(2*delta))-4*C_25*C_27*M_dq*L_q*sin(2*delta))/L_q^2;
Cm_q26 = (M_dq^2*(C_25^2+C_27^2+2*C_25*C_27*cos(2*delta))-4*C_25*C_27*M_dq*L_d*sin(2*delta))/L_d^2;

% Calculate phase angles
phi_d13 = atan(((C_12+C_14)*(M_dq*sin(delta)-L_q*cos(delta)))/sqrt(L_q^2*(C_12^2+C_14^2+2*C_12*C_14*cos(2*delta)+Cm_d13)));
phi_q13 = atan(((C_12-C_14)*(M_dq*cos(delta)+L_q*sin(delta)))/sqrt(L_q^2*(C_12^2+C_14^2+2*C_12*C_14*cos(2*delta)+Cm_q13)));
phi_d26 = atan(((C_25-C_27)*(L_q*sin(delta)+M_dq*cos(delta)))/sqrt(L_q^2*(C_25^2+C_27^2+2*C_25*C_27*cos(2*delta)+Cm_d26)));
phi_q26 = atan(((C_27-C_25)*(M_dq*sin(delta)+L_d*cos(delta)))/sqrt(L_d^2*(C_25^2+C_27^2-2*C_25*C_27*cos(2*delta)+Cm_q26)));

% Calculate Ud and Uq values
U_d13 = U_dc/2*sqrt(C_12^2+C_14^2+2*C_12*C_14*cos(2*delta)+Cm_d13);
U_q13 = U_dc/2*sqrt(C_12^


%
i_d_omega_mu = (L_q * u_d_omega_mu - M_dq * u_q_omega_mu) / (1j * omega_mu * (L_d * L_q - M_dq^2));
i_q_omega_mu = (L_d * u_q_omega_mu - M_dq * u_d_omega_mu) / (1j * omega_mu * (L_d * L_q - M_dq^2));


U_d_13 = U_dc/2 * sqrt(C_12^2 + C_14^2 + 2*C_12*C_14*cos(2*delta) + C_m_d_13);
U_q_13 = U_dc/2 * sqrt(C_12^2 + C_14^2 - 2*C_12*C_14*cos(2*delta) + C_m_q_13);
U_d_26 = U_dc/2 * sqrt(C_25^2 + C_27^2 + 2*C_25*C_27*cos(2*delta) + C_m_d_226);
U_q_26 = U_dc/2 * sqrt(C_25^2 + C_27^2 - 2*C_25*C_27*cos(2*delta) + C_m_q_226);

C_md_13 = (Mdq^2*(C_12^2 + C_14^2 - 2*C_12*C_14*cos(2*delta)) - 4*C_12*C_14*Mdq*Lq*sin(2*delta))/Lq^2;
C_mq_13 = (Mdq^2*(C_12^2 + C_14^2 + 2*C_12*C_14*cos(2*delta)) - 4*C_12*C_14*Mdq*Ld*sin(2*delta))/Ld^2;
C_md_26 = (Mdq^2*(C_25^2 + C_27^2 - 2*C_25*C_27*cos(2*delta)) - 4*C_25*C_27*Mdq*Lq*sin(2*delta))/Lq^2;
C_mq_26 = (Mdq^2*(C_25^2 + C_27^2 + 2*C_25*C_27*cos(2*delta)) - 4*C_25*C_27*Mdq*Ld*sin(2*delta))/Ld^2;

cos_phi_d_13 = ((C_12 + C_14)*(Mdq*sin(delta) - Lq*cos(delta)))/sqrt(Lq^2*(C_12^2 + C_14^2 + 2*C_12*C_14*cos(2*delta) + C_md_13));
sin_phi_d_13 = ((C_12 - C_14)*(Mdq*cos(delta) + Lq*sin(delta)))/sqrt(Lq^2*(C_12^2 + C_14^2 + 2*C_12*C_14*cos(2*delta) + C_md_13));
cos_phi_q_13 = ((C_12 - C_14)*(Mdq*sin(delta) + Ld*cos(delta)))/sqrt(Ld^2*(C_12^2 + C_14^2 - 2*C_12*C_14*cos(2*delta) + C_mq_13));
sin_phi_q_13 = ((C_12 + C_14)*(Mdq*cos(delta) - Ld*sin(delta)))/sqrt(Ld^2*(C_12^2 + C_14^2 - 2*C_12*C_14*cos(2*delta) + C_mq_13));
cos_phi_d_226 = ((C_25 - C_27)*(Lq*sin(delta) + Mdq*cos(delta)))/sqrt(Lq^2*(C_25^2 + C_27^2 + 2*C_25*C_27*cos(2*delta) + C_md_26));
sin_phi_d_22 = ((C_25 + C_27)*(Lq*cos(delta) - Mdq*sin(delta)))/sqrt(Lq^2*(C_25^2 + C_27^2 + 2*C_25*C_27*cos(2*delta) + C_md_26));
cos_phi_q_26 = ((C_27 + C_25)*(Mdq*cos(delta) - Ld*sin(delta)))/sqrt(Ld^2*(C_25^2 + C_27^2 - 2*C_25*C_27*cos(2*delta) + C_mq_26));
sin_phi_q_226 = ((C_27 - C_25)*(Mdq*sin(delta) + Ld*cos(delta)))/sqrt(Ld^2*(C_25^2


% 주어진 변수 값
sigma1 = 0.01;
sigma2 = 0.02;
sigmaM = 0.03;
M_dq = 0.04;
L_d = 0.05;
L_q = 0.06;
C_12 = 0.07;
C_14 = 0.08;
C_25 = 0.09;
C_27 = 0.10;
delta = 0.11;
U_dc = 100; % 예시 값, 사용자가 직접 정해야 함
omega_s = 200; % 예시 값, 사용자가 직접 정해야 함
omega_e = 50; % 예시 값, 사용자가 직접 정해야 함



% 수식 계산 (3.64) Sideband Current Harmonics in Stationary Frame
I_s_12 = (U_dc*sqrt(sigma1^2*C_12^2 + sigma2^2*C_14^2 + 2*sigma1*sigma2*C_12*C_14*cos(2*delta) + R_12))/(4*(omega_s + 3*omega_e)*(1-sigmaM^2));
I_s_14 = (U_dc*sqrt(sigma2^2*C_12^2 + sigma1^2*C_14^2 + 2*sigma1*sigma2*C_12*C_14*cos(2*delta) + R_14))/(4*(omega_s + 3*omega_e)*(1-sigmaM^2));


Is21 = -Udc*C21/(4*ws*(1-sigmaM^2)*sqrt((sin(delta)/Ld)^2 + (cos(delta)/Lq)^2 + R21));
Is25 = Udc*sqrt(sigma1^2*C25^2 + sigma2^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta) + R25)...
       /(4*(2*ws + 6*wc)*(1-sigmaM^2));
Is27 = Udc*sqrt(sigma2^2*C25^2 + sigma1^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta) + R27)...
       /(4*(2*ws + 6*wc)*(1-sigmaM^2));



%  coefficient (3.67)
R12 = 4*sigma_M^2*C14^2/(Ld*Lq) - (4*sigma_1*Mdq*C12*C14/(Ld*Lq))*sin(2*delta);
R14 = 4*sigma_M^2*C12^2/(Ld*Lq) - (4*sigma_1*Mdq*C12*C14/(Ld*Lq))*sin(2*delta);
R21 = sigma_M^2/(Ld*Lq) + ((1/Ld)+(1/Lq))*(Mdq/(Ld*Lq))*sin(2*delta);
R25 = 4*sigma_M^2*C27^2/(Ld*Lq) - (4*sigma_1*Mdq*C25*C27/(Ld*Lq))*sin(2*delta);
R27 = 4*sigma_M^2*C25^2/(Ld*Lq) - (4*sigma_1*Mdq*C25*C27/(Ld*Lq))*sin(2*delta);



