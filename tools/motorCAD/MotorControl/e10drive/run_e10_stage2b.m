function out = run_e10_stage2b(workDir)
%RUN_E10_STAGE2B  단계 2b — 교정표의 전압 여유가 고속 진각과 토크 정확도를 정한다.
%
%   단계 2 스위칭 모델(sim_e10_stage2)에 16 000 rpm 기준표 네 가지를 넣어 비교한다.
%     MCB      : mcb.generateMotorLUT 표 (단계 1·2 기준선, 전압 여유 사실상 0)
%     MBC 100/95/90 : calibratepmsm 표, VsMax = 403.2 V 피크의 100/95/90 %  (mbc_ref_from_lab)
%   토크 5/20/40/60/80 N·m x 데드타임 0/2/3 us (보상 없음) + td 3 us 보상 있음. 병렬 풀 없이 직렬.
%   출력: stage2b_results.csv (실현 토크, 진각, 전류 rms — 단계 3(c) Lab FMU 손실 입력)

if nargin < 1 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
S = load(fullfile(workDir, 'e10_stage1_data_16000_shaft.mat'));
M = load(fullfile(workDir, 'mbc_tables.mat'));
n0 = 16000;

refs = struct('name', "MCB", 'vsFactor', NaN, 'ref', []);
% 격자 표 대신 16 000 rpm 에서 수렴한(ExitFlags > 0) TPA 해만 쓴다. calibratepmsm 은 이 속도에서
% 약 20 N·m 아래의 해를 찾지 못하고(ExitFlags <= 0) 표를 전압 한계 2–4 배의 점으로 채운다.
% 그 구간은 수렴한 해의 첫 세 점을 T -> 0 으로 선형 외삽해 메운다 (보고서에 단서로 적는다).
for k = 1:numel(M.out)
    o = M.out(k);
    res = o.raw.results;
    g = res(res.n == n0 & res.ExitFlags > 0, :);
    g = sortrows(g, 'Trq');
    T = g.Trq;  id = g.Id;  iq = g.Iq;
    pd = polyfit(T(1:3), id(1:3), 1);  pq = polyfit(T(1:3), iq(1:3), 1);
    Tlo = (0:1:floor(T(1) - 1)).';
    r = struct('T', [Tlo; T], 'id', [polyval(pd, Tlo); id], 'iq', [max(polyval(pq, Tlo), 0); iq], ...
               'T_valid_min', T(1));
    refs(end+1) = struct('name', sprintf("MBC %d", round(100*o.vsFactor)), 'vsFactor', o.vsFactor, 'ref', r); %#ok<AGROW>
end

base = struct('Tstop', 0.08, 'n_delay', 1, 'delay_comp', 1, 'td', 0, 'dt_comp', 0, 'th_err', 0);
C = {};
for k = 1:numel(refs)
    for T = [5 20 40 60 80]
        for td = [0 2 3]*1e-6
            o = base;  o.td = td;  o.ref = refs(k).ref;  C(end+1, :) = {k, T, o}; %#ok<AGROW>
        end
        o = base;  o.td = 3e-6;  o.dt_comp = 1;  o.ref = refs(k).ref;  C(end+1, :) = {k, T, o}; %#ok<AGROW>
    end
end
fprintf('단계 2b: %d 실행\n', size(C, 1));
rows = cell(size(C, 1), 1);
for j = 1:size(C, 1)
    k = C{j, 1};  T = C{j, 2};  o = C{j, 3};
    o.Tref_fn = @(t) T*(t >= 0.005);
    r = sim_e10_stage2(S, o);
    L = round(0.85*numel(r.t)):numel(r.t);
    Tv = refs(k).ref;  if isempty(Tv), Tv = struct('T', S.T_ref_vec, 'id', S.id_ref_current, 'iq', S.iq_ref_current); end
    Tc = min(T, Tv.T(end));                        % 표 끝(최고 토크)을 넘는 지령은 제어기처럼 표 끝으로 자른다
    idr = interp1(Tv.T, Tv.id, Tc);  iqr = interp1(Tv.T, Tv.iq, Tc);
    rows{j} = struct('table', refs(k).name, 'vsFactor', refs(k).vsFactor, 'T_ref', T, 'td_us', o.td*1e6, ...
        'dt_comp', o.dt_comp, 'id_ref', idr, 'iq_ref', iqr, 'gamma_ref', atan2d(-idr, iqr), ...
        'I_ref_rms', hypot(idr, iqr)/sqrt(2), 'T', mean(r.T(L)), 'err_pct', 100*(mean(r.T(L))/T - 1), ...
        'gamma', mean(r.gamma(L)), 'I_rms', mean(r.Irms(L)), 'V_rms', mean(r.V(L)), ...
        'sat_pct', 100*mean(r.sat(L)));
end
out = struct2table([rows{:}].');
writetable(out, fullfile(workDir, 'stage2b_results.csv'));
fprintf('-> %s\n', fullfile(workDir, 'stage2b_results.csv'));
end
