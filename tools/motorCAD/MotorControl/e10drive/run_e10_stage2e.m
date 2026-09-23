function R = run_e10_stage2e(cases, Tstop, workDir, variantNames, outName, tableNames, remedyNames)
%RUN_E10_STAGE2E  단계 2e — 슬롯 고조파 대책(노치, 6차 PR, 육각형 과변조, 전압 피드백 약자속)을 Simscape 로 시험.
%
%   모델: stage2e\e10_stage2e.slx (build_e10_stage2e.m). 전동기 표 변형·기준표는 run_e10_stage2d 와 같다
%   (variantNames: 'fea_avg' C 평균 맵, 'fea_pos' D 위치별 맵; tableNames: 'QS 95' 등, 'MBC 95', 'MCB').
%   remedyNames (여러 개는 '+'로 조합, 예 'notch+fw'):
%     base   대책 없음 (2d 와 같아야 함)
%     notch  측정 전류에서 6차·접힌 12차 노치 (r = 0.9, 1.6 kHz 에서 위상 -4 deg)
%     pr6    6차 공진 제어기 (Kr = 150 Ohm, 위상 보상 pi/2 + 1.5 w0)
%     hex    육각형 한계 (khex = 0.97)
%     fw     전압 피드백 약자속 (Kfw = 200 A/(V s), Kleak = 2 1/s)
%     ffref  기준 전류 디커플링 (P.ffRef = 1, 2d 의 _ff 와 같음)
%   출력 CSV 에 idfw (약자속 루프가 더한 i_d, 마지막 15 % 평균) 포함.

if nargin < 1 || isempty(cases), cases = [5 0; 20 0; 60 0; 20 3e-6]; end
if nargin < 2 || isempty(Tstop), Tstop = 0.08; end
if nargin < 3 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
if nargin < 4 || isempty(variantNames), variantNames = {'fea_pos'}; end
if nargin < 5 || isempty(outName), outName = 'stage2e_results.csv'; end
if nargin < 6 || isempty(tableNames), tableNames = {'QS 95'}; end
if nargin < 7 || isempty(remedyNames), remedyNames = {'base', 'notch', 'pr6', 'hex', 'fw'}; end
mdl = 'e10_stage2e';
if ~bdIsLoaded(mdl), load_system(fullfile(workDir, 'stage2e', [mdl '.slx'])); end
mws = get_param(mdl, 'ModelWorkspace');
E0 = getVariable(mws, 'E10');  P0 = getVariable(mws, 'P');  Ts = getVariable(mws, 'Ts_c');
Tab = load(fullfile(workDir, 'stage2d_tables.mat'));

% ---- 16 krpm 대책 파라미터
we = P0.we;
w1 = mod(6*we*Ts, 2*pi);
w12 = mod(12*we*Ts, 2*pi);  w2 = min(w12, 2*pi - w12);          % 12차의 접힌 주파수
[b1, a1] = notchC(w1, 0.9);  [b2, a2] = notchC(w2, 0.9);
phi = pi/2 + 1.5*w1;
fprintf('notch at %.0f and %.0f Hz (fs %.0f Hz); PR at %.0f Hz, phase lead %.1f deg\n', ...
    w1/(2*pi*Ts), w2/(2*pi*Ts), 1/Ts, w1/(2*pi*Ts), rad2deg(mod(phi, 2*pi)));

% ---- 기준표
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
    E = E0;
    V = Tab.(['V_' vn]);
    for f = {'id', 'iq', 'x', 'fd', 'fq', 'f0', 'T', 'Rs'}
        E.(f{1}) = V.(f{1});
    end
    E.id = E.id(:).';  E.iq = E.iq(:).';  E.x = E.x(:).';
    for m = 1:numel(remedyNames)
        rn = remedyNames{m};
        parts = strsplit(rn, '+');
        for r = 1:numel(refs)
            P = refs(r).P;
            P.ffRef = 0;  P.notch = 0;  P.pr6 = 0;  P.hex = 0;  P.fw = 0;
            for p = parts
                switch p{1}
                    case 'base'
                    case 'notch', P.notch = 1;  P.nb1 = b1;  P.na1 = a1;  P.nb2 = b2;  P.na2 = a2;
                    case 'pr6',   P.pr6 = 1;  P.prw = w1;  P.prc0 = cos(phi);  P.prc1 = cos(w1 - phi);
                                  P.prKd = 150;  P.prKq = 150;
                    case 'hex',   P.hex = 1;  P.khex = 0.97;
                    case 'fw',    P.fw = 1;  P.Kfw = 200;  P.Kleak = 2;
                    case 'ffref', P.ffRef = 1;
                    otherwise, error('unknown remedy %s', p{1});
                end
            end
            for c = 1:size(cases, 1)
                Tr = cases(c, 1);  td = cases(c, 2);
                in = Simulink.SimulationInput(mdl);
                in = in.setVariable('E10', E, 'Workspace', mdl);
                in = in.setVariable('P', P, 'Workspace', mdl);
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
                idfw = mean(dg(nn, 6)) - interp1(P.Tv, P.idRef, min(max(Tr, 0), P.Tv(end)));
                rows(end+1, :) = {string(rn), string(vn), refs(r).name, Tr, td*1e6, Tavg, 100*(Tavg/Tr - 1), ...
                    max(Thalf(nn)) - min(Thalf(nn)), mean(atan2d(-idv, iqv)), mean(hypot(idv, iqv))/sqrt(2), ...
                    mean(vmag)/sqrt(2), 100*mean(sat), idfw, tRun}; %#ok<AGROW>
                fprintf('%-10s %-8s %-6s T*=%3g td=%g: T=%7.3f (%+6.1f %%) ripple %5.1f gamma %.3f I %.1f V %.1f sat %3.0f%% idfw %6.2f  %.0f s\n', ...
                    rn, vn, refs(r).name, Tr, td*1e6, Tavg, rows{end, 7}, rows{end, 8}, rows{end, 9}, rows{end, 10}, ...
                    rows{end, 11}, rows{end, 12}, idfw, tRun);
                R = cell2table(rows, 'VariableNames', {'remedy', 'variant', 'table', 'T_ref', 'td_us', 'T', 'err_pct', ...
                    'T_ripple_pp', 'gamma', 'I_rms', 'V_rms', 'sat_pct', 'idfw', 'run_s'});
                writetable(R, outCsv);
            end
        end
    end
end
fprintf('-> %s\n', outCsv);
end

function [b, a] = notchC(w0, r)
b = [1, -2*cos(w0), 1];  a = [1, -2*r*cos(w0), r^2];
b = b*sum(a)/sum(b);                                   % DC gain 1
end
