function S = prep_e10_stage1(speed_rpm, workDir)
%PREP_E10_STAGE1  단계 1(평균값 dq) 모델이 쓸 표를 만든다.
%
%   입력: e10_plant_lab.mat (prep_e10_maps_lab 산출물, Motor-CAD Lab Saturation & Loss Map)
%   출력: e10_stage1_data.mat + 같은 내용을 반환
%
%   만드는 것
%     1) 역맵 id(λd, λq), iq(λd, λq)  — 플랜트 상태가 자속이므로 필요하다
%     2) 그 격자 위의 토크·손실 (플랜트 출력)
%     3) 제어기 기준표: 요구 축 토크 -> (id*, iq*)  (전압 한계 아래 총손실 최소)
%     4) 제동 토크(철손·자석손) 표
%
%   자속 격자는 전류 격자에서 스캐터 보간으로 만든다. 자속면이 접히지 않는 영역
%   (id <= 0, iq >= 0) 만 쓰므로 일대일 대응이 성립한다.

if nargin < 1 || isempty(speed_rpm), speed_rpm = 16000; end
if nargin < 2 || isempty(workDir),  workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end

P = load(fullfile(workDir, 'e10_plant_lab.mat'));
m = P.machine;
kS = find(P.speeds == speed_rpm, 1);
assert(~isempty(kS), '속도 %g rpm 의 손실 맵이 없다 (있는 것: %s)', speed_rpm, mat2str(P.speeds));
we = 2*pi*speed_rpm/60*m.p;
wm = 2*pi*speed_rpm/60;

% 역맵 정확도를 위해 정방향 맵을 먼저 조밀하게 깐다 (원 격자 13 Apk -> 3.25 Apk)
idF = linspace(P.id_pk(1), P.id_pk(end), 4*numel(P.id_pk)-3);
iqF = linspace(P.iq_pk(1), P.iq_pk(end), 4*numel(P.iq_pk)-3);
[ID, IQ] = meshgrid(idF, iqF);
FD = interp2(P.id_pk, P.iq_pk, P.Fd, ID, IQ, 'spline');
FQ = interp2(P.id_pk, P.iq_pk, P.Fq, ID, IQ, 'spline');

% ---- 1) 역맵: (λd, λq) -> (id, iq)
nF = 241;
fdVec = linspace(min(FD(:)), max(FD(:)), nF);
fqVec = linspace(min(FQ(:)), max(FQ(:)), nF);
[FDq, FQq] = meshgrid(fdVec, fqVec);
Fid = scatteredInterpolant(FD(:), FQ(:), ID(:), 'linear', 'linear');
Fiq = scatteredInterpolant(FD(:), FQ(:), IQ(:), 'linear', 'linear');
S.fd_vec = fdVec;  S.fq_vec = fqVec;
S.id_of_flux = Fid(FDq, FQq);
S.iq_of_flux = Fiq(FDq, FQq);

% 왕복 검사: 전류 -> 자속 -> 전류 (자속 사각형의 모서리는 맵 밖이라 제외한다)
idBack = interp2(fdVec, fqVec, S.id_of_flux, FD, FQ, 'linear');
iqBack = interp2(fdVec, fqVec, S.iq_of_flux, FD, FQ, 'linear');
ok = isfinite(idBack) & isfinite(iqBack);
e_id = abs(idBack(ok) - ID(ok));  e_iq = abs(iqBack(ok) - IQ(ok));
S.roundtrip_id_max = max(e_id);   S.roundtrip_iq_max = max(e_iq);
S.roundtrip_id_p99 = prctile(e_id, 99);  S.roundtrip_iq_p99 = prctile(e_iq, 99);
% 자속 격자 중 실제 운전 영역(정방향 맵의 볼록포 안) 표시 — 모델에서 밖이면 경고
inHull = isfinite(interp2(idF, iqF, FD, Fid(FDq, FQq), Fiq(FDq, FQq), 'linear'));
S.flux_valid = inHull;

% ---- 2) 플랜트 출력표 (전류 격자 그대로 둔다 — 모델에서 2-D 룩업)
S.id_pk = P.id_pk;  S.iq_pk = P.iq_pk;
S.T_em = P.T;
S.T_drag = (P.Pfe(:, :, kS) + P.Pmag(:, :, kS))/wm;     % 제동 토크 [N·m]
S.T_shaft = P.Tshaft(:, :, kS);
S.Pcu_ac = P.Pac(:, :, kS);
S.Pfe = P.Pfe(:, :, kS);
S.Pmag = P.Pmag(:, :, kS);
S.V_map = P.Vrms(:, :, kS);
S.Fd = P.Fd;  S.Fq = P.Fq;          % 원 격자(id_pk, iq_pk) 기준으로 저장한다
S.Fd_fine = FD; S.Fq_fine = FQ; S.idF = idF; S.iqF = iqF;

S.Vmargin = 0.95;   % 기준표는 전압 여유를 두고 만든다 (폐루프가 약자속 트림을 할 여지)
% ---- 3) 제어기 기준표: 요구 축 토크 -> (id*, iq*), 전압 한계 아래 총손실 최소
% 전압 한계 아래 최대 축 토크 — 임계선 위에 얹히므로 조밀 보간으로 찾는다 (노드만 쓰면 과소평가)
idD = linspace(P.id_pk(1), P.id_pk(end), 1301);
iqD = linspace(P.iq_pk(1), P.iq_pk(end), 1301);
[IDd, IQd] = meshgrid(idD, iqD);
Td = interp2(S.id_pk, S.iq_pk, S.T_shaft, IDd, IQd, 'linear');
Vd = interp2(S.id_pk, S.iq_pk, S.V_map,   IDd, IQd, 'linear');
Tmax = max(Td(Vd <= m.Vph_lim*S.Vmargin & hypot(IDd, IQd)/sqrt(2) <= m.I_rated_rms), [], 'all');
S.T_ref_vec = [0, logspace(log10(0.5), log10(max(Tmax*0.995, 1)), 60)];
% 두 가지 목적함수로 만든다. Lab 의 제어전략 0(최대토크/암페어)에 대응하는 것은 'current' 이고,
% 'loss' 는 이 스레드가 묻는 총손실 최소다. 둘의 차이가 곧 '교류손을 넣으면 진각이 얼마나 움직이나'다.
for obj = {'current', 'loss'}
    o = obj{1};
    idv = zeros(size(S.T_ref_vec));  iqv = idv;  gmv = idv;  Iv = idv;  Vv = idv;  Pv = idv;
    for k = 2:numel(S.T_ref_vec)
        b = local_opt(S, m, S.T_ref_vec(k), o);
        if isempty(b)
            idv(k) = idv(k-1);  iqv(k) = iqv(k-1);  gmv(k) = gmv(k-1);
            Iv(k) = Iv(k-1);  Vv(k) = Vv(k-1);  Pv(k) = Pv(k-1);
        else
            idv(k) = b.id;  iqv(k) = b.iq;  gmv(k) = b.gamma;
            Iv(k) = b.I_rms;  Vv(k) = b.V;  Pv(k) = b.P;
        end
    end
    idv(1) = idv(2);  iqv(1) = 0;  gmv(1) = 90;  Iv(1) = Iv(2);  Vv(1) = Vv(2);  Pv(1) = Pv(2);
    S.(['fd_ref_' o]) = interp2(S.id_pk, S.iq_pk, S.Fd, idv, iqv, 'linear');
    S.(['fq_ref_' o]) = interp2(S.id_pk, S.iq_pk, S.Fq, idv, iqv, 'linear');
    S.(['id_ref_' o]) = idv;  S.(['iq_ref_' o]) = iqv;  S.(['gamma_ref_' o]) = gmv;
    S.(['I_ref_' o]) = Iv;    S.(['V_ref_' o]) = Vv;    S.(['P_ref_' o]) = Pv;
end
S.id_ref = S.id_ref_current;  S.iq_ref = S.iq_ref_current;  S.gamma_ref = S.gamma_ref_current;

S.speed_rpm = speed_rpm;  S.we = we;  S.wm = wm;  S.machine = m;
S.Tmax_shaft = Tmax;
S.source = fullfile(workDir, 'e10_plant_lab.mat');

fprintf('\n===== 단계 1 표 (%g rpm) =====\n', speed_rpm);
fprintf('역맵 왕복 오차: id %.2f Apk, iq %.2f Apk (격자 간격 %.0f Apk)\n', ...
        S.roundtrip_id_max, S.roundtrip_iq_max, P.id_pk(2)-P.id_pk(1));
fprintf('전압 한계 아래 최대 축 토크 %.1f N·m, 기준표 %d 점\n', Tmax, numel(S.T_ref_vec));
fprintf('기준표 예: T* %5.1f -> id %7.1f, iq %6.1f, γ %5.2f°\n', ...
        [S.T_ref_vec([2 10 30 50 end]); S.id_ref([2 10 30 50 end]); ...
         S.iq_ref([2 10 30 50 end]); S.gamma_ref([2 10 30 50 end])]);

f = fullfile(workDir, sprintf('e10_stage1_data_%d.mat', speed_rpm));
save(f, '-struct', 'S');
fprintf('-> %s\n', f);
end

function best = local_opt(S, m, Tdem, obj)
%  진각을 훑어 요구 축 토크를 내는 전류를 찾고, 전압 한계 아래에서
%  obj='current' 면 전류 최소(= Lab 제어전략 0), obj='loss' 면 총손실 최소를 고른다.
if nargin < 4, obj = 'loss'; end
best = [];  bestP = inf;
Ipk = linspace(5, 650, 1500);
for g = 0:0.25:89.95
    id = -Ipk*sind(g);  iq = Ipk*cosd(g);
    T = interp2(S.id_pk, S.iq_pk, S.T_shaft, id, iq, 'linear', NaN);
    ks = find(isfinite(T(1:end-1)) & isfinite(T(2:end)) & (T(1:end-1)-Tdem).*(T(2:end)-Tdem) <= 0);
    for k = ks(:).'
        f = (Tdem - T(k))/(T(k+1) - T(k));
        Ip = Ipk(k) + f*(Ipk(k+1) - Ipk(k));
        idq = -Ip*sind(g);  iqq = Ip*cosd(g);
        V = interp2(S.id_pk, S.iq_pk, S.V_map, idq, iqq, 'linear', NaN);
        if ~isfinite(V) || V > m.Vph_lim*S.Vmargin, continue; end
        Irms = Ip/sqrt(2);
        if Irms > m.I_rated_rms, continue; end
        P = 3*m.Rs_80C*Irms^2 ...
            + max(interp2(S.id_pk, S.iq_pk, S.Pcu_ac, idq, iqq, 'linear', NaN), 0) ...
            + max(interp2(S.id_pk, S.iq_pk, S.Pfe,    idq, iqq, 'linear', NaN), 0) ...
            + max(interp2(S.id_pk, S.iq_pk, S.Pmag,   idq, iqq, 'linear', NaN), 0);
        cost = P;
        if strcmp(obj, 'current'), cost = Irms; end
        if isfinite(cost) && cost < bestP
            bestP = cost;
            best = struct('id', idq, 'iq', iqq, 'gamma', g, 'I_rms', Irms, 'V', V, 'P', P);
        end
    end
end
end
