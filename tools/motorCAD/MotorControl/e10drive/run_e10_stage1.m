function out = run_e10_stage1(speed_rpm, workDir)
%RUN_E10_STAGE1  단계 1 실험 — 축 토크 기준표 재생성 + (오프셋 x 지연) 격자 + 진각 상한.
%
%   1) MCB 기준표를 **축 토크** 테이블로 다시 만든다 (앞서는 전자기 토크로 만들어 11~16 % 어긋났다).
%   2) 레졸버 오프셋 0/1/2 전기각도 x 연산 지연 0/1/2 샘플 (지연 보상 on/off) 격자를 돌린다.
%   3) 토크 지령을 올려 가며 어디서 추종이 깨지는지(진각 상한) 본다.
%
%   출력: stage1_results.csv + 화면 표. 0 단계 몬테카를로에서 σ 로 뭉뚱그렸던 오차원을
%   지연·포화·리미터로 분해하는 것이 목적이다.

if nargin < 1 || isempty(speed_rpm), speed_rpm = 16000; end
if nargin < 2 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end

P = load(fullfile(workDir, 'e10_plant_lab.mat'));
m = P.machine;
kS = find(P.speeds == speed_rpm, 1);

% ---------- 1) 축 토크 기준표
pmsm = struct('model', 'e10', 'sn', '001', 'p', m.p, 'Rs', m.Rs_80C, 'Ld', 0.85e-3, 'Lq', 1.6e-3, ...
              'J', 0.05, 'B', 1e-3, 'FluxPM', P.lambda_m, 'I_rated', m.I_rated_rms*sqrt(2), ...
              'N_max', m.n_rated, 'PositionOffset', 0, 'QEPSlits', 1024);
pmsm.Ke = pmsm.FluxPM*sqrt(3)*2*pi*1000*pmsm.p/60;
pmsm.Kt = 1.5*pmsm.p*pmsm.FluxPM;
pmsm.T_rated = mcb.PMSMRatedTorque(pmsm);

idV = P.id_pk;  iqV = [-fliplr(P.iq_pk(2:end)), P.iq_pk];
Fd = zeros(numel(idV), numel(iqV));  Fq = Fd;  Ts_tab = Fd;
for a = 1:numel(idV)
    for b = 1:numel(iqV)
        iq = iqV(b);  sg = sign(iq + eps);
        Fd(a, b) = interp2(P.id_pk, P.iq_pk, P.Fd, idV(a), abs(iq), 'linear');
        Fq(a, b) = sg*interp2(P.id_pk, P.iq_pk, P.Fq, idV(a), abs(iq), 'linear');
        Ts_tab(a, b) = sg*interp2(P.id_pk, P.iq_pk, P.Tshaft(:, :, kS), idV(a), abs(iq), 'linear');
    end
end
pmsm.PMSMLUT = struct('method', 'FluxDQ', 'idVec', idV, 'iqVec', iqV, ...
                      'FluxDTable', Fd, 'FluxQTable', Fq, 'TorqueTable', Ts_tab, ...
                      'trefVec', linspace(0, 0.9*max(Ts_tab(:)), 25), ...
                      'wrpmVec', [0 2000 4000 8000 12000 16000]);
inv = mcb.getInverterParameters('BoostXL-DRV8305');
inv.V_dc = m.Vdc;  inv.I_max = pmsm.I_rated;  inv.ISenseMax = pmsm.I_rated;  inv.R_board = 0;
LUT = mcb.generateMotorLUT(pmsm, inv, 'idiqLUTs', drawLUT = 0, useTorquePercent = 0);
save(fullfile(workDir, 'mcb_lut_shaft.mat'), 'LUT', 'pmsm');

% ---------- 기준표를 단계 1 데이터에 얹고 맵을 대칭 확장
S = load(fullfile(workDir, sprintf('e10_stage1_data_%d.mat', speed_rpm)));
k = find(LUT.wrpmVec == speed_rpm, 1);
S.T_ref_vec = LUT.trefVec;
S.id_ref_current = LUT.idTable(:, k).';
S.iq_ref_current = LUT.iqTable(:, k).';
S.gamma_ref_current = atan2d(-S.id_ref_current, S.iq_ref_current);
S.I_ref_current = hypot(S.id_ref_current, S.iq_ref_current)/sqrt(2);
S.Fd = [flipud(S.Fd(2:end, :)); S.Fd];
S.Fq = [-flipud(S.Fq(2:end, :)); S.Fq];
S.T_shaft = [-flipud(S.T_shaft(2:end, :)); S.T_shaft];
S.iq_pk = [-fliplr(S.iq_pk(2:end)), S.iq_pk];
S.fd_ref_current = interp2(S.id_pk, S.iq_pk, S.Fd, S.id_ref_current, S.iq_ref_current, 'linear');
S.fq_ref_current = interp2(S.id_pk, S.iq_pk, S.Fq, S.id_ref_current, S.iq_ref_current, 'linear');
idF = linspace(S.id_pk(1), S.id_pk(end), 4*numel(S.id_pk));
iqF = linspace(S.iq_pk(1), S.iq_pk(end), 4*numel(S.iq_pk));
[IDf, IQf] = meshgrid(idF, iqF);
FD = interp2(S.id_pk, S.iq_pk, S.Fd, IDf, IQf, 'spline');
FQ = interp2(S.id_pk, S.iq_pk, S.Fq, IDf, IQf, 'spline');
S.fd_vec = linspace(min(FD(:)), max(FD(:)), 281);
S.fq_vec = linspace(min(FQ(:)), max(FQ(:)), 281);
[FDq, FQq] = meshgrid(S.fd_vec, S.fq_vec);
Fi = scatteredInterpolant(FD(:), FQ(:), IDf(:), 'linear', 'linear');  S.id_of_flux = Fi(FDq, FQq);
Fj = scatteredInterpolant(FD(:), FQ(:), IQf(:), 'linear', 'linear');  S.iq_of_flux = Fj(FDq, FQq);
save(fullfile(workDir, sprintf('e10_stage1_data_%d_shaft.mat', speed_rpm)), '-struct', 'S');

base = struct('Ts', 5e-5, 'Tstop', 0.06, 'Kfw_p', 0, 'Kfw_i', 0, 'ctrl', 'pi_dec');

fprintf('\n===== 기준표 재생성 확인 (축 토크) =====\n');
fprintf('%8s | %8s %8s | %8s\n', 'T*', 'γ_표', 'I_표', 'T_달성');
rows = [];
for T = [5 20 60 85]
    R = runOne(S, base, T);
    fprintf('%8.1f | %8.2f %8.1f | %8.2f (%+5.1f %%)\n', T, ...
            interp1(S.T_ref_vec, S.gamma_ref_current, T), ...
            interp1(S.T_ref_vec, S.I_ref_current, T), R.T, 100*(R.T/T - 1));
    rows = [rows; mkrow('ref_check', T, 0, 1, 1, R)];  %#ok<AGROW>
end

% ---------- 2) 오프셋 x 지연 격자
fprintf('\n===== 오프셋 x 지연 (20 / 60 N·m, 지연보상 on) =====\n');
fprintf('%6s %6s %6s | %8s %8s %8s %7s\n', 'T*', '오프셋', '지연', 'T', '오차%', 'γ', '포화%');
for T = [20 60]
    for th = [0 1 2]
        for nd = [0 1 2]
            o = base;  o.th_err = th;  o.n_delay = nd;
            R = runOne(S, o, T);
            fprintf('%6.0f %6.0f %6.0f | %8.2f %8.1f %8.2f %7.0f\n', T, th, nd, R.T, 100*(R.T/T-1), R.gamma, R.sat);
            rows = [rows; mkrow('offset_delay', T, th, nd, 1, R)];  %#ok<AGROW>
        end
    end
end

% ---------- 지연 보상 on/off
fprintf('\n===== 지연 보상 on/off (지연 1 샘플) =====\n');
for T = [20 60]
    for dc = [1 0]
        o = base;  o.n_delay = 1;  o.delay_comp = dc;
        R = runOne(S, o, T);
        fprintf('T* %5.0f, 보상 %d -> T %7.2f (%+5.1f %%), γ %7.2f, 포화 %3.0f %%\n', ...
                T, dc, R.T, 100*(R.T/T-1), R.gamma, R.sat);
        rows = [rows; mkrow('delay_comp', T, 0, 1, dc, R)];  %#ok<AGROW>
    end
end

% ---------- 3) 진각 상한 (토크를 올려 가며 추종이 깨지는 지점)
fprintf('\n===== 토크 상한 스캔 =====\n');
fprintf('%8s | %8s %8s %8s %7s\n', 'T*', 'T', '오차%', 'γ', '포화%');
for T = round(linspace(5, 0.98*max(S.T_ref_vec), 10))
    R = runOne(S, base, T);
    fprintf('%8.1f | %8.2f %8.1f %8.2f %7.0f\n', T, R.T, 100*(R.T/T-1), R.gamma, R.sat);
    rows = [rows; mkrow('ceiling', T, 0, 1, 1, R)];  %#ok<AGROW>
end

out = struct2table(rows);
writetable(out, fullfile(workDir, 'stage1_results.csv'));
fprintf('\n-> %s\n', fullfile(workDir, 'stage1_results.csv'));
end

function R = runOne(S, opt, T)
opt.Tref_fn = @(t) T*(t >= 0.005);
r = sim_e10_stage1(S, opt);
n = numel(r.t);  last = round(0.9*n):n;
R = struct('T', mean(r.T(last)), 'gamma', mean(r.gamma(last)), 'I', mean(r.Irms(last)), ...
           'V', mean(r.V(last)), 'sat', 100*mean(r.sat(last)));
end

function row = mkrow(kind, T, th, nd, dc, R)
row = struct('kind', string(kind), 'T_ref', T, 'offset_deg', th, 'delay_samples', nd, ...
             'delay_comp', dc, 'T', R.T, 'err_pct', 100*(R.T/T - 1), 'gamma', R.gamma, ...
             'I_rms', R.I, 'V_rms', R.V, 'sat_pct', R.sat);
end
