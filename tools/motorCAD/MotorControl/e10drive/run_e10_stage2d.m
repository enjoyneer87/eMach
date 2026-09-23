function R = run_e10_stage2d(cases, Tstop, workDir, variantNames, outName, tableNames)
%RUN_E10_STAGE2D  단계 2d — Simscape 모델(e10_stage2c)에 전동기 표 변형과 기준표를 바꿔 넣어 한 요인씩 비교.
%
%   전동기 표 변형 (모델은 그대로, 모델 작업공간 변수 E10 만 SimulationInput 으로 바꾼다)
%     A lab_rep  : 단계 2c 그대로 — Lab 맵을 회전자각으로 복제, Lab 축 토크 정의(철손 전체+자석손), Rs = R_dc
%     B lab_conv : Lab 맵 + 손실 규약 축 토크(loss_torque_convention.html) + Rs = R_dc + R_ac,eff
%                  (부하분 교류 동손 = 입력측 손실을 직렬 저항으로)
%     C fea_avg  : B 에서 운전 영역(id -364..0, iq -13..52 Apk)을 직접 FEA 위치 평균값으로 교체
%     D fea_pos  : C 에서 위치 평균 대신 회전자 위치별 값 (슬롯 고조파·코깅 포함)
%     B–D 의 표는 fea_posmap_analyze.py 가 만든 stage2d_tables.mat.
%     이름 끝에 '_ff' 를 붙이면(예: 'fea_pos_ff') 같은 표에 디커플링을 기준 전류로 계산 (P.ffRef = 1,
%     patch_stage2c_ctrl.m 로 넣은 선택지) — 고조파 전류가 we*L 로 증폭돼 전압 여유를 먹는지 가른다.
%     '_slow' 는 '_ff' 에 더해 전류 PI 이득을 1/10 (대역 1.6 kHz -> 160 Hz, 영점 위치 같음) — 제어기가
%     고조파 전류에 거의 반응하지 않게 해서, 남는 차이가 물리(고조파 전류 x 고조파 자속)인지 가른다.
%   outName: 결과 CSV 이름 (기본 stage2d_results.csv)
%   tableNames: 기준표 목록 (기본 {'MCB','MBC 95'}; 'MBC 90' 도 가능)
%   기준표: MCB (여유 0) 와 MBC VsMax 95 % (run_e10_stage2b 와 같은 수렴 해 + 저토크 외삽).
%     'QS 85' 등: qs_opsolver.py --map fea --tables 0.05,0.10,0.15,0.20 이 만든 drive\qs_tables.mat 의 표
%     (FEA 위치 평균 맵 + R_ac 로 |v| = 403.2 V x 0.85 에 정확히 놓인 최소 전류점 — 여유를 표 사이에서 정확히 비교).
%   cases : [T_ref(N·m), td(s)] 행 목록 (기본 5/20/60 N·m x 0/3 µs). 병렬 풀 없이 직렬.
%   출력: stage2d_results.csv (실행마다 덧붙여 저장 — 중간에 끊겨도 앞 결과는 남는다)

if nargin < 1 || isempty(cases), cases = [5 0; 5 3e-6; 20 0; 20 3e-6; 60 0; 60 3e-6]; end
if nargin < 2 || isempty(Tstop), Tstop = 0.08; end
if nargin < 3 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
if nargin < 4 || isempty(variantNames), variantNames = {'lab_rep', 'lab_conv', 'fea_avg', 'fea_pos'}; end
if nargin < 5 || isempty(outName), outName = 'stage2d_results.csv'; end
mdl = 'e10_stage2c';
if ~bdIsLoaded(mdl), load_system(fullfile(workDir, 'stage2c', [mdl '.slx'])); end
mws = get_param(mdl, 'ModelWorkspace');
E0 = getVariable(mws, 'E10');  P0 = getVariable(mws, 'P');  Ts = getVariable(mws, 'Ts_c');
Tab = load(fullfile(workDir, 'stage2d_tables.mat'));

% ---- 기준표: MCB (모델에 들어 있는 것) 와 MBC (수렴 해 + 저토크 외삽)
if nargin < 6 || isempty(tableNames), tableNames = {'MCB', 'MBC 95'}; end
M = load(fullfile(workDir, 'mbc_tables.mat'));
refs = struct('name', {}, 'P', {});
for t = 1:numel(tableNames)
    nm = tableNames{t};
    P = P0;
    if startsWith(nm, 'MBC')
        f = sscanf(nm, 'MBC %f')/100;
        kf = find(abs([M.out.vsFactor] - f) < 1e-9, 1);
        res = M.out(kf).raw.results;
        g = sortrows(res(res.n == 16000 & res.ExitFlags > 0, :), 'Trq');
        T = g.Trq;  id = g.Id;  iq = g.Iq;
        pd = polyfit(T(1:3), id(1:3), 1);  pq = polyfit(T(1:3), iq(1:3), 1);
        Tlo = (0:1:floor(T(1) - 1)).';
        P.Tv = [Tlo; T];  P.idRef = [polyval(pd, Tlo); id];  P.iqRef = [max(polyval(pq, Tlo), 0); iq];
    elseif startsWith(nm, 'QS')
        Q = load(fullfile(workDir, 'qs_tables.mat'));
        q = Q.(strrep(nm, ' ', ''));
        P.Tv = double(q.Tv(:));  P.idRef = double(q.idRef(:));  P.iqRef = double(q.iqRef(:));
    end
    refs(end+1) = struct('name', string(nm), 'P', P); %#ok<AGROW>
end

outCsv = fullfile(workDir, outName);
N = floor(Tstop/Ts + 1e-9);  n1 = round(0.85*N);
rows = {};
for v = 1:numel(variantNames)
    vn = variantNames{v};
    slow = endsWith(vn, '_slow');                   % 'xxx_slow': reference decoupling + PI gains / 10
    ff = endsWith(vn, '_ff') || slow;               % 'xxx_ff'  : same motor table, decoupling from reference currents
    tn = erase(erase(vn, '_ff'), '_slow');
    kg = 1 - 0.9*slow;
    E = E0;
    for r = 1:numel(refs)
        refs(r).P.ffRef = double(ff);
        refs(r).P.Kpd = P0.Kpd*kg;  refs(r).P.Kpq = P0.Kpq*kg;
        refs(r).P.Kid = P0.Kid*kg;  refs(r).P.Kiq = P0.Kiq*kg;
    end
    if ~strcmp(tn, 'lab_rep')
        V = Tab.(['V_' tn]);
        for f = {'id', 'iq', 'x', 'fd', 'fq', 'f0', 'T', 'Rs'}
            E.(f{1}) = V.(f{1});
        end
        E.id = E.id(:).';  E.iq = E.iq(:).';  E.x = E.x(:).';
    end
    for r = 1:numel(refs)
        for c = 1:size(cases, 1)
            Tr = cases(c, 1);  td = cases(c, 2);
            in = Simulink.SimulationInput(mdl);
            in = in.setVariable('E10', E, 'Workspace', mdl);
            in = in.setVariable('P', refs(r).P, 'Workspace', mdl);
            in = in.setVariable('Tref_Nm', Tr, 'Workspace', mdl);
            in = in.setVariable('td_s', td, 'Workspace', mdl);
            in = in.setVariable('Tstop', Tstop, 'Workspace', mdl);
            t0 = tic;
            out = sim(in);
            tRun = toc(t0);
            if ~isempty(out.ErrorMessage), error('%s', out.ErrorMessage); end
            dg = squeeze(out.get('diag_log'));  Ti = out.get('Tint_log');  Ti = Ti(:);
            if size(dg, 2) ~= 7, dg = dg.'; end
            nr = min(size(dg, 1), numel(Ti)) - 1;
            Nn = min(N, nr);  nn = n1:Nn;
            Thalf = diff(Ti(1:Nn+1))/Ts;
            Tavg = (Ti(Nn+1) - Ti(n1))/((Nn - n1 + 1)*Ts);
            idv = dg(nn + 1, 2);  iqv = dg(nn + 1, 3);  vmag = dg(nn, 4);  sat = dg(nn, 5);
            rows(end+1, :) = {string(vn), refs(r).name, Tr, td*1e6, Tavg, 100*(Tavg/Tr - 1), ...
                max(Thalf(nn)) - min(Thalf(nn)), mean(atan2d(-idv, iqv)), mean(hypot(idv, iqv))/sqrt(2), ...
                mean(vmag)/sqrt(2), 100*mean(sat), E.Rs, tRun}; %#ok<AGROW>
            fprintf('%-8s %-6s T*=%3g td=%g: T=%7.3f (%+6.1f %%) ripple %5.2f gamma %.3f I %.1f V %.1f sat %3.0f%%  %.0f s\n', ...
                vn, refs(r).name, Tr, td*1e6, Tavg, rows{end, 6}, rows{end, 7}, rows{end, 8}, rows{end, 9}, ...
                rows{end, 10}, rows{end, 11}, tRun);
            R = cell2table(rows, 'VariableNames', {'variant', 'table', 'T_ref', 'td_us', 'T', 'err_pct', ...
                'T_ripple_pp', 'gamma', 'I_rms', 'V_rms', 'sat_pct', 'Rs', 'run_s'});
            writetable(R, outCsv);
        end
    end
end
fprintf('-> %s\n', outCsv);
end
