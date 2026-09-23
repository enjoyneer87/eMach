function R = run_e10_stage2c(cases, Tstop, workDir)
%RUN_E10_STAGE2C  단계 2c 실행 — Simscape 모델(e10_stage2c.slx)을 스크립트 단계 2와 같은 운전점에서 돌려 비교.
%
%   cases : [T_ref(N·m), td(s)] 행 목록. 기본 20/60 N·m x td 0/3 µs.
%   Tstop : 정지 시각 (기본 0.08 s, 5 ms 에서 토크 계단 — sim_e10_stage2 와 같음).
%   평균 구간: 스크립트와 같은 반주기 번호 n = round(0.85 N) .. N (N = Tstop/Ts).
%     토크 = 그 구간 축 토크 시간 평균 (토크 센서 적분), 리플 = 반주기 평균 토크의 최대-최소,
%     id, iq = 반주기 끝(= 다음 샘플) 전류 -> gamma = atan2d(-id, iq), I_rms = |i|/sqrt(2),
%     V_rms = |v*|/sqrt(2) (클램프 후 지령), sat = 전압원 클램프 비율.
%   출력: stage2c_results.csv (Simscape 값 + 같은 행의 스크립트 값 + 차이), 표 출력.
%   병렬 풀 없이 직렬 실행.

if nargin < 1 || isempty(cases), cases = [20 0; 20 3e-6; 60 0; 60 3e-6]; end
if nargin < 2 || isempty(Tstop), Tstop = 0.08; end
if nargin < 3 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
mdl = 'e10_stage2c';
mdlFile = fullfile(workDir, 'stage2c', [mdl '.slx']);
if ~bdIsLoaded(mdl), load_system(mdlFile); end
mws = get_param(mdl, 'ModelWorkspace');
Ts = getVariable(mws, 'Ts_c');
S = load(fullfile(workDir, 'e10_stage1_data_16000_shaft.mat'));
GT = griddedInterpolant({S.iq_pk, S.id_pk}, S.T_shaft, 'linear', 'nearest');
Tsign = +1;   % 이상 토크 센서(R=회전자 쪽, C=각속도원 쪽) 출력이 전동기 축 토크와 같은 부호 (T_shaft 표 조회로 확인)

N = floor(Tstop/Ts + 1e-9);
n1 = round(0.85*N);
rows = {};
for c = 1:size(cases, 1)
    T = cases(c, 1);  td = cases(c, 2);
    in = Simulink.SimulationInput(mdl);
    in = in.setVariable('Tref_Nm', T, 'Workspace', mdl);
    in = in.setVariable('td_s', td, 'Workspace', mdl);
    in = in.setVariable('Tstop', Tstop, 'Workspace', mdl);
    t0 = tic;
    out = sim(in);
    tRun = toc(t0);
    if ~isempty(out.ErrorMessage), error('%s', out.ErrorMessage); end
    dg = squeeze(out.get('diag_log'));  Ti = Tsign*out.get('Tint_log');  Ti = Ti(:);
    if size(dg, 2) ~= 7, dg = dg.'; end        % 벡터 신호 Array 저장은 7 x 1 x n 으로 올 수 있다
    nr = min(size(dg, 1), numel(Ti)) - 1;     % 행 k+1 = 시각 k Ts
    Nn = min(N, nr);
    nn = n1:Nn;
    Thalf = diff(Ti(1:Nn+1))/Ts;              % 반주기 n 의 평균 토크 = Thalf(n)
    Tavg = (Ti(Nn+1) - Ti(n1))/((Nn - n1 + 1)*Ts);
    id = dg(nn + 1, 2);  iq = dg(nn + 1, 3);  % 반주기 n 끝의 전류
    vmag = dg(nn, 4);  sat = dg(nn, 5);       % 반주기 n 시작에 계산된 지령
    Tlut = mean(GT(iq, id));                  % 표 조회 확인용 (샘플 순간 전류)
    rows(end+1, :) = {"simscape", T, td*1e6, Tavg, 100*(Tavg/T - 1), max(Thalf(nn)) - min(Thalf(nn)), ...
        mean(atan2d(-id, iq)), mean(hypot(id, iq))/sqrt(2), mean(vmag)/sqrt(2), 100*mean(sat), Tlut, tRun}; %#ok<AGROW>
    fprintf('[%d/%d] T*=%g td=%g us: T=%.3f gamma=%.3f Irms=%.2f Vrms=%.1f sat=%.0f%% (T_lut %.3f)  %.0f s\n', ...
        c, size(cases, 1), T, td*1e6, rows{end, 4}, rows{end, 7}, rows{end, 8}, rows{end, 9}, rows{end, 10}, Tlut, tRun);
end
R = cell2table(rows, 'VariableNames', {'model', 'T_ref', 'td_us', 'T', 'err_pct', 'T_ripple_pp', ...
    'gamma', 'I_rms', 'V_rms', 'sat_pct', 'T_lut_samples', 'run_s'});
R.Tstop = repmat(Tstop, height(R), 1);

% ---- 스크립트(단계 2) 같은 행과 비교
ref = readtable(fullfile(workDir, 'stage2_results.csv'), 'TextType', 'string');
ref = ref(ref.kind == "deadtime" & ref.dt_comp == 0 & ref.offset_deg == 0 & ref.delay_samples == 1 & ref.delay_comp == 1, :);
f = {'T', 'gamma', 'I_rms', 'V_rms', 'sat_pct', 'T_ripple_pp'};
for j = 1:numel(f), R.(['script_' f{j}]) = nan(height(R), 1); end
for i = 1:height(R)
    k = find(ref.T_ref == R.T_ref(i) & abs(ref.td_us - R.td_us(i)) < 1e-9, 1);
    if isempty(k), continue; end
    for j = 1:numel(f), R.(['script_' f{j}])(i) = ref.(f{j})(k); end
end
R.dT_pct = 100*(R.T./R.script_T - 1);
R.dT_Nm = R.T - R.script_T;
R.dgamma_deg = R.gamma - R.script_gamma;
R.dI_pct = 100*(R.I_rms./R.script_I_rms - 1);
outCsv = fullfile(workDir, 'stage2c_results.csv');
writetable(R, outCsv);

fprintf('\n%-6s %-6s | %-9s %-9s %-8s | %-8s %-8s %-7s | %-8s %-8s %-7s | %-6s %-6s\n', 'T*', 'td us', ...
    'T script', 'T simsc', 'dT %', 'g script', 'g simsc', 'dg deg', 'I script', 'I simsc', 'dI %', 'sat s', 'sat c');
for i = 1:height(R)
    fprintf('%-6g %-6g | %-9.3f %-9.3f %-8.2f | %-8.3f %-8.3f %-7.3f | %-8.2f %-8.2f %-7.2f | %-6.0f %-6.0f\n', ...
        R.T_ref(i), R.td_us(i), R.script_T(i), R.T(i), R.dT_pct(i), R.script_gamma(i), R.gamma(i), R.dgamma_deg(i), ...
        R.script_I_rms(i), R.I_rms(i), R.dI_pct(i), R.script_sat_pct(i), R.sat_pct(i));
end
fprintf('-> %s\n', outCsv);
end
