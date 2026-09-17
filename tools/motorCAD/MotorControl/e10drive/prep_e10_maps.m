function out = prep_e10_maps(saveDir)
%PREP_E10_MAPS  e10 기준기 dq 맵을 구동 모델용으로 정리하고 검증 앵커를 확인한다.
%
%   원본: D:\KangDH\Thesis\e10\refModel\e10Turn6V261_SyreMMM_B.mat  (SyR-e 규약)
%     FluxMap_dq       : Id, Iq, Fd, Fq, T, dTpp  (255x255) + Pac_*_kW(255x255x4), speed_vec
%     IronPMLossMap_dq : Pfes_h/c, Pfer_h/c, Ppm (n0 기준) + 주파수 지수 expH/expC/expPM
%
%   축 규약 (2026-09-17 확인): 배열은 M(iq, id) 이다. Id 는 열 방향으로 -460~0 Apk,
%   Iq 는 행 방향으로 0~460 Apk (한 사분면: 전동 + 약자속). id = 0 열은 통째로 NaN.
%   interp2(idVec, iqVec, M, id, iq) 규약에 그대로 맞는다.
%
%   하는 일: 표 정리 -> Ld/Lq 표 -> 검증 앵커 확인 -> e10_dq_maps.mat 저장.
%   앵커는 PC1 이 Motor-CAD Lab 에서 따로 얻은 값이다(gamma_highspeed_report.html 6.6 절).
%   맵이 같은 기계를 가리키는지 먼저 걸러야 모델을 만들 의미가 있다.

if nargin < 1 || isempty(saveDir)
    saveDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive';
end
if ~isfolder(saveDir), mkdir(saveDir); end

src = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_SyreMMM_B.mat';
S = load(src);
F = S.FluxMap_dq;
L = S.IronPMLossMap_dq;

% ---- 기계 상수 (제원 정본)
m = struct('p', 4, 'Vdc', 720, 'Vph_lim', 285.1, 'Rs_80C', 0.0786, ...
           'R_active', 0.0495, 'R_end', 0.0291, 'n_rated', 16000, 'I_rated_rms', 460);

% ---- 격자 (Apk).  M(iq, id)
idVec = F.Id(1, :);
iqVec = F.Iq(:, 1).';
assert(max(abs(diff(F.Id, 1, 1)), [], 'all') == 0, 'Id 가 행 방향으로 변한다');
assert(max(abs(diff(F.Iq, 1, 2)), [], 'all') == 0, 'Iq 가 열 방향으로 변한다');

out = struct();
out.id_pk = idVec;  out.iq_pk = iqVec;
out.Fd = F.Fd;  out.Fq = F.Fq;  out.T = F.T;  out.dTpp = F.dTpp;
out.Pac_kW = F.Pac_total_kW;  out.Pac_prox_kW = F.Pac_prox_kW;  out.Pac_skin_kW = F.Pac_skin_kW;
out.Pac_speed = F.speed_vec;
out.iron = struct('Pfes_h', L.Pfes_h, 'Pfes_c', L.Pfes_c, 'Pfer_h', L.Pfer_h, 'Pfer_c', L.Pfer_c, ...
                  'Ppm', L.Ppm, 'n0', L.n0, 'f0', L.f0, 'expH', L.expH, 'expC', L.expC, 'expPM', L.expPM);
out.machine = m;
out.source = src;
out.axis_note = 'M(iq, id); Id -460..0 Apk (열), Iq 0..460 Apk (행)';

[IDm, IQm] = meshgrid(idVec, iqVec);
nanFrac = 100*nnz(~isfinite(out.Fd))/numel(out.Fd);

% ---- PM 자속: id = 0 열이 NaN 이므로 iq = 0 행에서 id 축으로 외삽
lam_m = interp2(idVec, iqVec, out.Fd, 0, 0, 'linear', NaN);
if ~isfinite(lam_m)
    v = out.Fd(1, :);  g = isfinite(v);
    lam_m = interp1(idVec(g), v(g), 0, 'linear', 'extrap');
end
out.lambda_m = lam_m;

% ---- Ld/Lq 표 (FEM-Parameterized PMSM sinusoidalBackEMF 파라미터화용)
out.Ld = (out.Fd - lam_m) ./ IDm;  out.Ld(IDm == 0) = NaN;
out.Lq = out.Fq ./ IQm;            out.Lq(IQm == 0) = NaN;

fprintf('\n===== e10 dq 맵 (255x255, 한 사분면) =====\n');
fprintf('Id %.0f~%.0f Apk, Iq %.0f~%.0f Apk, 결측 %.1f %%\n', ...
        min(idVec), max(idVec), min(iqVec), max(iqVec), nanFrac);

% ================================================================= 검증 앵커
a = struct();
we = 2*pi*m.n_rated/60*m.p;
% 정상상태 단자 전압: vd = R id - we Fq,  vq = R iq + we Fd  (저항 강하 포함)
Vrms = hypot(m.Rs_80C*IDm - we*out.Fq, m.Rs_80C*IQm + we*out.Fd)/sqrt(2);
Irms = hypot(IDm, IQm)/sqrt(2);
gam  = atan2d(-IDm, IQm);

fprintf('\n===== 검증 앵커 (Lab 값 대비) =====\n');

a.lambda_m = lam_m;
fprintf('1) PM 자속        %.4f Vs      | Lab 0.2204 Vs   차이 %+.1f %%\n', lam_m, 100*(lam_m/0.2204-1));

a.bemf_rms = we*lam_m/sqrt(2);
fprintf('2) 16 krpm 역기전력 %.0f V rms  | Lab 1042 V      한계 %.1f V 의 %.1f 배\n', ...
        a.bemf_rms, m.Vph_lim, a.bemf_rms/m.Vph_lim);

Tem = 1.5*m.p*(out.Fd.*IQm - out.Fq.*IDm);
msk = isfinite(out.T) & isfinite(Tem) & abs(out.T) > 20;
a.torque_rel_err_pct = 100*median(abs(Tem(msk)-out.T(msk))./abs(out.T(msk)));
fprintf('3) T 대 1.5p(Fd iq-Fq id)      | 중앙 오차 %.2f %% (%d 점)\n', a.torque_rel_err_pct, nnz(msk));

feas = isfinite(Vrms) & Vrms <= m.Vph_lim & out.T > 0 & Irms <= m.I_rated_rms;
a.gamma_min_feasible = min(gam(feas));
a.Tmax_16k = max(out.T(feas));
[~, kT] = max(out.T(:).*feas(:));
a.Tmax_I_rms = Irms(kT);  a.Tmax_gamma = gam(kT);
fprintf('4) 16 krpm 가능 최소 진각      | %.1f°  | 최대 토크 %.1f N·m (γ %.1f°, %.0f A rms) | Lab 88.0 N·m, 85.2°, 204 A\n', ...
        a.gamma_min_feasible, a.Tmax_16k, a.Tmax_gamma, a.Tmax_I_rms);

a.opt = local_min_loss_contour(out, m, we, 1.0);
fprintf('5) 16 krpm 1 N·m 손실 최소     | gamma %.2f°, I %.1f A rms, V %.0f V | Lab 89.70°, 135.6 A, 277 V\n', ...
        a.opt.gamma_deg, a.opt.I_rms, a.opt.V_rms);

a.dTdg_138 = arrayfun(@(g) local_dTdg(out, 138*sqrt(2), g), [70 80 85]);
fprintf('6) dT/dgamma @138 A rms        | 70° %.1f, 80° %.1f, 85° %.1f N·m/°  | Lab -8.5 / -10.4 / -10.9\n', ...
        a.dTdg_138(1), a.dTdg_138(2), a.dTdg_138(3));

a.split = struct('Pcu_dc', a.opt.Pcu, 'Pcu_ac', a.opt.Pac, 'Pfe', a.opt.Pfe, 'Ppm', a.opt.Ppm);
fprintf('+) 손실 분해 @최소점           | DC %.2f + AC %.2f + 철손 %.2f kW | Lab 4.3 / 2.8 / 2.7 (0.44 N·m 점)\n', ...
        a.split.Pcu_dc/1e3, a.split.Pcu_ac/1e3, a.split.Pfe/1e3);

% 특성전류: d 축 자속이 0 이 되는 전류 (전압 한계가 무엇을 강제하는지 보는 값)
v = out.Fd(1, :);  g = isfinite(v);
a.I_char_pk = interp1(v(g), idVec(g), 0, 'linear');
fprintf('+) 특성전류 (Fd = 0)           | %.0f Apk = %.0f A rms | Lab 최적점 전류 135.6 A rms\n', ...
        abs(a.I_char_pk), abs(a.I_char_pk)/sqrt(2));

out.anchors = a;
f = fullfile(saveDir, 'e10_dq_maps.mat');
save(f, '-struct', 'out', '-v7.3');
fprintf('\n-> %s\n', f);
end

% ------------------------------------------------------------------ helpers
function s = local_min_loss_contour(out, m, we, Tdem)
%  진각을 훑으며 요구 토크를 내는 전류를 보간으로 정확히 풀고(격자 톨러런스 없이),
%  전압 한계를 지키는 점 중 총손실 최소를 고른다.
nr = m.n_rated/out.iron.n0;
Pfe_map = (out.iron.Pfes_h + out.iron.Pfer_h)*nr^out.iron.expH + ...
          (out.iron.Pfes_c + out.iron.Pfer_c)*nr^out.iron.expC;
Ppm_map = out.iron.Ppm*nr^out.iron.expPM;
kSpd = interp1(out.Pac_speed, 1:numel(out.Pac_speed), m.n_rated, 'nearest');
Pac_map = out.Pac_kW(:, :, kSpd)*1e3;
best = struct('Ptot', inf);
Ipk = linspace(5, 650, 2000);
for g = 60:0.1:89.9
    id = -Ipk*sind(g);  iq = Ipk*cosd(g);
    T = interp2(out.id_pk, out.iq_pk, out.T, id, iq, 'linear', NaN);
    k = find(isfinite(T(1:end-1)) & isfinite(T(2:end)) & ...
             (T(1:end-1)-Tdem).*(T(2:end)-Tdem) <= 0, 1);
    if isempty(k), continue; end
    f = (Tdem - T(k))/(T(k+1) - T(k));
    Ip = Ipk(k) + f*(Ipk(k+1) - Ipk(k));
    idq = -Ip*sind(g);  iqq = Ip*cosd(g);
    Fd = interp2(out.id_pk, out.iq_pk, out.Fd, idq, iqq, 'linear', NaN);
    Fq = interp2(out.id_pk, out.iq_pk, out.Fq, idq, iqq, 'linear', NaN);
    V = hypot(m.Rs_80C*idq - we*Fq, m.Rs_80C*iqq + we*Fd)/sqrt(2);
    if ~isfinite(V) || V > m.Vph_lim, continue; end
    I_rms = Ip/sqrt(2);
    Pcu = 3*m.Rs_80C*I_rms^2;
    Pac = interp2(out.id_pk, out.iq_pk, Pac_map, idq, iqq, 'linear', NaN);
    Pfe = interp2(out.id_pk, out.iq_pk, Pfe_map, idq, iqq, 'linear', NaN);
    Ppm = interp2(out.id_pk, out.iq_pk, Ppm_map, idq, iqq, 'linear', NaN);
    tot = Pcu + max(Pac, 0) + max(Pfe, 0) + max(Ppm, 0);
    if isfinite(tot) && tot < best.Ptot
        best = struct('gamma_deg', g, 'I_rms', I_rms, 'T', Tdem, 'V_rms', V, ...
                      'Pcu', Pcu, 'Pac', Pac, 'Pfe', Pfe, 'Ppm', Ppm, 'Ptot', tot);
    end
end
s = best;
end

function g = local_dTdg(out, Ipk, gamma_deg)
dg = 1;
T1 = local_T_at(out, Ipk, gamma_deg - dg/2);
T2 = local_T_at(out, Ipk, gamma_deg + dg/2);
g = (T2 - T1)/dg;
end

function T = local_T_at(out, Ipk, gamma_deg)
T = interp2(out.id_pk, out.iq_pk, out.T, -Ipk*sind(gamma_deg), Ipk*cosd(gamma_deg), 'linear', NaN);
end
