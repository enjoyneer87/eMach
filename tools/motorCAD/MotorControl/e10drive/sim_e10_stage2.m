function R = sim_e10_stage2(S, opt)
%SIM_E10_STAGE2  단계 2 — 스위칭 인버터 + Lab 자속맵 플랜트 + 이산 FOC (단계 1 과 같은 제어기).
%
%   단계 1(sim_e10_stage1)과 다른 점은 전압 인가 경로뿐이다.
%     단계 1: 제어기 dq 전압을 (지연 후) 회전 좌표계에서 그대로 플랜트에 넣는다 (평균값, 스위칭 없음).
%     단계 2: 제어기 dq 전압 -> 제어기 각도로 αβ 변환 -> SVPWM(min-max 주입) 듀티 ->
%             10 kHz 중앙정렬 삼각파, 양 끝 갱신(Ts = Tpwm/2) -> 폴 전압 ±Vdc/2 ->
%             데드타임(전류 부호에 따라 스위칭 순간이 td 만큼 밀림) -> 상전압 -> 기계 각도로 dq -> 플랜트.
%     전압 벡터는 한 반주기 동안 **고정자 좌표계에서** 유지되고, 그동안 회전자는 ωe·Ts 만큼 돈다.
%
%   전류 샘플은 반주기 시작(삼각파 꼭짓점 = 리플 평균점)에서 abc 로 읽어 제어기 각도로 dq 변환한다.
%   레졸버 오프셋 th_err: 제어기 각도 = 기계 각도 + th_err.
%   연산 지연 n_delay: k 번째 샘플로 계산한 αβ 전압이 k+n_delay 번째 반주기에 인가된다.
%   지연 보상 delay_comp: 지령을 ωe(n_delay+0.5)Ts 만큼 미리 돌린다 (반주기 유지 평균각까지 포함).
%   데드타임 보상 dt_comp: 에지가 밀리는 반주기에서만 듀티를 td/Ts 보정한다 (샘플 전류 부호;
%     주기 평균 sign(i_x)·Vdc·td/Tpwm).
%
%   opt 필드 (기본값): Tref_fn(@(t) 20*(t>=5e-3)), th_err(0 deg), n_delay(1), delay_comp(1),
%     td(0 s), dt_comp(0), Tpwm(1e-4), h_max(2e-6), Tstop(0.06), Kp_d/Kp_q/Ki_d/Ki_q/Kaw (단계 1 과 같음),
%     Kfw_p/Kfw_i(0 = 약자속 트림 끔, 단계 1 기준선과 같음), trace_from(Inf: 상전류 파형 기록 시작 시각),
%     ref(struct T, id, iq — 이 속도의 토크 -> 피크 전류 기준표; 비우면 S 의 MCB 표)

if nargin < 2, opt = struct(); end
d = @(f, v) getdef(opt, f, v);
Tpwm  = d('Tpwm', 1e-4);   Ts = Tpwm/2;          % 양 끝 갱신
hmax  = d('h_max', 2e-6);
Tstop = d('Tstop', 0.06);
th    = d('th_err', 0)*pi/180;
nDel  = d('n_delay', 1);
td    = d('td', 0);
dtComp = d('dt_comp', 0);
Tref_fn = d('Tref_fn', @(t) 20*(t >= 0.005));
traceFrom = d('trace_from', Inf);

m = S.machine;  we = S.we;  Rph = m.Rs_80C;  Vdc = m.Vdc;
Vmax = m.Vph_lim*sqrt(2);
Ld = 0.85e-3;  Lq = 1.6e-3;  lam = S.fd_vec(end);
Kpd = d('Kp_d', 8.50);   Kpq = d('Kp_q', 16.00);
Kid = d('Ki_d', Kpd/(Ld/Rph));   Kiq = d('Ki_q', Kpq/(Lq/Rph));
Kaw = d('Kaw', 1/(Ld/Rph));
KfwP = d('Kfw_p', 0);  KfwI = d('Kfw_i', 0);  fwMax = d('fw_max', 120);
Vtgt = d('V_target', 0.98)*Vmax;
thc = d('delay_comp', 1)*we*(nDel + 0.5)*Ts;

% 룩업 (단계 1 의 interp2 와 같은 격자·선형, 격자 밖은 가장자리 값)
Gid = griddedInterpolant({S.fq_vec, S.fd_vec}, S.id_of_flux, 'linear', 'nearest');
Giq = griddedInterpolant({S.fq_vec, S.fd_vec}, S.iq_of_flux, 'linear', 'nearest');
GT  = griddedInterpolant({S.iq_pk, S.id_pk}, S.T_shaft, 'linear', 'nearest');
GFd = griddedInterpolant({S.iq_pk, S.id_pk}, S.Fd, 'linear', 'nearest');
GFq = griddedInterpolant({S.iq_pk, S.id_pk}, S.Fq, 'linear', 'nearest');
Tv = S.T_ref_vec;  idRef = S.id_ref_current;  iqRef = S.iq_ref_current;
if isfield(opt, 'ref') && ~isempty(opt.ref)       % 기준표 교체 (단계 2b: MBC 교정표 등), 피크 A
    Tv = opt.ref.T(:);  idRef = opt.ref.id(:);  iqRef = opt.ref.iq(:);
end
clampT = @(x) min(max(x, 0), Tv(end));

% 초기 상태 = 첫 기준점, 전압은 그 정상상태 전압(평균)으로 시작
T0 = Tref_fn(0);
id0 = interp1(Tv, idRef, clampT(T0));  iq0 = interp1(Tv, iqRef, clampT(T0));
flux = [GFd(iq0, id0); GFq(iq0, id0)];
v0 = [Rph*id0 - we*flux(2); Rph*iq0 + we*flux(1)];

N = floor(Tstop/Ts);
X = complex(v0(1) - (-we*Lq*iq0), v0(2) - we*(Ld*id0 + lam));   % 적분기를 정상상태로 초기화
Xfw = 0;  Xfw_i = 0;
vab_q = repmat(rot(v0, 0), 1, nDel + 1);   % 인가 대기열 (αβ, θ=0 에서의 정상상태 전압)
pole = [0; 0; 0];                          % 실제 폴 상태 (1 = 상단)
pend = nan(3, 2);                          % 지연된 스위칭 [시각, 목표상태]

R = struct('t', zeros(N, 1), 'T', zeros(N, 1), 'Tref', zeros(N, 1), 'id', zeros(N, 1), 'iq', zeros(N, 1), ...
           'gamma', zeros(N, 1), 'Irms', zeros(N, 1), 'V', zeros(N, 1), 'sat', zeros(N, 1), ...
           'clip', zeros(N, 1), 'verr', zeros(N, 2));
tr = struct('t', [], 'ia', [], 'ib', [], 'ic', [], 'va', []);
t = 0;
for n = 1:N
    t0 = (n-1)*Ts;
    theta0 = we*t0;
    % ---------------- 샘플 (반주기 시작)
    i_dq = fluxToI(Gid, Giq, flux);
    i_ab = rot(i_dq, theta0);                     % 기계 dq -> αβ
    i_abc = clarkeInv(i_ab);
    i_meas = rot(i_ab, -(theta0 + th));           % 제어기 각도로 dq
    Tr = Tref_fn(t0);
    idr = interp1(Tv, idRef, clampT(Tr));  iqr = interp1(Tv, iqRef, clampT(Tr));
    % ---------------- 제어기 (단계 1 'pi_dec' 와 같음)
    idc = idr - Xfw;
    ed = idc - i_meas(1);  eq = iqr - i_meas(2);
    vu = complex(Kpd*ed, Kpq*eq) + X + complex(-we*Lq*i_meas(2), we*(Ld*i_meas(1) + lam));
    vmag = abs(vu);
    if vmag > Vmax, vs = vu*Vmax/vmag; sat = 1; else, vs = vu; sat = 0; end
    X = X + Ts*(complex(Kid*ed, Kiq*eq) + Kaw*(vs - vu));
    Xfw_i = min(max(0, Xfw_i + Ts*KfwI*(vmag - Vtgt)), fwMax);
    Xfw = min(max(0, Xfw_i + KfwP*(vmag - Vtgt)), fwMax);
    vc = vs*exp(1i*thc);                          % 지연 보상
    vab_cmd = rot([real(vc); imag(vc)], theta0 + th);   % 제어기 각도로 αβ (이 샘플 시점의 각도)
    vab_q = [vab_q(:, 2:end), vab_cmd];
    vab_app = vab_q(:, 1);                        % n_delay 샘플 전에 계산된 지령
    % ---------------- 변조 (SVPWM: min-max 영상분 주입)
    vabc = clarkeInv(vab_app);
    vzs = -(max(vabc) + min(vabc))/2;
    duty = 0.5 + (vabc + vzs)/Vdc;
    if dtComp && td > 0
        % 밀리는 에지는 반주기마다 한 번이 아니라 캐리어 주기마다 한 번이다:
        % i > 0 이면 상승 반주기의 켜짐 에지, i < 0 이면 하강 반주기의 꺼짐 에지만 td 늦는다.
        % 그 반주기에서만 듀티를 td/Ts 만큼 보정한다 (주기 평균 = sign(i)·Vdc·td/Tpwm).
        % (09-23 초판은 매 반주기 sign(i)·Vdc·td/Ts 를 더해 2 배 과보상이었다.)
        if mod(n-1, 2) == 0
            duty = duty + (i_abc > 0)*td/Ts;
        else
            duty = duty - (i_abc < 0)*td/Ts;
        end
    end
    clip = any(duty < 0 | duty > 1);
    duty = min(max(duty, 0), 1);
    rising = mod(n-1, 2) == 0;                    % 짝수 반주기: 카운터 상승 -> (1-d)Ts 에 상단 ON
    % 지령 스위칭 목록 [시각, 상, 목표상태]
    ev = zeros(0, 3);
    for x = 1:3
        if rising
            s0 = double(duty(x) >= 1);  te = t0 + (1 - duty(x))*Ts;
            ev = [ev; t0, x, s0];                              %#ok<AGROW>  반주기 시작 상태
            if duty(x) > 0 && duty(x) < 1, ev = [ev; te, x, 1]; end %#ok<AGROW>
        else
            s0 = double(duty(x) > 0);   te = t0 + duty(x)*Ts;
            ev = [ev; t0, x, s0];                              %#ok<AGROW>
            if duty(x) > 0 && duty(x) < 1, ev = [ev; te, x, 0]; end %#ok<AGROW>
        end
    end
    ev = sortrows(ev, 1);
    tEnd = t0 + Ts;
    % ---------------- 사건 구동 적분 (지령 사건 + 데드타임으로 밀린 사건)
    Tacc = 0;  Vacc = [0; 0];
    k = 1;
    while true
        tNextCmd = inf;  if k <= size(ev, 1), tNextCmd = ev(k, 1); end
        [tNextPend, xp] = min(pend(:, 1));
        if isnan(tNextPend), tNextPend = inf; end
        tNext = min([tNextCmd, tNextPend, tEnd]);
        % 현재 폴 상태로 tNext 까지 적분
        if tNext > t
            [flux, Tseg, Vseg] = integrate(Gid, Giq, GT, flux, pole, Vdc, Rph, we, t, tNext, hmax);
            Tacc = Tacc + Tseg;  Vacc = Vacc + Vseg;
            if t >= traceFrom
                ia = clarkeInv(rot(fluxToI(Gid, Giq, flux), we*tNext));
                tr.t(end+1) = tNext; tr.ia(end+1) = ia(1); tr.ib(end+1) = ia(2); tr.ic(end+1) = ia(3); %#ok<AGROW>
                tr.va(end+1) = Vdc*(pole(1) - mean(pole));                                                 %#ok<AGROW>
            end
            t = tNext;
        end
        if tNext >= tEnd && tNextCmd > tEnd && tNextPend > tEnd, break; end
        if tNextPend <= tNextCmd && tNextPend < inf && tNextPend <= tEnd
            pole(xp) = pend(xp, 2);  pend(xp, :) = nan;     % 밀린 스위칭 실행
            continue
        end
        if tNextCmd <= tEnd && k <= size(ev, 1)
            x = ev(k, 2);  sNew = ev(k, 3);  k = k + 1;
            if ~isnan(pend(x, 1))                 % 아직 실행 안 된 밀린 스위칭이 있으면 목표만 갱신
                if sNew == pole(x), pend(x, :) = nan; else, pend(x, 2) = sNew; end
                continue
            end
            if sNew == pole(x), continue; end
            if td > 0
                ix = clarkeInv(rot(fluxToI(Gid, Giq, flux), we*t));
                delayed = (sNew == 1 && ix(x) > 0) || (sNew == 0 && ix(x) < 0);
                if delayed, pend(x, :) = [t + td, sNew]; continue; end
            end
            pole(x) = sNew;
            continue
        end
        if tNext >= tEnd, break; end
    end
    % ---------------- 기록 (반주기 평균 토크, 반주기 끝 전류)
    i_end = fluxToI(Gid, Giq, flux);
    R.t(n) = t0;  R.Tref(n) = Tr;  R.T(n) = Tacc/Ts;
    R.id(n) = i_end(1);  R.iq(n) = i_end(2);
    R.gamma(n) = atan2d(-i_end(1), i_end(2));
    R.Irms(n) = hypot(i_end(1), i_end(2))/sqrt(2);
    R.V(n) = abs(vs)/sqrt(2);  R.sat(n) = sat;  R.clip(n) = clip;
    % 진단: 반주기 평균 인가 αβ 전압 - 지령 αβ 전압 (td = 0, 비포화면 0 이어야 한다)
    R.verr(n, :) = (Vacc/Ts - vab_app).';
end
R.trace = tr;
R.opt = struct('Tpwm', Tpwm, 'Ts', Ts, 'h_max', hmax, 'th_err_deg', th*180/pi, 'n_delay', nDel, ...
               'td', td, 'dt_comp', dtComp, 'delay_comp_deg', thc*180/pi, 'Vmax_peak', Vmax);
end

% ------------------------------------------------------------------ helpers
function [flux, Tint, Vint] = integrate(Gid, Giq, GT, flux, pole, Vdc, Rph, we, ta, tb, hmax)
% 폴 상태 고정 구간 [ta, tb] 적분. 상전압(중성점 부동) -> αβ 는 고정, dq 는 회전각으로 변한다.
vp = Vdc*(pole - 0.5);
vn = vp - mean(vp);
vab = [vn(1); (vn(2) - vn(3))/sqrt(3)];
L = tb - ta;  ns = max(1, ceil(L/hmax));  h = L/ns;  tt = ta;
Tint = 0;  Vint = vab*L;
for s = 1:ns
    k1 = fdot(Gid, Giq, flux,          vab, Rph, we, tt);
    k2 = fdot(Gid, Giq, flux + h/2*k1, vab, Rph, we, tt + h/2);
    k3 = fdot(Gid, Giq, flux + h/2*k2, vab, Rph, we, tt + h/2);
    k4 = fdot(Gid, Giq, flux + h*k3,   vab, Rph, we, tt + h);
    fnew = flux + h/6*(k1 + 2*k2 + 2*k3 + k4);
    i1 = fluxToI(Gid, Giq, flux);  i2 = fluxToI(Gid, Giq, fnew);
    Tint = Tint + h/2*(GT(i1(2), i1(1)) + GT(i2(2), i2(1)));
    flux = fnew;  tt = tt + h;
end
end

function df = fdot(Gid, Giq, f, vab, Rph, we, t)
i = fluxToI(Gid, Giq, f);
v = rot(vab, -we*t);
df = [v(1) - Rph*i(1) + we*f(2);
      v(2) - Rph*i(2) - we*f(1)];
end

function i = fluxToI(Gid, Giq, f)
i = [Gid(f(2), f(1)); Giq(f(2), f(1))];
end

function y = rot(u, th)
c = cos(th); s = sin(th);
y = [c*u(1) - s*u(2); s*u(1) + c*u(2)];
end

function abc = clarkeInv(ab)
abc = [ab(1); -ab(1)/2 + sqrt(3)/2*ab(2); -ab(1)/2 - sqrt(3)/2*ab(2)];
end

function v = getdef(s, f, dflt)
if isfield(s, f) && ~isempty(s.(f)), v = s.(f); else, v = dflt; end
end
