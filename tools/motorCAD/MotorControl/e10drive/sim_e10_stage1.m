function R = sim_e10_stage1(S, opt)
%SIM_E10_STAGE1  단계 1 — 평균값 dq 플랜트 + 이산 FOC/약자속 (스위칭 없음).
%
%   build_e10_stage1.m 이 조립할 Simulink 모델과 같은 방정식을 고정스텝으로 푼다.
%   (Simulink 래핑 전에 물리·제어 내용을 먼저 확정하기 위한 구현)
%
%   플랜트 (연속, ode4 대신 h 고정 RK4)
%     dλd/dt = vd - R id + we λq,   dλq/dt = vq - R iq - we λd
%     (id, iq) = 역맵(λd, λq),      T_shaft = 토크맵(id, iq)   (제동 손실 이미 반영)
%
%   제어기 (이산 Ts)
%     기준표 T* -> (id*, iq*) -> 전류 PI(디커플링·안티와인드업) -> 전압 원 제한
%     약자속 외루프: |v*| 가 한계를 넘으면 id 를 더 음수로 민다
%     오차원: 레졸버 오프셋 th_err (제어기 프레임 회전), 연산 지연 n_delay 샘플
%
%   opt 필드 (기본값)
%     Tref_fn   @(t) 요구 축 토크 [N·m]        (기본: 20 N·m 스텝)
%     th_err    레졸버 오프셋 [전기각 deg]      (0)
%     n_delay   연산 지연 [샘플]                (1)
%     ref       'current' | 'loss'              ('current')
%     Ts, h, Tstop, Kp, Ki, Kfw                 (아래 기본값)
%
%   상태 (2026-09-17): 플랜트는 단위 시험 통과(test_e10_plant.m — 열린 루프로 정상상태 전압을
%   인가하면 세 점 모두 0.1 A 안에서 기준점에 머문다. 필요 전압은 한계의 24~87 %라 여유도 있다).
%   제어기 실험 기록 (2026-09-17, 전부 MCB 이득 + 약자속 트림 끔, Ts=50 us):
%     구조              5 Nm      20 Nm     60 Nm     85 Nm     비고
%     보통 PI+상수디커플 -161 %   -117 %    -6.5 %   -11.7 %   고토크는 잘 맞고 저토크 붕괴
%     복소벡터 PI       -171 %    +10 %    -25.6 %  -37.1 %   중간 토크만 맞음
%   저토크에서 두 구조 모두 감마 90도로 붕괴한다(iq -> 0). 원인은 전향보상 모델 오차로 보인다 —
%   깊은 약자속점에서 상수 Ld/lam 으로 계산한 we*(Ld id + lam) 이 실제보다 85 V 작다.
%   **다음 작업: 손으로 짠 제어기를 버리고 MCB 의 FOC 블록(Field Weakening Control,
%   MTPA Control Reference, 전류 PI)을 Simulink 에 그대로 인스턴스화한다.** 사용자 지적대로
%   튜닝·구조가 이미 검증된 것을 쓰는 편이 빠르고, 플랜트(자속맵)는 그대로 붙이면 된다.
%
%   **남은 것은 제어기뿐이다.** 전류 PI 이득은 Motor Control Blockset 설계식에서 받았고
%   (mcb.getPIControllerParameters, Modulus Optimum; Ts=50 us 에서 Kp_d 8.5 / Kp_q 16.0 V/A,
%   Ki = Kp/(L/R), 약자속 Kp 0.79 A/V · Ki 38.9 A/(V·s)), 손으로 고른 값은 전류 P 가 2.5배 과했다.
%   그래도 폐루프가 기준점을 못 잡는다 — we*Ts = 0.34 rad (샘플당 19도) 에서 실축 PI + 기준자속
%   전향보상만으로는 회전 결합을 못 지운다. 다음: 복소벡터 전류제어(또는 측정자속 디커플링 +
%   지연보상)로 교체. 플랜트는 그대로 두면 된다.


if nargin < 2, opt = struct(); end
d = @(f, v) getfielddef(opt, f, v);
Ts    = d('Ts', 1e-4);        % 제어 주기 (10 kHz)
h     = d('h', 2e-6);         % 플랜트 적분 스텝
Tstop = d('Tstop', 0.06);
th    = d('th_err', 0)*pi/180;
nDel  = d('n_delay', 1);
refKind = d('ref', 'current');
Tref_fn = d('Tref_fn', @(t) 20*(t >= 0.005));

m = S.machine;
we = S.we;  R_ph = m.Rs_80C;
Vmax = m.Vph_lim*sqrt(2);                  % 전압 원 (피크)

% 제어기가 쓰는 상수 모델 (일부러 상수 — 실제 제어기도 그렇다)
Ld = 0.85e-3;  Lq = 1.6e-3;  lam = S.fd_vec(end);
% 전류 PI 는 Motor Control Blockset 의 설계식(Modulus Optimum)에서 받는다.
%   mcb.getPIControllerParameters(pmsm, inverter, PU, T_pwm, Ts, Ts_speed)
%   -> Kp_id/Kp_i (PU) 를 V_base/I_base 로 SI 환산, Ti = L/R 이므로 Ki = Kp/Ti.
% Ts = 50 us 기준값 (손으로 고른 값은 전류 P 가 2.5배 과했다).
Kpd = d('Kp_d', 8.50);   Kpq = d('Kp_q', 16.00);
Kid = d('Ki_d', Kpd/(Ld/R_ph));   Kiq = d('Ki_q', Kpq/(Lq/R_ph));
Kaw = d('Kaw', 1/(Ld/R_ph));
% 약자속 루프도 MCB 설계값 (Kp_fwc, Ki_fwc 를 I_base/V_base 로 SI 환산)
KfwP = d('Kfw_p', 0.79);                   % [A/V]
KfwI = d('Kfw_i', 38.9);                   % [A/(V·s)]
fwMax = d('fw_max', 120);
Vtgt = d('V_target', 0.98)*Vmax;

thc = d('delay_comp', 1)*we*(nDel + 0.5)*Ts;   % 지연 보상각 (0 이면 끔)
rotSign = d('rot_sign', 1);
ctrlMode = d('ctrl', 'pi_dec');   % 'pi_dec' | 'cvpi'
idRef = S.(['id_ref_' refKind]);  iqRef = S.(['iq_ref_' refKind]);
fdRef = S.(['fd_ref_' refKind]);  fqRef = S.(['fq_ref_' refKind]);

% 초기 상태: 첫 기준점의 자속
T0 = Tref_fn(0);
id0 = interp1(S.T_ref_vec, idRef, T0, 'linear', 'extrap');
iq0 = interp1(S.T_ref_vec, iqRef, T0, 'linear', 'extrap');
flux = [interp2(S.id_pk, S.iq_pk, S.Fd, id0, iq0, 'linear');
        interp2(S.id_pk, S.iq_pk, S.Fq, id0, iq0, 'linear')];

nStep = round(Tstop/h);
nSub  = round(Ts/h);
vq_hist = zeros(2, max(nDel, 1) + 1);
X = complex(0, 0); Xfw = 0; Xfw_i = 0;  v_ctrl = [0; 0];  v_app = [0; 0];

N = floor(nStep/nSub);
R = struct('t', zeros(N, 1), 'T', zeros(N, 1), 'Tref', zeros(N, 1), 'id', zeros(N, 1), ...
           'iq', zeros(N, 1), 'gamma', zeros(N, 1), 'Irms', zeros(N, 1), 'V', zeros(N, 1), ...
           'fw', zeros(N, 1), 'idcmd', zeros(N, 1), 'sat', zeros(N, 1));

k = 0;
for n = 1:N
    t = (n-1)*Ts;
    % ---- 측정 (제어기 프레임: 레졸버 오프셋만큼 돌아가 있다)
    i_phys = fluxToI(S, flux);
    i_meas = rot(i_phys, -th);
    Tr = Tref_fn(t);
    idr = interp1(S.T_ref_vec, idRef, min(max(Tr, 0), S.T_ref_vec(end)), 'linear', 'extrap');
    iqr = interp1(S.T_ref_vec, iqRef, min(max(Tr, 0), S.T_ref_vec(end)), 'linear', 'extrap');

    % ---- 제어기
    idc = idr - Xfw;
    ed = idc - i_meas(1);   eq = iqr - i_meas(2);
    % 전향보상은 기준표의 자속을 쓴다 (제어기가 실제로 가진 정보).
    fdr = interp1(S.T_ref_vec, fdRef, min(max(Tr, 0), S.T_ref_vec(end)), 'linear', 'extrap');
    fqr = interp1(S.T_ref_vec, fqRef, min(max(Tr, 0), S.T_ref_vec(end)), 'linear', 'extrap');
    % --- 복소벡터 전류제어 (Briz/Lorenz): 적분기를 we 로 회전시켜 교차결합을 상쇄한다.
    %     실축 PI + 상수 디커플링은 we*Ts 가 커지면(여기서 샘플당 19도) 회전 결합을 못 지운다.
    switch ctrlMode
      case 'pi_dec'   % 보통 PI + 측정전류 디커플링 (MCB FOC 와 같은 구조). 동기좌표계 DC 오차 0.
        vu = complex(Kpd*ed, Kpq*eq) + X ...
             + complex(-we*Lq*i_meas(2), we*(Ld*i_meas(1) + lam));
      otherwise       % 'cvpi': 복소벡터 PI (적분기 극점 -jwe) + 기준자속 전향보상
        vu = complex(Kpd*ed, Kpq*eq) + X + complex(-we*fqr, we*fdr);
    end
    vd_u = real(vu);  vq_u = imag(vu);
    vmag = abs(vu);
    if vmag > Vmax
        vd = vd_u*Vmax/vmag;  vq = vq_u*Vmax/vmag;  sat = 1;
    else
        vd = vd_u;  vq = vq_u;  sat = 0;
    end
    X = X*exp(-1i*we*Ts*rotSign*strcmp(ctrlMode,'cvpi')) + Ts*(complex(Kid*ed, Kiq*eq) + Kaw*complex(vd - vd_u, vq - vq_u));
    Xfw_i = min(max(0, Xfw_i + Ts*KfwI*(vmag - Vtgt)), fwMax);
    Xfw = min(max(0, Xfw_i + KfwP*(vmag - Vtgt)), fwMax);
    % --- 지연 보상: 인가 시점의 각도 앞섬 we*(n+0.5)*Ts 만큼 지령을 미리 돌려 둔다
    vc = complex(vd, vq)*exp(1i*thc);
    v_ctrl = [real(vc); imag(vc)];

    % ---- 연산 지연 (샘플 단위) 후 기계 프레임으로
    vq_hist = [vq_hist(:, 2:end), v_ctrl];
    v_app = rot(vq_hist(:, max(1, end-nDel)), th);

    % ---- 플랜트 (RK4, nSub 스텝)
    for s = 1:nSub
        flux = rk4(S, flux, v_app, R_ph, we, h);
    end

    i_phys = fluxToI(S, flux);
    k = k + 1;
    R.t(k) = t;  R.Tref(k) = Tr;
    R.T(k) = interp2(S.id_pk, S.iq_pk, S.T_shaft, ...
                     min(max(i_phys(1), S.id_pk(1)), S.id_pk(end)), ...
                     min(max(i_phys(2), S.iq_pk(1)), S.iq_pk(end)), 'linear');
    R.id(k) = i_phys(1);  R.iq(k) = i_phys(2);
    R.gamma(k) = atan2d(-i_phys(1), i_phys(2));
    R.Irms(k) = hypot(i_phys(1), i_phys(2))/sqrt(2);
    R.V(k) = hypot(v_app(1), v_app(2))/sqrt(2);
    R.fw(k) = Xfw;  R.idcmd(k) = idc;  R.sat(k) = sat;
end
R.opt = struct('Ts', Ts, 'h', h, 'th_err_deg', th*180/pi, 'n_delay', nDel, 'ref', refKind, ...
               'Kp_d', Kpd, 'Kp_q', Kpq, 'Ki_d', Kid, 'Ki_q', Kiq, ...
               'Kfw_p', KfwP, 'Kfw_i', KfwI, 'Vmax_peak', Vmax, 'delay_comp_deg', thc*180/pi);
end

% ------------------------------------------------------------------ helpers
function i = fluxToI(S, flux)
i = [interp2(S.fd_vec, S.fq_vec, S.id_of_flux, flux(1), flux(2), 'linear', NaN);
     interp2(S.fd_vec, S.fq_vec, S.iq_of_flux, flux(1), flux(2), 'linear', NaN)];
if ~all(isfinite(i))                      % 자속 격자 밖 — 가장자리로 클립
    i = [interp2(S.fd_vec, S.fq_vec, S.id_of_flux, ...
                 min(max(flux(1), S.fd_vec(1)), S.fd_vec(end)), ...
                 min(max(flux(2), S.fq_vec(1)), S.fq_vec(end)), 'linear');
         interp2(S.fd_vec, S.fq_vec, S.iq_of_flux, ...
                 min(max(flux(1), S.fd_vec(1)), S.fd_vec(end)), ...
                 min(max(flux(2), S.fq_vec(1)), S.fq_vec(end)), 'linear')];
end
end

function f2 = rk4(S, f, v, R_ph, we, h)
k1 = fdot(S, f,          v, R_ph, we);
k2 = fdot(S, f + h/2*k1, v, R_ph, we);
k3 = fdot(S, f + h/2*k2, v, R_ph, we);
k4 = fdot(S, f + h*k3,   v, R_ph, we);
f2 = f + h/6*(k1 + 2*k2 + 2*k3 + k4);
end

function df = fdot(S, f, v, R_ph, we)
i = fluxToI(S, f);
df = [v(1) - R_ph*i(1) + we*f(2);
      v(2) - R_ph*i(2) - we*f(1)];
end

function y = rot(u, th)
c = cos(th); s = sin(th);
y = [c*u(1) - s*u(2); s*u(1) + c*u(2)];
end

function v = getfielddef(s, f, dflt)
if isfield(s, f) && ~isempty(s.(f)), v = s.(f); else, v = dflt; end
end
