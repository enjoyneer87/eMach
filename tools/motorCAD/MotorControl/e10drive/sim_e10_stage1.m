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
%   상태 (2026-09-17): 플랜트·역맵·기준표는 검증됐고 루프는 돌지만 **제어기 정정 전**이다.
%   16 krpm 에서 전류 추종이 기준표보다 15~40 % 높게 정착하고 약자속 트림이 계속 물린다.
%   원인 후보: (i) we*Ts = 0.67 rad (샘플당 전기각 38도) 라 2 kHz 대역 dq PI + 1샘플 지연이
%   안정 한계에 가깝다, (ii) 기준점 자체가 전압 한계에 붙어 있어 약자속 외루프가 항상 활성이다.
%   다음 작업: 복소벡터(또는 지연보상) 전류제어로 바꾸고 Ts 를 20~50 us 로 낮춰 재정정,
%   약자속 루프에 불감대와 누설을 넣는다. 그 다음에야 4절 실험(오프셋·지연·상한)이 의미를 갖는다.

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
Kp  = d('Kp', Ld*2*pi*2000);               % 전류 루프 2 kHz
Ki  = d('Ki', R_ph*2*pi*2000);
Kaw = d('Kaw', 1/(Ld/R_ph));
Kfw = d('Kfw', 2);                         % 약자속 외루프 [A/(V·s)]
fwMax = d('fw_max', 80);                   % 기준표가 이미 약자속점이라 트림 폭만 준다
Vtgt = d('V_target', 0.95)*Vmax;           % 전압 여유 (한계에 딱 붙이면 감김)

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
Xd = 0; Xq = 0; Xfw = 0;  v_ctrl = [0; 0];  v_app = [0; 0];

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
    % 전향보상은 기준표의 자속을 쓴다 (제어기가 실제로 가진 정보). 상수 Ld/Lq 보다 오차가 작다.
    fdr = interp1(S.T_ref_vec, fdRef, min(max(Tr, 0), S.T_ref_vec(end)), 'linear', 'extrap');
    fqr = interp1(S.T_ref_vec, fqRef, min(max(Tr, 0), S.T_ref_vec(end)), 'linear', 'extrap');
    vd_u = Kp*ed + Xd - we*fqr;
    vq_u = Kp*eq + Xq + we*fdr;
    vmag = hypot(vd_u, vq_u);
    if vmag > Vmax
        vd = vd_u*Vmax/vmag;  vq = vq_u*Vmax/vmag;  sat = 1;
    else
        vd = vd_u;  vq = vq_u;  sat = 0;
    end
    Xd = Xd + Ts*(Ki*ed + Kaw*(vd - vd_u));
    Xq = Xq + Ts*(Ki*eq + Kaw*(vq - vq_u));
    Xfw = min(max(0, Xfw + Ts*Kfw*(vmag - Vtgt)), fwMax);
    v_ctrl = [vd; vq];

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
               'Kp', Kp, 'Ki', Ki, 'Kfw', Kfw, 'Vmax_peak', Vmax);
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
