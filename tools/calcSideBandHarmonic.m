

%% expand struct variable 2 function variable
i=1
j=20
row=i
col=j
%% example value
id=HDEVdata.current_dq_map.id(row,col);
iq=HDEVdata.current_dq_map.iq(row,col);
phi_d=mean(HDEVdata.flux_linkage_map.in_d(i,j,:))
phi_q=mean(HDEVdata.flux_linkage_map.in_q(i,j,:))

Ld=phi_d/id;
Lq=phi_q/iq;

PmsmFem.NumPolePairs = HDEVdata.p/2;
rpm=freq2rpm(f_e,HDEVdata.p);


%% code

% Define variables
Udc = 150; % example value
dc_voltage = Udc; % example value
% freq (Hz, 1/s)
    freq_e=170; % exmaple value
    % freq_e=input_obj.ShaftSpeed/60*(input_obj.p/2); 
    % One_mech_Endtime=1/freq_mech;
    % One_elec_Endtime=1/freq_e;
    f_e=freq_e;
    freq_carrier=10000;
    freq_s=freq_carrier;
    freq_mech=rpm/60;

%  omega (rad/s)

% omega_mech=freq_mech*2*pi;
% omegaE=freq_e*2*pi;
    omega_e = freq2omega(freq_e) % electrical frequency of modulation wave
    omega_s = freq2omega(f_s); % carrier frequency 
    w_e = omega_e; % electrical frequency of modulation wave
    w_s = omega_s; % carrier frequency 
    W_r=2*pi*170; % rotational rad/s?
    Rs=HDEVdata.Rs;


%% Thesis eq
u_s = 50; % eq 2.6
u_s = sqrt((Rs*id - w_e*phi_q)^2 + (Rs*iq + w_e*phi_d)^2);

u_d = Rs*id - w_e*phi_q; % example value
u_q = Rs*iq + w_e*phi_d; % example value

% Calculate modulation index and angle
xi = 3*sqrt(3)/(8*pi);         %eq 3.8 
a=0.9; %example
sigma_M = 0.1; % Modulation index
M = 2*a/sqrt(3); % Modulation Index eq 3.8
M = 2*u_s/Udc;       % eq 2.10

delta = atan2(-u_d, u_q); % eq 2.10 torque angle
delta = atan(-u_d/u_q); %eq 2.10 torque angle

% eq 3.17
% w_s
% Define constants


%% 3.1  

%%  3.2 sideband voltage harmonic model

% Define constants

% Calculate coefficients eq 3.12 p.62
C10 = (4/pi) * besselj(0, M*pi/2) * besselj(0, M*pi*xi/2);
C12 = (4/pi) * (besselj(2, M*pi/2)*besselj(0,M*pi*xi/2) - besselj(1,M*pi/2)*besselj(1,M*pi*xi/2));
C14 = (4/pi) * besselj(1,M*pi/2) * besselj(1,M*pi*xi/2);

C21 = -(2/pi) * (besselj(1,M*pi)*besselj(0,M*pi*xi) + besselj(2,M*pi)*besselj(1,M*pi*xi) - besselj(4,M*pi)*besselj(1,M*pi*xi));
C23 = -(2/pi) * (besselj(3,M*pi)*besselj(0,M*pi*xi) + besselj(0,M*pi)*besselj(1,M*pi*xi));
C25 = -(2/pi) * besselj(2,M*pi) * besselj(1,M*pi*xi);
C27 = -(2/pi) * besselj(4,M*pi) * besselj(1,M*pi*xi);


% Calculate signals
% t = linspace(0, 1, 100000); % example time vector
t = linspace(0,0.03, 100000); % example time vector

% Basic wave
a0 = 2*M*(sin(omega_e*t) + xi*sin(3*omega_e*t));
ua_basic = (dc_voltage/2) * a0/2;

% H1
H1_plus = (dc_voltage/2) * C12 * cos((omega_s + 3*omega_e)*t - delta);
H1_minus = (dc_voltage/2) * C12 * cos((omega_s - 3*omega_e)*t + delta);

% H2
H2_plus = (dc_voltage/2) * C21 * sin((omega_e + 2*omega_s)*t - delta) ...
                + C23 * sin((3*omega_e + 2*omega_s)*t - delta) ...
                + C25 * sin((5*omega_e + 2*omega_s)*t - delta) ...
                + C27 * sin((7*omega_e + 2*omega_s)*t - delta);
H2_minus = (dc_voltage/2) * C21 * sin((omega_e + 2*omega_s)*t + delta) ...
                + C23 * sin((3*omega_e + 2*omega_s)*t + delta) ...
                + C25 * sin((5*omega_e + 2*omega_s)*t + delta) ...
                + C27 * sin((7*omega_e + 2*omega_s)*t + delta);

% Combined signal
u_a = (Udc/2) * (a0/2)+H1_plus+H2_plus+H1_minus+H2_minus;

% Plot signals
figure
plot(t, ua_basic, 'DisplayName', 'Basic Wave')
hold on
plot(t, H1_plus, 'DisplayName', 'H1 (+)')
plot(t, H1_minus, 'DisplayName', 'H1 (-)')
plot(t, H2_plus, 'DisplayName', 'H2 (+)')
plot(t, H2_minus, 'DisplayName', 'H2 (-)')
plot(t, u_a, 'DisplayName', 'Combined (-)','Color','r')
xlabel('Time')
ylabel('Voltage')
legend('Location', 'best')



%% 3.2.2 sideban voltage harmonic in syncrhonous frame


% Calculate sideband voltages
% w_s +-2w_e, 4w_e-order voltage harmonics 
% eq 3.17
u12d_plus = -(Udc/2)*C12*cos((omega_s+3*omega_e)*t-delta);
u12d_minus = -(Udc/2)*C12*cos((omega_s-3*omega_e)*t+delta);
u14d_plus = -(Udc/2)*C14*cos((omega_s+3*omega_e)*t+delta);
u14d_minus = -(Udc/2)*C14*cos((omega_s-3*omega_e)*t-delta);
% eq 3.18
u12q_plus = (Udc/2)*C12*sin((omega_s+3*omega_e)*t-delta);
u12q_minus = -(Udc/2)*C12*sin((omega_s-3*omega_e)*t+delta);
u14q_plus = -(Udc/2)*C14*sin((omega_s+3*omega_e)*t+delta);
u14q_minus = (Udc/2)*C14*sin((omega_s-3*omega_e)*t-delta);

% (omega_s +-3omega_e)-order voltage harmonics 
% eq 3.20 w_s+-3w_e
Ud_13 = Udc/2 * sqrt(C12^2 + C14^2 + 2*C12*C14*cos(2*delta));
Uq_13 = Udc/2 * sqrt(C12^2 + C14^2 - 2*C12*C14*cos(2*delta));

% eq 3.21
phi_d_13 = pi + atan(((C14-C12)*tan(delta))/ (C14+C12));
phi_q_13 = atan(((C14+C12)*tan(delta))/ (C14-C12));

% eq. 3.19
ud_ws3we_pos = Ud_13 * cos((omega_s + 3*omega_e)*t + phi_d_13);
ud_ws3we_neg = Ud_13 * cos((omega_s - 3*omega_e)*t - phi_d_13);

uq_ws3we_pos = Uq_13 * sin((omega_s + 3*omega_e)*t + phi_q_13);
uq_ws3we_neg = -Uq_13 * sin((omega_s - 3*omega_e)*t -phi_q_13);

% (2omega_s 2omegas+-6omega_e)-order voltage harmonics 

%2omega_s 
% eq 3.22
ud_2ws = -(Udc)*C21*sin(delta)*cos(2*omega_s*t);
uq_2ws = (Udc)*C21*cos(delta)*cos(2*omega_s*t);

%2omegas+-6omega_e
% eq 3.24
Ud_26 = Udc/2 * sqrt(C25^2 + C27^2 + 2*C25*C25*cos(2*delta));
Uq_26 = Udc/2 * sqrt(C25^2 + C27^2 - 2*C25*C25*cos(2*delta));

% eq 3.25
phi_d_26 = pi + atan(((C25+C27)*cot(delta))/ (C25-C27));
phi_q_26 = atan(((C25-C27)*cot(delta))/ (C25+C27));
% eq 3.23

Ud_2wsPos6we = Ud_26*cos((2*w_s+6*w_e)*t+phi_d_26);
Ud_2wsNeg6we = Ud_26*cos((2*w_s-6*w_e)*t-phi_d_26);

Uq_2wsPos6we = Uq_26*sin((2*w_s+6*w_e)*t+phi_q_26);
Uq_2wsNeg6we = -Uq_26*sin((2*w_s-6*w_e)*t-phi_q_26);


%% 3.3 Analytical Sideband Current Harmonic Modeling
%3.3.1 sideband in synchronous frame

% in stationary Frame

% Define frequency vector for mu-order harmonics
omega_mu = 1+omega_e;

% Calculate mu-order harmonic voltages
% eq. 3.9
id_w_mu=id;
iq_w_mu=iq;
ud_mu = Rs*id_w_mu + 1j*omega_mu*Ld*id_w_mu - omega_e*Lq*iq_w_mu;
uq_mu = Rs*iq_w_mu + 1j*omega_mu*Lq*iq_w_mu + omega_e*Ld*id_w_mu;


%% 3.5 

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
Ud_13 = Udc/2*sqrt(C_12^2+C_14^2+2*C_12*C_14*cos(2*delta)+Cm_d13);
U_q13 = Udc/2*sqrt(C_12^


%
i_d_omega_mu = (L_q * u_d_omega_mu - M_dq * u_q_omega_mu) / (1j * omega_mu * (L_d * L_q - M_dq^2));
i_q_omega_mu = (L_d * u_q_omega_mu - M_dq * u_d_omega_mu) / (1j * omega_mu * (L_d * L_q - M_dq^2));


U_d_13 = Udc/2 * sqrt(C_12^2 + C_14^2 + 2*C_12*C_14*cos(2*delta) + C_m_d_13);
U_q_13 = Udc/2 * sqrt(C_12^2 + C_14^2 - 2*C_12*C_14*cos(2*delta) + C_m_q_13);
U_d_26 = Udc/2 * sqrt(C_25^2 + C_27^2 + 2*C_25*C_27*cos(2*delta) + C_m_d_226);
U_q_26 = Udc/2 * sqrt(C_25^2 + C_27^2 - 2*C_25*C_27*cos(2*delta) + C_m_q_226);

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



% 수식 계산 (3.64) Sideband Current Harmonics in Stationary Frame
I_s_12 = (Udc*sqrt(sigma1^2*C_12^2 + sigma2^2*C_14^2 + 2*sigma1*sigma2*C_12*C_14*cos(2*delta) + R_12))/(4*(w_s + 3*w_e)*(1-sigmaM^2));
I_s_14 = (Udc*sqrt(sigma2^2*C_12^2 + sigma1^2*C_14^2 + 2*sigma1*sigma2*C_12*C_14*cos(2*delta) + R_14))/(4*(w_s + 3*w_e)*(1-sigmaM^2));


Is21 = -Udc*C21/(4*w_s*(1-sigmaM^2)*sqrt((sin(delta)/Ld)^2 + (cos(delta)/Lq)^2 + R21));
Is25 = Udc*sqrt(sigma1^2*C25^2 + sigma2^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta) + R25)...
       /(4*(2*w_s + 6*wc)*(1-sigmaM^2));
Is27 = Udc*sqrt(sigma2^2*C25^2 + sigma1^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta) + R27)...
       /(4*(2*w_s + 6*wc)*(1-sigmaM^2));



%  coefficient (3.67)
R12 = 4*sigma_M^2*C14^2/(Ld*Lq) - (4*sigma_1*Mdq*C12*C14/(Ld*Lq))*sin(2*delta);
R14 = 4*sigma_M^2*C12^2/(Ld*Lq) - (4*sigma_1*Mdq*C12*C14/(Ld*Lq))*sin(2*delta);
R21 = sigma_M^2/(Ld*Lq) + ((1/Ld)+(1/Lq))*(Mdq/(Ld*Lq))*sin(2*delta);
R25 = 4*sigma_M^2*C27^2/(Ld*Lq) - (4*sigma_1*Mdq*C25*C27/(Ld*Lq))*sin(2*delta);
R27 = 4*sigma_M^2*C25^2/(Ld*Lq) - (4*sigma_1*Mdq*C25*C27/(Ld*Lq))*sin(2*delta);



