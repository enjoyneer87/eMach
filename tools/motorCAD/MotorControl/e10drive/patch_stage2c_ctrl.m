function patch_stage2c_ctrl(workDir)
%PATCH_STAGE2C_CTRL  저장된 e10_stage2c.slx 의 제어기에 디커플링 선택지 P.ffRef 를 넣는다 (모델 재생성 없이).
%
%   build_e10_stage2c.m 의 ctrlCode 와 같은 변경: P.ffRef = 1 이면 디커플링 전향 항
%   (-we Lq iq, we (Ld id + lam)) 을 측정 전류 대신 기준 전류로 계산한다. 16 krpm 에서 we*Lq = 10.7 Ω 이라
%   회전자 위치 고조파로 생긴 전류 고조파가 측정 전류 경로로 들어오면 전압 지령을 크게 흔든다.
%   기본값은 P.ffRef = 0 (이전과 같은 동작).

if nargin < 1 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
mdl = 'e10_stage2c';
f = fullfile(workDir, 'stage2c', [mdl '.slx']);
if ~bdIsLoaded(mdl), load_system(f); end
rt = sfroot;
charts = rt.find('-isa', 'Stateflow.EMChart');
hit = 0;
for k = 1:numel(charts)
    s = charts(k).Script;
    if contains(s, 'function [vab, dg] = ctrl') && ~contains(s, 'P.ffRef')
        old1 = 'vud = P.Kpd*ed + X(1) - P.we*P.Lq*iqm;';
        old2 = 'vuq = P.Kpq*eq + X(2) + P.we*(P.Ld*idm + P.lam);';
        assert(contains(s, old1) && contains(s, old2), 'ctrl code not as expected');
        new = sprintf(['%% decoupling: measured currents (P.ffRef = 0) or reference currents (P.ffRef = 1)\n' ...
                       'if P.ffRef > 0, idf = idr; iqf = iqr; else, idf = idm; iqf = iqm; end\n' ...
                       'vud = P.Kpd*ed + X(1) - P.we*P.Lq*iqf;']);
        s = strrep(s, old1, new);
        s = strrep(s, old2, 'vuq = P.Kpq*eq + X(2) + P.we*(P.Ld*idf + P.lam);');
        charts(k).Script = s;
        hit = hit + 1;
    elseif contains(s, 'function [vab, dg] = ctrl')
        hit = hit + 1;                                   % already patched
    end
end
assert(hit == 1, 'expected exactly one ctrl chart, found %d', hit);
mws = get_param(mdl, 'ModelWorkspace');
P = getVariable(mws, 'P');
if ~isfield(P, 'ffRef'), P.ffRef = 0; assignin(mws, 'P', P); end
save_system(mdl, f);
fprintf('patched ctrl (P.ffRef option) and saved %s\n', f);
end
