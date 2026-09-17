function out = prep_e10_maps_lab(workDir)
%PREP_E10_MAPS_LAB  Motor-CAD Lab 의 Saturation & Loss Map export 로 구동 모델 플랜트 표를 만든다.
%
%   입력: export_lab_satmap.py 가 만든 e10_satloss_<speed>.mat (기준기 e10Turn6V261)
%     Tools -> Saturation and Loss Maps,  Input Definition = D/Q Axis Currents,
%     Calculation Method = Interpolate Lab Model (빌드된 Lab 모델 보간, FEA 재실행 없음)
%     51x51 격자: Id -650~0 Apk, Iq 0~650 Apk, 결측 없음.
%
%   축 규약 (2026-09-17 확인): 이 파일의 배열은 M(id, iq) 이다 — SyR-e 맵(M(iq, id))과 반대다.
%   여기서는 interp2 규약에 맞게 M(iq, id) 로 전치해 저장한다.
%
%   속도 의존: 자속·토크·인덕턴스는 속도와 무관하고, 손실(교류 동손·철손·자석손)만 속도별이다.
%   그래서 손실은 속도 축을 하나 더 갖는 3-D 배열로 쌓는다.
%
%   왜 SyR-e 맵 대신 이것인가: 이 스레드의 진각 결론·검증 앵커가 전부 Lab 모델에서 나왔다.
%   플랜트도 같은 모델에서 뽑아야 앵커가 모델 검증으로 기능한다(사용자 지시, 09-17).

if nargin < 1 || isempty(workDir)
    workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive';
end
files = dir(fullfile(workDir, 'e10_satloss_*.mat'));
assert(~isempty(files), 'export_lab_satmap.py 산출물이 없다: %s', workDir);

m = struct('p', 4, 'Vdc', 720, 'Vph_lim', 285.1, 'Rs_80C', 0.0786, ...
           'R_active', 0.0495, 'R_end', 0.0291, 'n_rated', 16000, 'I_rated_rms', 460);

speeds = zeros(1, numel(files));
for k = 1:numel(files)
    speeds(k) = sscanf(files(k).name, 'e10_satloss_%d.mat');
end
[speeds, ord] = sort(speeds);  files = files(ord);

out = struct();
for k = 1:numel(files)
    S = load(fullfile(workDir, files(k).name));
    if k == 1
        idVec = S.Id_Peak(:, 1).';          % 행 방향으로 변한다 -> 전치해서 쓴다
        iqVec = S.Iq_Peak(1, :);
        assert(max(abs(diff(S.Id_Peak, 1, 2)), [], 'all') == 0, 'Id 가 열 방향으로 변한다');
        out.id_pk = idVec;  out.iq_pk = iqVec;
        out.Fd = S.Flux_Linkage_D.';  out.Fq = S.Flux_Linkage_Q.';
        out.T  = S.Electromagnetic_Torque.';
        out.Ld = S.Ld.'*1e-3;  out.Lq = S.Lq.'*1e-3;   % Motor-CAD 는 mH
        out.PM = S.PM_Flux_Linkage.';
        out.dTpp = S.Torque_Ripple_Peak_to_Peak.';
        out.lambda_m = interp2(idVec, iqVec, out.Fd, 0, 0, 'linear', NaN);
        nS = numel(files);
        out.Pac  = zeros([size(out.Fd), nS]);
        out.Pfe  = zeros([size(out.Fd), nS]);
        out.Pfe_s = zeros([size(out.Fd), nS]);
        out.Pfe_r = zeros([size(out.Fd), nS]);
        out.Pmag = zeros([size(out.Fd), nS]);
        out.Pcu_dc = zeros([size(out.Fd), nS]);
        out.Vrms = zeros([size(out.Fd), nS]);
    else
        assert(max(abs(S.Flux_Linkage_D.' - out.Fd), [], 'all') < 1e-9, ...
               '속도 %d 의 자속이 다르다 - 같은 모델이 아니다', speeds(k));
    end
    out.Pac(:, :, k)  = S.Stator_Copper_Loss_AC.';
    out.Pfe(:, :, k)  = S.Iron_Loss.';
    out.Pfe_s(:, :, k) = S.Iron_Loss_Stator.';
    out.Pfe_r(:, :, k) = S.Iron_Loss_Rotor.';
    out.Pmag(:, :, k) = S.Magnet_Loss.';
    out.Pcu_dc(:, :, k) = S.Stator_Copper_Loss_DC.';
    out.Vrms(:, :, k) = S.Voltage_Phase_RMS.';
end
out.speeds = speeds;
out.machine = m;
out.source = fullfile(workDir, 'e10_satloss_*.mat');
out.axis_note = 'M(iq, id) 로 전치해 저장 (원본 export 는 M(id, iq))';

[IDm, IQm] = meshgrid(out.id_pk, out.iq_pk);
we = 2*pi*m.n_rated/60*m.p;
kR = find(speeds == m.n_rated, 1);

fprintf('\n===== Motor-CAD Lab Saturation & Loss Map =====\n');
fprintf('격자 %dx%d, Id %.0f~%.0f Apk, Iq %.0f~%.0f Apk, 속도 %s rpm, 결측 %.1f %%\n', ...
        numel(out.id_pk), numel(out.iq_pk), min(out.id_pk), max(out.id_pk), ...
        min(out.iq_pk), max(out.iq_pk), mat2str(speeds), ...
        100*nnz(~isfinite(out.Fd))/numel(out.Fd));

% ================================================================= 검증 앵커
a = struct();
fprintf('\n===== 검증 앵커 (Lab 운전점 값 대비) =====\n');

a.lambda_m = out.lambda_m;
fprintf('1) PM 자속        %.4f Vs      | Lab 운전점 0.2204 Vs   차이 %+.1f %%\n', ...
        a.lambda_m, 100*(a.lambda_m/0.2204-1));

a.bemf_rms = we*a.lambda_m/sqrt(2);
fprintf('2) 16 krpm 역기전력 %.0f V rms  | Lab 1042 V   한계 %.1f V 의 %.1f 배\n', ...
        a.bemf_rms, m.Vph_lim, a.bemf_rms/m.Vph_lim);

Tem = 1.5*m.p*(out.Fd.*IQm - out.Fq.*IDm);
msk = abs(out.T) > 20;
a.torque_rel_err_pct = 100*median(abs(Tem(msk)-out.T(msk))./abs(out.T(msk)));
fprintf('3) T 대 1.5p(Fd iq-Fq id)      | 중앙 오차 %.2f %% (%d 점)\n', a.torque_rel_err_pct, nnz(msk));

% 단자 전압: export 값(Voltage_Phase_RMS)과 정상상태식 비교 후 식을 쓴다
Vcalc = hypot(m.Rs_80C*IDm - we*out.Fq, m.Rs_80C*IQm + we*out.Fd)/sqrt(2);
VR = out.Vrms(:, :, kR);
a.V_export_vs_calc_pct = 100*median(abs(Vcalc(msk) - VR(msk)) ./ max(VR(msk), 1));
Irms = hypot(IDm, IQm)/sqrt(2);
gam = atan2d(-IDm, IQm);
feas = Vcalc <= m.Vph_lim & out.T > 0 & Irms <= m.I_rated_rms;
a.gamma_min_feasible = min(gam(feas));
[a.Tmax_16k, kT] = max(out.T(:).*feas(:));
a.Tmax_gamma = gam(kT);  a.Tmax_I_rms = Irms(kT);
fprintf('4) 16 krpm 가능 최소 진각      | %.1f°  | 최대 토크 %.1f N·m (γ %.1f°, %.0f A rms) | Lab 88.0, 85.2°, 204 A\n', ...
        a.gamma_min_feasible, a.Tmax_16k, a.Tmax_gamma, a.Tmax_I_rms);

a.opt = local_min_loss(out, m, we, 1.0, kR);
fprintf('5) 16 krpm 1 N·m 손실 최소     | γ %.2f°, I %.1f A rms, V %.0f V | Lab 89.70°, 135.6 A, 277 V\n', ...
        a.opt.gamma_deg, a.opt.I_rms, a.opt.V_rms);

a.dTdg_138 = arrayfun(@(g) local_dTdg(out, 138*sqrt(2), g), [70 80 85]);
fprintf('6) dT/dγ @138 A rms            | 70° %.1f, 80° %.1f, 85° %.1f N·m/°  | Lab -8.5 / -10.4 / -10.9\n', ...
        a.dTdg_138(1), a.dTdg_138(2), a.dTdg_138(3));

fprintf('+) 손실 분해 @최소점           | DC %.2f + AC %.2f + 철손 %.2f kW | Lab 4.3 / 2.8 / 2.7 (0.44 N·m 점)\n', ...
        a.opt.Pcu/1e3, a.opt.Pac/1e3, a.opt.Pfe/1e3);

v = out.Fd(1, :);                                  % iq = 0 행
a.I_char_pk = interp1(v, out.id_pk, 0, 'linear');
fprintf('+) 특성전류 (Fd = 0)           | %.0f Apk = %.0f A rms | Lab 최적 전류 135.6 A rms\n', ...
        abs(a.I_char_pk), abs(a.I_char_pk)/sqrt(2));
fprintf('+) export 전압 대 정상상태식   | 중앙 차이 %.1f %%\n', a.V_export_vs_calc_pct);

out.anchors = a;
f = fullfile(workDir, 'e10_plant_lab.mat');
save(f, '-struct', 'out', '-v7.3');
fprintf('\n-> %s\n', f);
end

% ------------------------------------------------------------------ helpers
function s = local_min_loss(out, m, we, Tdem, kR)
best = struct('Ptot', inf);
Ipk = linspace(5, 650, 2000);
for g = 60:0.1:89.9
    id = -Ipk*sind(g);  iq = Ipk*cosd(g);
    T = interp2(out.id_pk, out.iq_pk, out.T, id, iq, 'linear', NaN);
    k = find(isfinite(T(1:end-1)) & isfinite(T(2:end)) & (T(1:end-1)-Tdem).*(T(2:end)-Tdem) <= 0, 1);
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
    Pac = interp2(out.id_pk, out.iq_pk, out.Pac(:, :, kR), idq, iqq, 'linear', NaN);
    Pfe = interp2(out.id_pk, out.iq_pk, out.Pfe(:, :, kR), idq, iqq, 'linear', NaN);
    Pmg = interp2(out.id_pk, out.iq_pk, out.Pmag(:, :, kR), idq, iqq, 'linear', NaN);
    tot = Pcu + max(Pac, 0) + max(Pfe, 0) + max(Pmg, 0);
    if isfinite(tot) && tot < best.Ptot
        best = struct('gamma_deg', g, 'I_rms', I_rms, 'T', Tdem, 'V_rms', V, ...
                      'Pcu', Pcu, 'Pac', Pac, 'Pfe', Pfe, 'Pmag', Pmg, 'Ptot', tot);
    end
end
s = best;
end

function g = local_dTdg(out, Ipk, gamma_deg)
T1 = interp2(out.id_pk, out.iq_pk, out.T, -Ipk*sind(gamma_deg-0.5), Ipk*cosd(gamma_deg-0.5), 'linear', NaN);
T2 = interp2(out.id_pk, out.iq_pk, out.T, -Ipk*sind(gamma_deg+0.5), Ipk*cosd(gamma_deg+0.5), 'linear', NaN);
g = T2 - T1;
end
