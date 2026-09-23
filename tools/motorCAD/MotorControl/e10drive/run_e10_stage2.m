function out = run_e10_stage2(workDir, nWorkers, part)
%RUN_E10_STAGE2  단계 2 실험 — 스위칭 인버터(10 kHz SVPWM, 양 끝 갱신) + 데드타임.
%
%   1) 데드타임 td = 0/1/2/3 us x 토크 5/20/60/85 N·m (지연 1 샘플, 보상 on, 오프셋 0)
%   2) 데드타임 보상 on/off (td = 2, 3 us)
%   3) 레졸버 오프셋 0/1/2 deg x 연산 지연 0/1/2 샘플 x 20/60 N·m (td = 2 us) — 단계 1 결론 재확인
%   4) 지연 보상 on/off (td = 0, 2 us)
%   5) 토크 상한 스캔 (td = 0, 2 us)
%   6) 상전류 파형 (5/60 N·m, td = 0/3 us) -> THD
%   데이터: e10_stage1_data_16000_shaft.mat (단계 1 과 같은 플랜트·기준표·이득)
%   출력: stage2_results.csv, stage2_traces.mat
%
%   part = [i n] 이면 병렬 풀 없이 전체 작업(격자 + 파형)의 i 번째 n 등분만 직렬로 돌려
%   stage2_part_i.mat 에 저장한다. 독립 배치 n 개로 돌린 뒤 merge_e10_stage2 로 합친다.
%   (병렬 풀이 다른 풀과 워커 좌석을 두고 겹치면 연결 단계에서 멈추는 일이 있었다.)

if nargin < 1 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
if nargin < 2, nWorkers = 12; end
if nargin < 3, part = []; end
S = load(fullfile(workDir, 'e10_stage1_data_16000_shaft.mat'));
Tstop = 0.08;
base = struct('Tstop', Tstop, 'n_delay', 1, 'delay_comp', 1, 'td', 0, 'dt_comp', 0, 'th_err', 0);

C = {};   % {kind, T, opt}
for td = [0 1 2 3]*1e-6
    for T = [5 20 60 85], o = base; o.td = td; C(end+1, :) = {'deadtime', T, o}; end %#ok<AGROW>
end
for td = [2 3]*1e-6
    for T = [5 20 60 85], o = base; o.td = td; o.dt_comp = 1; C(end+1, :) = {'dt_comp', T, o}; end %#ok<AGROW>
end
for T = [20 60]
    for th = [0 1 2]
        for nd = [0 1 2], o = base; o.td = 2e-6; o.th_err = th; o.n_delay = nd; C(end+1, :) = {'offset_delay', T, o}; end %#ok<AGROW>
    end
end
for td = [0 2]*1e-6
    for T = [20 60]
        for dc = [1 0], o = base; o.td = td; o.delay_comp = dc; C(end+1, :) = {'delay_comp', T, o}; end %#ok<AGROW>
    end
end
for td = [0 2]*1e-6
    for T = [5 20 40 60 70 80 85 90 100]
        o = base; o.td = td; C(end+1, :) = {'ceiling', T, o}; end %#ok<AGROW>
end
nRun = size(C, 1);
fprintf('단계 2: %d 실행\n', nRun);

we = S.we;  Te = 2*pi/we;
cases = {5, 0; 5, 3e-6; 60, 0; 60, 3e-6; 20, 0; 20, 3e-6};
if ~isempty(part)
    jobs = [ones(nRun, 1), (1:nRun)'; 2*ones(size(cases, 1), 1), (1:size(cases, 1))'];
    mine = jobs(part(1):part(2):end, :);
    res = {};  trs = {};
    for j = 1:size(mine, 1)
        t0 = tic;
        if mine(j, 1) == 1
            res{end+1} = gridRun(S, C(mine(j, 2), :)); %#ok<AGROW>
        else
            trs{end+1} = traceRun(S, base, cases(mine(j, 2), :), Tstop, Te); %#ok<AGROW>
        end
        fprintf('[%d/%d] job %d/%d done (%.0f s)\n', part(1), part(2), j, size(mine, 1), toc(t0));
    end
    save(fullfile(workDir, sprintf('stage2_part_%d.mat', part(1))), 'res', 'trs', 'mine');
    out = [];
    return
end
if isempty(gcp('nocreate')), parpool('Processes', nWorkers); end
res = cell(nRun, 1);
parfor k = 1:nRun
    res{k} = gridRun(S, C(k, :));
end
out = struct2table([res{:}].');
writetable(out, fullfile(workDir, 'stage2_results.csv'));
fprintf('-> %s\n', fullfile(workDir, 'stage2_results.csv'));

% ---- 상전류 파형 (마지막 전기 2주기)
tr = struct();
trs = cell(size(cases, 1), 1);
parfor k = 1:size(cases, 1)
    trs{k} = traceRun(S, base, cases(k, :), Tstop, Te);
end
tr.cases = [trs{:}];
save(fullfile(workDir, 'stage2_traces.mat'), '-struct', 'tr', '-v7');
fprintf('-> %s\n', fullfile(workDir, 'stage2_traces.mat'));
end

function row = gridRun(S, c)
o = c{3};  T = c{2};
o.Tref_fn = @(t) T*(t >= 0.005);
r = sim_e10_stage2(S, o);
L = round(0.85*numel(r.t)):numel(r.t);
row = struct('kind', string(c{1}), 'T_ref', T, 'td_us', o.td*1e6, 'dt_comp', o.dt_comp, ...
    'offset_deg', o.th_err, 'delay_samples', o.n_delay, 'delay_comp', o.delay_comp, ...
    'T', mean(r.T(L)), 'err_pct', 100*(mean(r.T(L))/T - 1), 'T_ripple_pp', max(r.T(L)) - min(r.T(L)), ...
    'gamma', mean(r.gamma(L)), 'I_rms', mean(r.Irms(L)), 'V_rms', mean(r.V(L)), ...
    'sat_pct', 100*mean(r.sat(L)), 'clip_pct', 100*mean(r.clip(L)));
end

function tr = traceRun(S, base, c, Tstop, Te)
T = c{1};  o = base;  o.td = c{2};
o.Tref_fn = @(t) T*(t >= 0.005);  o.trace_from = Tstop - 2*Te;
r = sim_e10_stage2(S, o);
tr = struct('T_ref', T, 'td_us', o.td*1e6, 'trace', r.trace);
end
