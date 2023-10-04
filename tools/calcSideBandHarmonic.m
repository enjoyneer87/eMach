%% expand struct variable 2 function variable

i=1
j=20
row=i
col=j
%% example value

test_data_dq_map_motorcad;
id=HDEVdata.current_dq_map.id(row,col);
iq=HDEVdata.current_dq_map.iq(row,col);
phi_d=mean(HDEVdata.flux_linkage_map.in_d(i,j,:))
phi_q=mean(HDEVdata.flux_linkage_map.in_q(i,j,:))

Ld=phi_d/id;
Lq=phi_q/iq;

PmsmFem.NumPolePairs = HDEVdata.p/2;
%% code
% 주석 )코드에서 $\omega_x$는 w_x 형태로 표기합니다.
% 
% reference 순서대로 코드를 작성하고 역순으로 실행되어야하는부분은 함수화를 통해 해결한다.

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
    rpm=freqE2rpm(f_e,HDEVdata.p);

%  omega (rad/s)
% omega_mech=freq_mech*2*pi;
% omegaE=freq_e*2*pi;
    w_e = freq2omega(freq_e) % electrical frequency of modulation wave
    w_s = freq2omega(freq_s); % carrier frequency 
    w_mu =0 ; % 임의의 차수
    w_e = w_e; % electrical frequency of modulation wave
    w_s = w_s; % carrier frequency 
    w_r=2*pi*170; % rotational rad/s?
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
% 3.1
% 3.2 Sideband Voltage Harmonic Model

% Define constants

% 3.2.1 Sideband Voltage Harmonics in Stationary Frame



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
a0 = 2*M*(sin(w_e*t) + xi*sin(3*w_e*t));
ua_basic = (dc_voltage/2) * a0/2;

% H1
H1_plus = (dc_voltage/2) * C12 * cos((w_s + 3*w_e)*t - delta);
H1_minus = (dc_voltage/2) * C12 * cos((w_s - 3*w_e)*t + delta);

% H2
H2_plus = (dc_voltage/2) * C21 * sin((w_e + 2*w_s)*t - delta) ...
                + C23 * sin((3*w_e + 2*w_s)*t - delta) ...
                + C25 * sin((5*w_e + 2*w_s)*t - delta) ...
                + C27 * sin((7*w_e + 2*w_s)*t - delta);
H2_minus = (dc_voltage/2) * C21 * sin((w_e + 2*w_s)*t + delta) ...
                + C23 * sin((3*w_e + 2*w_s)*t + delta) ...
                + C25 * sin((5*w_e + 2*w_s)*t + delta) ...
                + C27 * sin((7*w_e + 2*w_s)*t + delta);

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
% 3.2.2 sideban voltage harmonic in syncrhonous frame

% Calculate sideband voltages
% w_s +-2w_e, 4w_e-order voltage harmonics 
% eq 3.17
u12d_plus = -(Udc/2)*C12*cos((w_s+3*w_e)*t-delta);
u12d_minus = -(Udc/2)*C12*cos((w_s-3*w_e)*t+delta);
u14d_plus = -(Udc/2)*C14*cos((w_s+3*w_e)*t+delta);
u14d_minus = -(Udc/2)*C14*cos((w_s-3*w_e)*t-delta);
% eq 3.18
u12q_plus = (Udc/2)*C12*sin((w_s+3*w_e)*t-delta);
u12q_minus = -(Udc/2)*C12*sin((w_s-3*w_e)*t+delta);
u14q_plus = -(Udc/2)*C14*sin((w_s+3*w_e)*t+delta);
u14q_minus = (Udc/2)*C14*sin((w_s-3*w_e)*t-delta);

% (w_s +-3w_e)-order voltage harmonics 
% eq 3.20 w_s+-3w_e
Ud_13 = Udc/2 * sqrt(C12^2 + C14^2 + 2*C12*C14*cos(2*delta));
Uq_13 = Udc/2 * sqrt(C12^2 + C14^2 - 2*C12*C14*cos(2*delta));

% eq 3.21
phi_d_13 = pi + atan(((C14-C12)*tan(delta))/ (C14+C12));
phi_q_13 = atan(((C14+C12)*tan(delta))/ (C14-C12));

% eq. 3.19
ud_ws3we_pos = Ud_13 * cos((w_s + 3*w_e)*t + phi_d_13);
ud_ws3we_neg = Ud_13 * cos((w_s - 3*w_e)*t - phi_d_13);

uq_ws3we_pos = Uq_13 * sin((w_s + 3*w_e)*t + phi_q_13);
uq_ws3we_neg = -Uq_13 * sin((w_s - 3*w_e)*t -phi_q_13);

% (2w_s 2omegas+-6w_e)-order voltage harmonics 

%2w_s 
% eq 3.22
ud_2ws = -(Udc)*C21*sin(delta)*cos(2*w_s*t);
uq_2ws = (Udc)*C21*cos(delta)*cos(2*w_s*t);

%2omegas+-6w_e
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

% no figure use in 3.3

% 3.3 Analytical Sideband Current Harmonic Modeling
% 3.3.1 sideband in synchronous frame
% 주요 sideband current 고조파는 해당 PMSM의 전압 고조파로부터 직접적으로 유도할수 있다. 
% 
% $w_{mu}$ 차수 전압과 dq 전류 고조파의 해석적(analytic)상관관계는 dq 전압 방정식  eq 2.1로부터 쉽게 얻을수 
% 있다.
% 
% $$\left\{\begin{array}{l}u_d=R_s i_d+L_d \frac{\mathrm{d} i_d}{\mathrm{~d} 
% t}-\omega_e \psi_q \\ u_q=R_s i_q+L_q \frac{\mathrm{d} i_q}{\mathrm{~d} t}+\omega_e 
% \psi_d\end{array}\right.$$  (2.1)
% 
% 최종 모델은 다음과 같이 표현할수 있다. 
% 
% $$\left\{\begin{array}{l}u_{d \_\omega_\mu}=R_s i_{d \_\omega_\mu}+j \omega_\mu 
% L_d i_{d \_\omega_\mu}-\omega_e L_q i_{q \_\omega_\mu} \\ u_{q \_\omega_\mu}=R_s 
% i_{q \_\omega_\mu}+j \omega_\mu L_q i_{q \_\omega_\mu}+\omega_e L_d i_{d \_\omega_\mu}\end{array}\right.$$   
% (3.26)

% eq 3.26
% Define frequency vector for mu-order harmonics (mu는 임의의 차수를 나타냄)
w_mu = w_mu;
% Calculate mu-order harmonic voltages
% eq. 3.9
% ud_w_mu = Rs*id_w_mu + 1j*w_mu*Ld*id_w_mu - w_e*Lq*iq_w_mu;
% uq_w_mu= Rs*iq_w_mu + 1j*w_mu*Lq*iq_w_mu + w_e*Ld*id_w_mu;
%% 
% sideband 전류 고조파 주파수는 $w_{mu}$는 일반적으로 전기주파수 $w_{e}$ 보다 적어도 1개이상의 자리수가 높기 때문에 
% sideband 고조파 리액턴스는 권선의 d축 저항보다 훨씬 크다. 
% 
% 따라서 식 3.26 우항의 저항에 의한 전압강하성분은 정확도에 영향을 주지 않아 무시될수 있다. 
% 
% 또한 회전에의한 EMF 성분  또한 무시될 수 있다. ( 고속에서도 그럴까?) 
% 
% 때문에 sideband  전압 고조파는 거의 Induction EMF에 해당된다고 볼수 있다. 그결과 아래 식과 같이 정상상태에서 sideband 
% 전류 고조파 성분은 정의된다. 
% 
% $$i_{d \_\omega_\mu}=\frac{u_{d \_\omega_\mu}}{j \omega_\mu L_d}, \quad i_{q\_\omega_\mu}=\frac{u_{q 
% \_\omega_\mu}}{j \omega_\mu L_q}$$ (3.27)
% 
% $$\left\{\begin{array}{l}i_{d_{(\omega_s\pm3\omega_e)}}=\frac{U_{d_{13}} \sin 
% \left(\left(\omega_s \pm 3 \omega_e\right) t \pm \varphi_{d_{{13}}}\right)}{\left(\omega_s 
% \pm 3 \omega_e\right) L_d} \\ i_{q_{(\omega_s \pm 3 \omega_e)}}=\frac{\mp U_{q_{13}} 
% \cos \left(\left(\omega_s \pm 3 \omega_e\right) t \pm \varphi_{q_{13}}\right)}{\left(\omega_s 
% \pm 3 \omega_e\right) L_q}\end{array}\right.$$  (3.28)
% 
% 
% 
% $$\left\{\begin{array}{l}i_{d_{-}\left(2 \omega_s\right)}=\frac{-U_{d c} C_{21} 
% \sin \delta \sin \left(2 \omega_s t\right)}{2 \omega_s L_d} \\ i_{q_{-}\left(2 
% \omega_s\right)}=\frac{U_{d c} C_{21} \cos \delta \sin \left(2 \omega_s t\right)}{2 
% \omega_s L_q}\end{array}\right.$$ (3.29)
% 
% 
% 
% $$\left\{\begin{array}{l}i_{d_{(2 \omega_s \pm 6\omega_e)}}=\frac{U_{d_{26}} 
% \sin \left(\left(2 \omega_s \pm 6 \omega_e\right) t \pm \varphi_{d_{-26}}\right)}{\left(2 
% \omega_s \pm 6 \omega_e\right) L_d} \\ i_{q_{(2 \omega_s \pm 6 \omega_e)}}=\frac{\mp 
% U_{q_{26}} \cos \left(\left(2 \omega_s \pm 6 \omega_e\right) t \pm \varphi_{q-26}\right)}{\left(2 
% \omega_s \pm 6 \omega_e\right) L_q}\end{array}\right.$$ (3.30)

% eq 3.27
% id_w_mu = ud_w_mu ./ (1j * w_mu * Ld);
% iq_w_mu = uq_w_mu ./ (1j * w_mu * Lq);

%eq 3.28
id_wsPos3we = (Ud_13*sin((w_s+3*w_e)*t+phi_d_13))/((w_s+3*w_e)*Ld);
id_wsNeg3we = (Ud_13*sin((w_s-3*w_e)*t-phi_d_13))/((w_s-3*w_e)*Ld);

iq_wsPos3we = -(Uq_13*cos((w_s+3*w_e)*t+phi_q_13))/((w_s+3*w_e)*Lq);
iq_wsNeg3we = -(Uq_13*cos((w_s-3*w_e)*t-phi_q_13))/((w_s-3*w_e)*Lq);

%eq 3.29
id_2ws = -(Udc*C21*sin(delta)*sin(2*w_s*t))/(2*w_s*Ld);
id_2ws = (Udc*C21*cos(delta)*sin(2*w_s*t))/(2*w_s*Lq);

%eq 3.30
id_2wsPos6we = Ud_26 * sin((2*w_s + 6*w_e)*t + phi_d_26) / ((2*w_s + 6*w_e)*Ld);
id_2wsNeg6we = Ud_26 * sin((2*w_s - 6*w_e)*t - phi_d_26) / ((2*w_s - 6*w_e)*Ld);

iq_2wsPos6we = -Uq_26 * cos((2*w_s + 6*w_e)*t + phi_q_26) / ((2*w_s + 6*w_e)*Lq);
iq_2wsNeg6we = Uq_26 * cos((2*w_s - 6*w_e)*t - phi_q_26) / ((2*w_s - 6*w_e)*Lq);

% Summation of main sideband current harmonic 
id_sb_sync = id_wsPos3we + id_wsNeg3we + id_2ws + id_2wsPos6we + id_2wsNeg6we;
iq_sb_sync = iq_wsPos3we + iq_wsNeg3we + iq_2wsPos6we + iq_2wsNeg6we;
id_sync=id+id_sb_sync;
iq_sync=iq+id_sb_sync;


% 3.3.2 Sideband Current harmonics in Stationary Frame
% 
% 
% 회전자 동기 프레임에서 sideband 전류고조파는 역변환(Inverse Park transformation)에 의해서 고정자 고정좌표계 
% 프레임으로 변환된다.
% 
% 회전자 동기프레임에서 $\omega_{s} \pm 3\omega_{e}$차수 전류 고조파는 고정자 프레임에서 $\omega_s \pm 
% 2\omega_e$ 차와 $\omega_s \pm 4\omega_e$차수로 변환된다.
% 
% 해당 상전류 고조파는 다음과 같다.
% 
% $$\left\{\begin{array}{l}i_{s_{-}\left(\omega_s \pm 2 \omega_e\right)}= \pm 
% I_{s_{-} 12} \cos \left(\left(\omega_s \pm 2 \omega_e\right) t \mp \varphi_{s_{-} 
% 12}\right) \\ i_{s_{-}\left(\omega_s \pm 4 \omega_e\right)}= \pm I_{s_{-} 14} 
% \cos \left(\left(\omega_s \pm 4 \omega_e\right) t \pm \varphi_{s_{-} 14}\right)\end{array}\right.$$ 
% (3.31)
% 
% 
% 
% $$\left\{\begin{array}{l}I_{s_{-} 12}=\frac{U_{d c} \sqrt{\sigma_1^2 C_{12}^2+\sigma_2^2 
% C_{14}^2+2 \sigma_1 \sigma_2 C_{12} C_{14} \cos (2 \delta)}}{4\left(\omega_s 
% \pm 3 \omega_e\right)} \\ I_{s_{-} 14}=\frac{U_{d c} \sqrt{\sigma_2^2 C_{12}^2+\sigma_1^2 
% C_{14}^2+2 \sigma_1 \sigma_2 C_{12} C_{14} \cos (2 \delta)}}{4\left(\omega_s 
% \pm 3 \omega_e\right)}\end{array}\right.$$ (3.32)
% 
% 
% 
% $$\left\{\begin{array}{l}\cos \varphi_{s_{-} 12}=\frac{\left(\sigma_1 C_{12}-\sigma_2 
% C_{14}\right) \sin \delta}{\sqrt{\sigma_1^2 C_{12}^2+\sigma_2^2 C_{14}^2+2 \sigma_1 
% \sigma_2 C_{12} C_{14} \cos (2 \delta)}} \\ \sin \varphi_{s_{-12}}=\frac{-\left(\sigma_1 
% C_{12}+\sigma_2 C_{14}\right) \cos \delta}{\sqrt{\sigma_1^2 C_{12}^2+\sigma_2^2 
% C_{14}^2+2 \sigma_1 \sigma_2 C_{12} C_{14} \cos (2 \delta)}} \\ \cos \varphi_{s_{-} 
% 14}=\frac{\left(\sigma_2 C_{12}-\sigma_1 C_{14}\right) \sin \delta}{\sqrt{\sigma_2^2 
% C_{12}^2+\sigma_1^2 C_{14}^2+2 \sigma_1 \sigma_2 C_{12} C_{14} \cos (2 \delta)}} 
% \\ \sin \varphi_{s_{-14}}=\frac{\left(\sigma_2 C_{12}+\sigma_1 C_{14}\right) 
% \cos \delta}{\sqrt{\sigma_2^2 C_{12}^2+\sigma_1^2 C_{14}^2+2 \sigma_1 \sigma_2 
% C_{12} C_{14} \cos (2 \delta)}}\end{array}\right.$$ (3.33)
% 
% 
% 
% $$\sigma_1=\frac{1}{L_d}+\frac{1}{L_q}, \quad \sigma_2=\frac{1}{L_d}-\frac{1}{L_q}$$  
% (3.34)
% 
% 
% 
% 식 3.32를 아래 식과같이 검토하면, $\omega_s \pm 2\omega_e$ 와 $\omega_s \pm 4\omega_e$의 
% 관계는 다음과 같다
% 
% $$I_{s_{-} 12}^2-I_{s_{-} 14}^2=\frac{U_{d c}^2\left(C_{12}^2-C_{14}^2\right)}{4 
% L_d L_q\left(\omega_s \pm 3 \omega_e\right)^2}>0$$ (3.35)
% 
% 가 SVPWM의 경우에는 항상 더 중요하다는것이 분명해진다. ( 나는 아닌데 ?) 
% 
% 식 3.32를 살펴보면 주요 sideband 전류가 modulation index와 토크 각에 종속적이라는것을 확인할수 있다.  $\sigma$(Modulation 
% Index)인데 Ld,Lq로 정의 와 $\delta$ (토크각)
% 
% 
% 
% 4kHz , 24V_{DC}의 PMSM prototypeII에서 검토되었다. Figure 3.5
% 
% 두성분 모두 Modulation Index가 증가함에 따라 급격히 증가한다. 
% 
% 반면 q축 인덕턴스가 d축에 비해 크기때문에 (Inset magnet) 두 성분모두 토크각이 증가함에따라 완만하게 감소한다.
% 
% $\omega_s \pm 4\omega_e$ 의 감소가 더 눈에 띄긴한다.

calcSigma;
calcSideCurrentStationary_phi;
calcSideCurrentStationary;

% arc cosine
phi_s_14=acos(cos_phi_s_14);
phi_s_12=acos(cos_phi_s_12);
phi_s_s12=asin(sin_phi_s_12);

% eq 3.31
is_1Pos2 = Is_12*sin((w_s+2*w_e)*t - phi_s_12);
is_1Neg2 = -Is_12*sin((w_s-2*w_e)*t + phi_s_12);
is_1Pos4 = Is_14*cos((w_s+4*w_e)*t + phi_s_14);
is_1Neg4 = -Is_14*cos((w_s-4*w_e)*t - phi_s_14);

% eq 3.32
% (w_s +-2w_e, w_s +-4w_e) current harmonics 
Is_12 = (Udc*sqrt((sigma1^2*C12^2 + sigma2^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta))) / (4*(w_s + 2*w_e)));
Is_14 = (Udc*sqrt((sigma2^2*C12^2 + sigma1^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta))) / (4*(w_s + 4*w_e)));


% eq 3.33
cos_phi_s_12 = ((sigma1*C12 - sigma2*C14)*sin(delta)) / sqrt(sigma1^2*C12^2 + sigma2^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta));
sin_phi_s_12 = -((sigma1*C12 + sigma2*C14)*cos(delta)) / sqrt(sigma1^2*C12^2 + sigma2^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta));

cos_phi_s_14 = ((sigma2*C12 - sigma1*C14)*sin(delta)) / sqrt(sigma2^2*C12^2 + sigma1^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta));
sin_phi_s_14 = ((sigma2*C12 + sigma1*C14)*cos(delta)) / sqrt(sigma2^2*C12^2 + sigma1^2*C14^2 + 2*sigma1*sigma2*C12*C14*cos(2*delta));

% eq 3.34
sigma1 = 1/Ld + 1/Lq;
sigma2 = 1/Ld - 1/Lq;

% eq 3.35
Is_12_sq = Is_12^2;
Is_14=sqrt(Is_12_sq -Udc^2*(C12^2 - C14^2) / (4*Ld*Lq*(w_s + 3*w_e)^2));

%% 
% $$i_{s_{-}\left(2 \omega_s \pm \omega_e\right)}=\mp I_{s_{-} 21} \cos \left(\left(2 
% \omega_s \pm \omega_e\right) t \pm \varphi_{s_{-} 21}\right)$$ (3.36)
% 
% 
% 
% $$\left\{\begin{array}{l}i_{s_{-}\left(2 \omega_s \pm 5 \omega_e\right)}= 
% \pm I_{s_2 25} \cos \left(\left(2 \omega_s \pm 5 \omega_e\right) t \mp \varphi_{s_{-} 
% 25}\right) \\ i_{s_{-}\left(2 \omega_s \pm 7 \omega_e\right)}= \pm I_{s_{-} 
% 27} \cos \left(\left(2 \omega_s \pm 7 \omega_e\right) t \pm \varphi_{s_{-} 27}\right)\end{array}\right.$$ 
% (3.37)
% 
% 
% 
% $I_{s 21}=-\frac{U_{d c} C_{21}}{4 \omega_s} \sqrt{\frac{\sin ^2 \delta}{L_d^2}+\frac{\cos 
% ^2 \delta}{L_q^2}}$  (3.38)
% 
% $$\cos \varphi_{s-21}=\frac{L_d \cos \delta}{\sqrt{L_d^2 \cos ^2 \delta+L_q^2 
% \sin ^2 \delta}}, \quad \sin \varphi_{s_{-} 21}=\frac{L_q \sin \delta}{\sqrt{L_d^2 
% \cos ^2 \delta+L_q^2 \sin ^2 \delta}}$$ (3.39)
% 
% 
% 
% $$\left\{\begin{array}{l}I_{s_{-} 25}=\frac{U_{d c} \sqrt{\sigma_1^2 C_{25}^2+\sigma_2^2 
% C_{27}^2+2 \sigma_1 \sigma_2 C_{25} C_{27} \cos (2 \delta)}}{4\left(2 \omega_s 
% \pm 6 \omega_e\right)} \\ I_{s_{-} 27}=\frac{U_{d c} \sqrt{\sigma_2^2 C_{25}^2+\sigma_1^2 
% C_{27}^2+2 \sigma_1 \sigma_2 C_{25} C_{27} \cos (2 \delta)}}{4\left(2 \omega_s 
% \pm 6 \omega_\rho\right)}\end{array}\right.$$ (3.40)
% 
% 
% 
% $$\left\{\begin{array}{l}\cos \varphi_{s_{-} 25}=\frac{\left(\sigma_1 C_{25}+\sigma_2 
% C_{27}\right) \cos \delta}{\sqrt{\sigma_1^2 C_{25}^2+\sigma_2^2 C_{27}^2+2 \sigma_1 
% \sigma_2 C_{25} C_{27} \cos (2 \delta)}} \\ \sin \varphi_{s_{-} 25}=\frac{\left(\sigma_1 
% C_{25}-\sigma_2 C_{27}\right) \sin \delta}{\sqrt{\sigma_1^2 C_{25}^2+\sigma_2^2 
% C_{27}^2+2 \sigma_1 \sigma_2 C_{25} C_{27} \cos (2 \delta)}} \\ \cos \varphi_{s_{-} 
% 27}=\frac{\left(\sigma_2 C_{25}+\sigma_1 C_{27}\right) \cos \delta}{\sqrt{\sigma_2^2 
% C_{25}^2+\sigma_1^2 C_{27}^2+2 \sigma_1 \sigma_2 C_{25} C_{27} \cos (2 \delta)}} 
% \\ \sin \varphi_{s_{-} 27}=\frac{-\left(\sigma_2 C_{25}-\sigma_1 C_{27}\right) 
% \sin \delta}{\sqrt{\sigma_2^2 C_{25}^2+\sigma_1^2 C_{27}^2+2 \sigma_1 \sigma_2 
% C_{25} C_{27} \cos (2 \delta)}}\end{array}\right.$$ (3.41)
% 
% 

calcSigma;
calcSideCurrentStationary_phi;
calcSideCurrentStationary;

% arc cosine
phi_s_21=acos(cos_phi_s_21);
phi_s_25=acos(cos_phi_s_25);
phi_s_27=acos(cos_phi_s_27);



% 3.36
is_2wsPos1we = -Is_21*cos((2*w_s+w_e)*t+phi_s_21);
is_2wsNeg1we = Is_21*cos((2*w_s-w_e)*t-phi_s_21);

% 3.37
is_2wsPos5we = Is_25*sin((2*w_s + 5*w_e)*t - phi_s_25);
is_2wsNeg5we = -Is_25*sin((2*w_s - 5*w_e)*t + phi_s_25);

is_2wsPos7we = Is_27*sin((2*w_s + 7*w_e)*t + phi_s_27);
is_2wsNeg7we = -Is_27*sin((2*w_s - 7*w_e)*t - phi_s_27);

% 3.38
Is_21 = - (Udc*C21)/(4*ws)*sqrt((sin(delta)/Ld)^2 + (cos(delta)/Lq)^2);

% 3.39 
cos_phi_s_21 = Ld*cos(delta)/sqrt(Ld^2*cos(delta)^2+Lq^2*sin(delta)^2);
sin_phi_s_21 = Lq*sin(delta)/sqrt(Ld^2*cos(delta)^2+Lq^2*sin(delta)^2);

% 3.40
Is_25 = Udc * sqrt(sigma_1^2*C25^2 + sigma_2^2*C27^2 + 2*sigma_1*sigma_2*C25*C27*cos(2*delta)) / (4*(2*w_s + 6*w_e));
Is_27 = Udc * sqrt(sigma_2^2*C25^2 + sigma_1^2*C27^2 + 2*sigma_1*sigma_2*C25*C27*cos(2*delta)) / (4*(2*w_s + 6*w_e));

% 3.41
cos_phi_s_25 = (sigma_1*C25 + sigma_2*C27*cos(delta)) / sqrt(sigma_1^2*C25^2 + sigma_2^2*C27^2 + 2*sigma_1*sigma_2*C25*C27*cos(2*delta));
sin_phi_s_25 = (sigma_1*C25 - sigma_2*C27*sin(delta)) / sqrt(sigma_1^2*C25^2 + sigma_2^2*C27^2 + 2*sigma_1*sigma_2*C25*C27*cos(2*delta));
cos_phi_s_27 = (sigma_2*C25 + sigma_1*C27*cos(delta)) / sqrt(sigma_2^2*C25^2 + sigma_1^2*C27^2 + 2*sigma_1*sigma_2*C25*C27*cos(2*delta));
sin_phi_s_27 = -(sigma_2*C25 - sigma_1*C27*sin(delta)) / sqrt(sigma_2^2*C25^2 + sigma_1^2*C27^2 + 2*sigma_1*sigma_2*C25*C27*cos(2*delta));


%% 
% 상전류 합성 

is_fund=sqrt(id^2+iq^2)*cos((w_e)*t)
is = is_fund+ is_2wsPos1we + is_2wsNeg1we + is_2wsPos5we + is_2wsNeg5we + is_2wsPos7we + is_2wsNeg7we + is_1Pos2 + is_1Neg2 + is_1Pos4 + is_1Neg4;
plot(is)
%% 3.5 Improved Analytical Sideband Current Harmonic Modeling

% % Calculate Cm values
% Cm_d13 = (M_dq^2*(C_12^2+C_14^2-2*C_12*C_14*cos(2*delta))-4*C_12*C_14*M_dq*L_q*sin(2*delta))/L_q^2;
% Cm_q13 = (M_dq^2*(C_12^2+C_14^2+2*C_12*C_14*cos(2*delta))-4*C_12*C_14*M_dq*L_d*sin(2*delta))/L_d^2;
% Cm_d26 = (M_dq^2*(C_25^2+C_27^2-2*C_25*C_27*cos(2*delta))-4*C_25*C_27*M_dq*L_q*sin(2*delta))/L_q^2;
% Cm_q26 = (M_dq^2*(C_25^2+C_27^2+2*C_25*C_27*cos(2*delta))-4*C_25*C_27*M_dq*L_d*sin(2*delta))/L_d^2;
% 
% % Calculate phase angles
% phi_d13 = atan(((C_12+C_14)*(M_dq*sin(delta)-L_q*cos(delta)))/sqrt(L_q^2*(C_12^2+C_14^2+2*C_12*C_14*cos(2*delta)+Cm_d13)));
% phi_q13 = atan(((C_12-C_14)*(M_dq*cos(delta)+L_q*sin(delta)))/sqrt(L_q^2*(C_12^2+C_14^2+2*C_12*C_14*cos(2*delta)+Cm_q13)));
% phi_d26 = atan(((C_25-C_27)*(L_q*sin(delta)+M_dq*cos(delta)))/sqrt(L_q^2*(C_25^2+C_27^2+2*C_25*C_27*cos(2*delta)+Cm_d26)));
% phi_q26 = atan(((C_27-C_25)*(M_dq*sin(delta)+L_d*cos(delta)))/sqrt(L_d^2*(C_25^2+C_27^2-2*C_25*C_27*cos(2*delta)+Cm_q26)));
% 
% % Calculate Ud and Uq values
% Ud_13 = Udc/2*sqrt(C_12^2+C_14^2+2*C_12*C_14*cos(2*delta)+Cm_d13);
% % U_q13 = Udc/2*sqrt(C_12^
% 
% 
% %
% id_w_mu = (L_q * u_d_w_mu - M_dq * u_q_w_mu) / (1j * w_mu * (L_d * L_q - M_dq^2));
% iq_w_mu = (L_d * u_q_w_mu - M_dq * u_d_w_mu) / (1j * w_mu * (L_d * L_q - M_dq^2));
% 
% 
% U_d_13 = Udc/2 * sqrt(C_12^2 + C_14^2 + 2*C_12*C_14*cos(2*delta) + C_m_d_13);
% U_q_13 = Udc/2 * sqrt(C_12^2 + C_14^2 - 2*C_12*C_14*cos(2*delta) + C_m_q_13);
% U_d_26 = Udc/2 * sqrt(C_25^2 + C_27^2 + 2*C_25*C_27*cos(2*delta) + C_m_d_226);
% U_q_26 = Udc/2 * sqrt(C_25^2 + C_27^2 - 2*C_25*C_27*cos(2*delta) + C_m_q_226);
% 
% C_md_13 = (Mdq^2*(C_12^2 + C_14^2 - 2*C_12*C_14*cos(2*delta)) - 4*C_12*C_14*Mdq*Lq*sin(2*delta))/Lq^2;
% C_mq_13 = (Mdq^2*(C_12^2 + C_14^2 + 2*C_12*C_14*cos(2*delta)) - 4*C_12*C_14*Mdq*Ld*sin(2*delta))/Ld^2;
% C_md_26 = (Mdq^2*(C_25^2 + C_27^2 - 2*C_25*C_27*cos(2*delta)) - 4*C_25*C_27*Mdq*Lq*sin(2*delta))/Lq^2;
% C_mq_26 = (Mdq^2*(C_25^2 + C_27^2 + 2*C_25*C_27*cos(2*delta)) - 4*C_25*C_27*Mdq*Ld*sin(2*delta))/Ld^2;
% 
% cos_phi_d_13 = ((C_12 + C_14)*(Mdq*sin(delta) - Lq*cos(delta)))/sqrt(Lq^2*(C_12^2 + C_14^2 + 2*C_12*C_14*cos(2*delta) + C_md_13));
% sin_phi_d_13 = ((C_12 - C_14)*(Mdq*cos(delta) + Lq*sin(delta)))/sqrt(Lq^2*(C_12^2 + C_14^2 + 2*C_12*C_14*cos(2*delta) + C_md_13));
% cos_phi_q_13 = ((C_12 - C_14)*(Mdq*sin(delta) + Ld*cos(delta)))/sqrt(Ld^2*(C_12^2 + C_14^2 - 2*C_12*C_14*cos(2*delta) + C_mq_13));
% sin_phi_q_13 = ((C_12 + C_14)*(Mdq*cos(delta) - Ld*sin(delta)))/sqrt(Ld^2*(C_12^2 + C_14^2 - 2*C_12*C_14*cos(2*delta) + C_mq_13));
% cos_phi_d_226 = ((C_25 - C_27)*(Lq*sin(delta) + Mdq*cos(delta)))/sqrt(Lq^2*(C_25^2 + C_27^2 + 2*C_25*C_27*cos(2*delta) + C_md_26));
% sin_phi_d_22 = ((C_25 + C_27)*(Lq*cos(delta) - Mdq*sin(delta)))/sqrt(Lq^2*(C_25^2 + C_27^2 + 2*C_25*C_27*cos(2*delta) + C_md_26));
% cos_phi_q_26 = ((C_27 + C_25)*(Mdq*cos(delta) - Ld*sin(delta)))/sqrt(Ld^2*(C_25^2 + C_27^2 - 2*C_25*C_27*cos(2*delta) + C_mq_26));
% sin_phi_q_226 = ((C_27 - C_25)*(Mdq*sin(delta) + Ld*cos(delta)))/sqrt(Ld^2*(C_25^2
% 
% 
% 
% % 수식 계산 (3.64) Sideband Current Harmonics in Stationary Frame
% I_s_12 = (Udc*sqrt(sigma1^2*C_12^2 + sigma2^2*C_14^2 + 2*sigma1*sigma2*C_12*C_14*cos(2*delta) + R_12))/(4*(w_s + 3*w_e)*(1-sigmaM^2));
% I_s_14 = (Udc*sqrt(sigma2^2*C_12^2 + sigma1^2*C_14^2 + 2*sigma1*sigma2*C_12*C_14*cos(2*delta) + R_14))/(4*(w_s + 3*w_e)*(1-sigmaM^2));
% 
% 
% Is21 = -Udc*C21/(4*w_s*(1-sigmaM^2)*sqrt((sin(delta)/Ld)^2 + (cos(delta)/Lq)^2 + R21));
% Is25 = Udc*sqrt(sigma1^2*C25^2 + sigma2^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta) + R25)...
%        /(4*(2*w_s + 6*wc)*(1-sigmaM^2));
% Is27 = Udc*sqrt(sigma2^2*C25^2 + sigma1^2*C27^2 + 2*sigma1*sigma2*C25*C27*cos(2*delta) + R27)...
%        /(4*(2*w_s + 6*wc)*(1-sigmaM^2));
% 
% 
% 
% %  coefficient (3.67)
% R12 = 4*sigma_M^2*C14^2/(Ld*Lq) - (4*sigma_1*Mdq*C12*C14/(Ld*Lq))*sin(2*delta);
% R14 = 4*sigma_M^2*C12^2/(Ld*Lq) - (4*sigma_1*Mdq*C12*C14/(Ld*Lq))*sin(2*delta);
% R21 = sigma_M^2/(Ld*Lq) + ((1/Ld)+(1/Lq))*(Mdq/(Ld*Lq))*sin(2*delta);
% R25 = 4*sigma_M^2*C27^2/(Ld*Lq) - (4*sigma_1*Mdq*C25*C27/(Ld*Lq))*sin(2*delta);
% R27 = 4*sigma_M^2*C25^2/(Ld*Lq) - (4*sigma_1*Mdq*C25*C27/(Ld*Lq))*sin(2*delta);