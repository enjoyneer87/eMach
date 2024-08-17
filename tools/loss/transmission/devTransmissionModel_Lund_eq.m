
zpn = 20; % number of teeth on pinion
gmfn = (zpn * nn) / 60;  
%% 기어사이징 모델
m= rho_gears * pi * b * d^2 / 4;

%% Layout Model

%\begin{equation}
%M_{\text {tot }_N}=\pi \rho \sum_{n=1}^N \frac{2\left(u_n+1\right) T_{p, n}}{u_n K_{0 n}} \frac{\left(e_1+e_2 u_n^2\right)}{4}
%\end{equation}
%where $T_{p, n}$ is the allowable torque on the shaft, $K_{0 n}$ is the allowable load intensity factor, $\rho$ is the density of the gears, $d_{w_{1 n}}$ is the pitch diameter of the pinion, $u_n$ is the gear ratio, and $e_1$ and $e_2$ is the volume coefficients of pinion and wheel, respectively.

K0n = 1.5; % allowable load intensity factor
e1 = 0.5; % volume coefficient of pinion
e2 = 0.5; % volume coefficient of wheel
u = 1.5; % gear ratio
T_pn = 100; % allowable torque on the shaft

for n = 1:N
    M_totN = pi * rho_gears * (2 * (u(n) + 1) * T_pn(n)) / (u(n) * K0n(n)) * (e1 + e2 * u(n)^2) / 4;
end


%b_0 Coefficient of face width
b = b_0 * m_n; % face width 
%  m_n 은 normal 모듈입니다.[mm]
%     gear sizing
dp % pinion diameter

Ft = (2 * T) / dp; % tangential force on reference cylinder



%     bending stress limit

sigmaH0 = Z_H * Z_E * Zepsilon * Z_beta * sqrt((Ft / (dp * b)) * ((U + 1) / U));
sigmaHp = Z_B * sigmaH0 * sqrt(K_A * K_gamma * Kv * KHbeta * KHalpha);
sigmaH0wheel = Z_D * sigmaH0 * sqrt(K_A * K_gamma * Kv * KHbeta * KHalpha);
sigmaHG = sigmaHlim * Z_NT * ZL * ZV * ZR * ZW * ZX;

%     bending sheer stress limit
sigmaF0 = (Ft / (b * mn)) * YF * YS * Ybeta * Y_B * Y_DT;
% 여기서 Ft 는 횡방향 접선 하중, b 는 기어의 면 너비, mn 은 일반 모듈입니다.
% 치근 응력 한계( $\sigma _{FG}$ )는 공식 13에 따라 허용 치근 응력 $\sigma _{Flim}$ )에서 계산했습니다.
sigmaFG = sigmaFlim * Y_ST * Y_NT * Ydelta_relT * YR_relT * Yx;
% 치아 굽힘에 대한 일반적인 영향 요인인 K Fβ 및 K Fα 은 ISO [20]에 따라 계산된 굽힘 응력 요인인
% Y와 함께 부록의 표 A.1에서 확인할 수 있습니다.
%      constraints
% Hunting tooth ratio
% 
% 헌팅 치아 비율을 달성하기 위해 더들리[21]가 설명한 것처럼 치아 번호는 상대적으로 소수 로 선택됩니다
% 
% Durability Constraints
sigmaHG / sigmaH > SH;
% 
% further constraints
% 기어가 언더컷, 간섭 없이 작동하고 톱니 두께가 팁 반경에서 0보다 큰지 확인하기 위해 추가
% 제약 조건이 정의됩니다. 기어의 림 두께( $s_R$ )는 톱니 뿌리 아래에 얼마나 많은 재료가 존재하는지를 측정하는 것으로,
% 재료의 폭은 톱니의 면 폭과 같습니다[20]. 그림 2.5는 기어 림을 보여줍니다.
s_R >= 1.2 * h_t;
% 치아의 굽힘 응력에 영향을 주지 않기 위해 ISO [20]에 따라 방정식 16을 충족하는 최소 림 두께를
% 선택했습니다.
% 여기서 $h_t$ 는 치아 높이입니다.
% 마지막으로, 최소 횡단 및 총 접촉비와 같이 BorgWarner에서 정의한 몇 가지 설계 제약 조건이 있습니다. 보그워너의 기어 설계 
% 제약 조건은 동력 전달 장치 설계에서 얻은 테스트 및 경험을 기반으로 하며, 바람직한 작동 및 제조 조건을 보장합니다. 이러한 제약 조건에 
% 대한 값은 보그워너의 기밀 자산이므로 이 보고서에서 제외되었습니다.
%  다른 구성요소의 크기조정
% 변속기 시스템의 다른 구성 요소로는 샤프트, 베어링, 씰이 있습니다. 샤프트와 베어링은 기계적
% 과부하로 인한 고장 없이 메시 하중과 토크를 견딜 수 있도록 크기를 측정했습니다. 씰은 이 논문
% 에서 크기 조정에서 제외되었습니다
%     shaft sizing
d_shMin= ((sqrt((Kts * 32 * M)^2 + 3 * (Ktnom * 16 * T)^2)) / (pi * sigmaAllow))^(1 / 3);
% 여기서 $d_{sh,min}$은 샤프트의 최소 허용 직경, $K_{ts}$ 및 $K_{tnom}$ 은 각각 굽힘 모멘트와 토크에 대한
% 응력 집중 계수, $M_b$ 은 굽힘 모멘트, T는 샤프트의 토크, $\sigma _{allow}$ 은 제한 응력을 $\frac{\sigma_{lim}}{F_s}$ 
% 안전 계수로 나 눈 값입니다,
% 샤프트의 길이는 샤프트의 구성 요소 수에 따라 결정되며 모든 구성 요소 사이에 지정된 간격이 있
% 습니다. 샤프트의 직경과 길이는 모두 선택한 베어링에 따라 달라집니다.
%  Bearing sizing
% 모델에 사용된 베어링은 SKF 제품 카탈로그 [23]의 깊은 홈 볼 베어링 데이터베이스에서 선택했
% 습니다. 따라서 SKF [23]에 따라 사이징을 수행했습니다.
% 이 접근 방식은 최소 샤프트 직경을 베어링의 최소 내경으로 사용했습니다. 하중을 견딜 수 있는

d_brMin=d_shMin
% 질량이 가장 낮은 베어링이 선택되었습니다. 베 어 링 의 내경이 샤프트 직경보다 큰 경우, 샤프트
% 직경 증가에 따른 추가 질량도 베어링을 선택할 때 고려했습니다.

% 질량에서 제외되었습니다.
%     Packaging model
% diversion angle
% 그림 2.6의 전환 각도 γ는 각도를 생성하는 두 중심 거리와 각도의 반대쪽을 사용하여 코사인의 법
% 칙으로 계산되었습니다. 반대쪽의 최소 길이는 첫 번째와 마지막 샤프트의 구성 요소 간 충돌에 대
% 한 제약 조건을 기반으로 했습니다.
% 그림 2.7의 γ1 및 γ2 에 대해서도 비슷한 계산을 수행했습니다. 그러나 γ1 은 고정된 값으로 설정
% 되었고 γ2 은 구성 요소의 충돌을 일으키지 않고 최소화되었습니다. 이상적으로는 두 각도가
% 모두 최적화되어야 하지만 패키징에 대한 최적화 목표가 개발되지 않았기 때문에 두 각도의
% 최적 조합을 찾을 수 없었습니다.
y1 = (R1^2 - R2^2 - a1^2) / (-2 * a1);
y2 = sqrt(R1^2 - y1^2);

% outer dimensions of transmission system
% 전송 시스템의 외부 치수는 전송 최적화 도구의 출력 매개변수입니다.
% 이 방법은 각 샤프트에서 가장 큰 기어를 사용하여 변속기 시스템의 외부 경계를 정의했습니
% 다. 그림 2.6에는 길이와 높이의 두 가지 치수 L과 H가 나와 있습니다. 치수는 방정식 18을 사
% 용하여 계산했습니다.

L_2stage =  R1 + a1 + R2 + 2 * s + 2 * t;
H_2stage = R2 + X + R3 + 2 * s + 2 * t;   
% 여기서 L2Stage 은 길이, H2Stage 은 높이, a1 는 1단 기어 스테이지의 중심 거리입니다,
% a2 는 마지막 기어 스테이지의 중심 거리, γ 는 전환 각도, s 는 부품 간격, t 는 하우징의 벽 두께
% 입니다.
% 그림 2.7에서 볼 수 있듯이 3단 레이샤프트 레이아웃의 외부 치수의 근사치도 비슷한 방식으로 계
% 산했습니다.
% Approximation of housing mass
% 변속기 시스템의 외형 치수를 활용하여 하우징에 필요한 재료의 양에 대한 대략적인 추정치를 얻
% 었습니다. 길이, 높이, 너비를 사용하여 방정식 21에 따라 기어박스의 부피를 구한 다음 방정식 22
% 에 따라 알루미늄으로 만든 하우징의 대략적인 질량을 계산했습니다.
V= L * W * H - (L - 2 * t) * (W - 2 * t) * (H - 2 * t);
m_housing = rho_housing * V;

%%  loss model
% 전력 손실은 일반적으로 부하 및 비부하 의존적 손실로 나뉩니다[24, 25, 26, 27]. 표 2.2에 따라 계산했 
% 습니다. ISO [26]에서도 포함되는 전력 손실인 펌프 및 샤프트 손실은 이 논문에서 무시되었습니다.
% load dependent losses
% Gear loaded losses
% 이 논문에서 가정한 기어 부하 손실은 기어 메시의 마찰에서 비롯됩니다. ISO [26]의 기어 메시 전력 손실 방정식:
P_m= (f_m * T_p * n_p * cos(beta_w)^2) / (9549 * M);
% 여기서 PM 는 메시 전력 손실, $f_m$ 는 메시 마찰 계수, $T_p$ 는 피니언의 토크, $n_p$ 은 피니언의 회전 속
% 도, $\beta _w$ 는 작동 나선 각도, M 은 메시 기계적 이점입니다.
% 접촉 경로에 대한 평균 상수 마찰 계수를 근사화하는 Schlenck(방정식 24)가 정의한 ISO[28]의 마찰 계수를 사용했습니다
f_m= 0.048 * ((F_bt / b) / (v_SigmaC * rho_redC))^0.2 * eta_oil^(-0.05) * Ra^0.25 * XL;
% 여기서 $F_{bt}$ 는 베이스 원에서의 접선력, b 는 톱니 폭, $v_{\Sigma C}$ 는 작동 피치 원에서의 합 속도, $\rho 
% _{redC}$  는 피치 포인트에서의 곡률 감소 반경, $\eta _{oil}$ 는 동적 오일 점도, $R_a$ 은 산술 평균 조도, $X_L$ 는 
% 오일 유형에 대한 계수입니다.
% 

% bearing load losses
% 베어링의 부하 동력 손실을 결정하기 위해 ISO [26](방정식 25)의 추정치인 베어링 마찰 토크 $M_B$을 사용했습니다
M_B= (f_B * P)^i * (d_m)^j / 1000; 
P_B = M_B * n / 9549;
% 여기서 마찰 계수 $f_B$ 는 ISO [26]에서 선택한 값이고, P는 베어링 동적 하중입니다, $d_m$ 는 베어링 평균 직경이고, i와 j는 베어링 유형에 따른 지수입니다.방정식 26에서 마찰 토크에 베어링의 회전 속도를 곱 하 여 전력 손실을 결정했습니다.
% non-load dependent losses
% 모델에 포함된 비부하 의존적 전력 손실은 기어와 베어링의 풍력 및 오일 휘젓는 전력 손실과 오일씰 전력 손실입니다
% windage and churning losses
% 기어 감김 및 휘젓는 손실은 ISO [26]을 적용했으며, 기어 면에서의 손실(PGW 1)과 톱니 표면에서의 손실(PGW 2)을 개별적으로 계산했습니다. 기어의 면에는 방정식 27을, 기어의 톱니 표면에는 방 정식 28을 사용했습니다.
P_GW1 = (1.474 * fg * nu * n^3 * D^5.7) / (Ag * 10^26);
P_GW2 = (7.37 * fg * nu * n^3 * D^4.7 * b * (Rf / sqrt(tan(beta)))) / (Ag * 10^26);
% 여기서 fg 는 기어 딥 계 수 , ν 은 오일 점도, n 은 요소의 회전 속도, Ag 는 배열 상수, Rf 은 조도 계수, b 는 전체 면 폭, D 는 요소의 외경, β 는 나선 각도입니다.
% 베어링의 바람과 휘청거림에 대한 전력 손실 방정식인 PBW 도 ISO [26]에 나와 있습니다
% oil seal losses
% 방정식 29의 오일 씰 전력 손실 함수는 Schlegel과 H¨osl [24]이 설명한 것으로, 다음과 같이 정의됩니다. H. Linke가 사용되었습니다.
P_VD = (145 - 1.6 * theta + 350 * log(log(nu40 + 0.8))) * 10^(-16) * dsh^2 * n;
% 여기서 P VD 는 오일 씰의 동력 손실, θ 는 온도, ν40° 는 40°C에서 오일 점도, dsh 는 샤프트 직경입니다.
% scoring model
% \begin{equation}
% 
% \eta_P=\frac{P_{\text {out }}}{P_{\text {in }}}=\frac{P_{\text {in }}-P_{\text 
% {loss }}}{P_{\text {in }}}
% 
% \end{equation}
etaP = P_out / P_in;
% 
% 
% $$
% 
% P_{\text {wheels }}=\left(F_{\text {drag }}+F_{\text {roll }}\right) v
% 
% $$
P_Wheels = (F_drag + F_roll) * v;
% where $F_{d r a g}=C_d A \frac{\rho_a v^2}{2}$, and $F_{\text {roll }}=\mu 
% m g$.
% 
% 
% 
% \begin{equation}
% 
% P(m)=C_d A \frac{\rho v^3}{2}+\left(m_0+m\right) g \mu v
% 
% \end{equation}
P_m = Cd * A * rho * v^3 / 2 + (m0 + m) * g * mu * v;

% 
% 
% 


% 
% 
% 
% 
% 
%