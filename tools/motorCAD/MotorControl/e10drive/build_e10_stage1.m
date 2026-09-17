function mdl = build_e10_stage1(S)
%BUILD_E10_STAGE1  e10 단계 1 모델 — 평균값 dq 플랜트 + 이산 FOC/약자속 (스위칭 없음).
%
%   HumanX Level 2 의 구조를 그대로 따르되(전압 방정식까지, 인버터 스위칭은 없음),
%   차이는 두 가지다: (1) 플랜트가 Motor-CAD Lab 자속맵이라 포화·교차포화가 들어온다,
%   (2) 이상 전류원이 아니라 전류 제어기가 붙어 있어 지연·포화·약자속 루프가 재현된다.
%
%   플랜트 (연속)
%     dλd/dt = vd - R id + we λq,   dλq/dt = vq - R iq - we λd
%     (id, iq) = 역맵(λd, λq)          2-D 룩업 (prep_e10_stage1)
%     T_shaft  = 토크맵(id, iq)         제동 손실(철손·자석손)을 이미 뺀 값
%
%   제어기 (이산 Ts)
%     기준표 T* -> (id*, iq*)  ->  전류 PI(디커플링, 안티와인드업)  ->  전압 원 제한
%     약자속: |v*| 가 한계를 넘으면 PI 로 id 를 더 음수로 민다
%     오차원: 레졸버 오프셋 th_err (제어기 프레임과 기계 프레임의 회전), 연산 지연 n_delay 샘플
%
%   왜 제어기 모델은 일부러 단순한가: 디커플링에 쓰는 Ld/Lq/λm 은 상수다. 실제 제어기도 그렇고,
%   그 모델 오차가 4절에서 σ 로 뭉뚱그렸던 오차원 중 하나다.
%
%   상태 (2026-09-17): **WIP — 블록 배치까지만 되어 있고 결선(add_line)이 없다.**
%   물리·제어 내용은 sim_e10_stage1.m 에서 먼저 확정한 뒤 여기에 옮긴다.

mdl = 'e10_stage1';
if bdIsLoaded(mdl), close_system(mdl, 0); end
new_system(mdl);
here = fileparts(mfilename('fullpath'));

add = @(src, name, pos) add_block(src, [mdl '/' name], 'Position', pos);

% ---------------------------------------------------------------- 입력·기준표
add('simulink/Sources/From Workspace', 'TrefIn', [20 100 100 130]);
set_param([mdl '/TrefIn'], 'VariableName', 'TrefTS', 'SampleTime', '0', ...
          'OutputAfterFinalValue', 'Holding final value');
add('simulink/Lookup Tables/1-D Lookup Table', 'idRef', [140 60 200 100]);
add('simulink/Lookup Tables/1-D Lookup Table', 'iqRef', [140 130 200 170]);
for b = {'idRef', 'iqRef'}
    set_param([mdl '/' b{1}], 'BreakpointsForDimension1', 'S.T_ref_vec', ...
              'ExtrapMethod', 'Clip', 'SampleTime', '-1');
end
set_param([mdl '/idRef'], 'Table', 'S.id_ref_ctrl');
set_param([mdl '/iqRef'], 'Table', 'S.iq_ref_ctrl');

% ---------------------------------------------------------------- 제어기
add('simulink/User-Defined Functions/MATLAB Function', 'Ctrl', [260 70 380 190]);
ctrl = sprintf([ ...
'function [vd, vq, idc, fw] = ctrl(idr, iqr, idm, iqm, P)\n' ...
'%%#codegen\n' ...
'persistent Xd Xq Xfw\n' ...
'if isempty(Xd), Xd = 0; Xq = 0; Xfw = 0; end\n' ...
'fw = Xfw;\n' ...
'idc = idr - Xfw;                          %% 약자속이 id 를 더 음수로 민다\n' ...
'ed = idc - idm;   eq = iqr - iqm;\n' ...
'vd_u = P.Kp*ed + Xd - P.we*(P.Lq*iqm);\n' ...
'vq_u = P.Kp*eq + Xq + P.we*(P.Ld*idm + P.lam);\n' ...
'vmag = hypot(vd_u, vq_u);\n' ...
'vd = vd_u;  vq = vq_u;\n' ...
'if vmag > P.Vmax\n' ...
'    vd = vd_u*P.Vmax/vmag;  vq = vq_u*P.Vmax/vmag;\n' ...
'end\n' ...
'Xd = Xd + P.Ts*(P.Ki*ed + P.Kaw*(vd - vd_u));   %% 안티와인드업 (역계산)\n' ...
'Xq = Xq + P.Ts*(P.Ki*eq + P.Kaw*(vq - vq_u));\n' ...
'Xfw = max(0, Xfw + P.Ts*P.Kfw*(vmag - P.Vmax)); %% 약자속 외루프\n' ...
'Xfw = min(Xfw, P.fw_max);\n']);
setMatlabFcn(mdl, 'Ctrl', ctrl);

% ---------------------------------------------------------------- 지연·각도 오차
add('simulink/Discrete/Unit Delay', 'Delay', [420 100 460 140]);
set_param([mdl '/Delay'], 'SampleTime', 'S.Ts', 'InitialCondition', '[0 0]');
add('simulink/User-Defined Functions/MATLAB Function', 'RotV', [500 100 570 140]);
setMatlabFcn(mdl, 'RotV', sprintf([ ...
'function v = rotv(u, th)\n%%#codegen\n' ...
'c = cos(th); s = sin(th);\n' ...
'v = [c*u(1) - s*u(2); s*u(1) + c*u(2)];\n']));
add('simulink/User-Defined Functions/MATLAB Function', 'RotI', [500 260 570 300]);
setMatlabFcn(mdl, 'RotI', sprintf([ ...
'function v = roti(u, th)\n%%#codegen\n' ...
'c = cos(-th); s = sin(-th);\n' ...
'v = [c*u(1) - s*u(2); s*u(1) + c*u(2)];\n']));
add('simulink/Sources/Constant', 'ThErr', [420 180 470 210]);
set_param([mdl '/ThErr'], 'Value', 'S.th_err');

% ---------------------------------------------------------------- 플랜트
add('simulink/User-Defined Functions/MATLAB Function', 'Plant', [620 100 760 200]);
setMatlabFcn(mdl, 'Plant', sprintf([ ...
'function dflux = plant(v, i, flux, P)\n%%#codegen\n' ...
'dflux = [v(1) - P.R*i(1) + P.we*flux(2);\n' ...
'         v(2) - P.R*i(2) - P.we*flux(1)];\n']));
add('simulink/Continuous/Integrator', 'Flux', [800 120 840 160]);
set_param([mdl '/Flux'], 'InitialCondition', 'S.flux0');
add('simulink/Lookup Tables/2-D Lookup Table', 'InvMap', [880 100 950 180]);
set_param([mdl '/InvMap'], 'NumberOfTableDimensions', '2', ...
          'BreakpointsForDimension1', 'S.fd_vec', 'BreakpointsForDimension2', 'S.fq_vec', ...
          'Table', 'S.id_of_flux_T', 'ExtrapMethod', 'Clip');
add('simulink/Lookup Tables/2-D Lookup Table', 'InvMapQ', [880 200 950 280]);
set_param([mdl '/InvMapQ'], 'NumberOfTableDimensions', '2', ...
          'BreakpointsForDimension1', 'S.fd_vec', 'BreakpointsForDimension2', 'S.fq_vec', ...
          'Table', 'S.iq_of_flux_T', 'ExtrapMethod', 'Clip');
add('simulink/Lookup Tables/2-D Lookup Table', 'TorqueMap', [880 320 950 400]);
set_param([mdl '/TorqueMap'], 'NumberOfTableDimensions', '2', ...
          'BreakpointsForDimension1', 'S.id_pk', 'BreakpointsForDimension2', 'S.iq_pk', ...
          'Table', 'S.T_shaft_T', 'ExtrapMethod', 'Clip');

% ---------------------------------------------------------------- 결선용 Mux/Demux
add('simulink/Signal Routing/Mux', 'MuxRef', [230 70 235 170]);
add('simulink/Signal Routing/Mux', 'MuxV', [400 100 405 140]);
add('simulink/Signal Routing/Demux', 'DemuxV', [590 100 595 140]);
add('simulink/Signal Routing/Mux', 'MuxI', [980 140 985 230]);
add('simulink/Signal Routing/Demux', 'DemuxFlux', [860 120 865 160]);
add('simulink/Signal Routing/Demux', 'DemuxIctrl', [610 260 615 300]);

% ---------------------------------------------------------------- 출력
names = {'flux', 'iDQ', 'vDQ', 'Tshaft', 'idCmd', 'fwState'};
for k = 1:numel(names)
    add('simulink/Sinks/To Workspace', ['out_' names{k}], [1050 60+50*k 1130 90+50*k]);
    set_param([mdl '/out_' names{k}], 'VariableName', names{k}, 'SaveFormat', 'Timeseries', ...
              'SampleTime', '-1');
end

set_param(mdl, 'Solver', 'ode4', 'FixedStep', 'S.h', 'StopTime', 'S.Tstop', ...
          'SolverType', 'Fixed-step');
save_system(mdl, fullfile(here, [mdl '.slx']));
fprintf('모델 저장: %s\n', fullfile(here, [mdl '.slx']));
end

function setMatlabFcn(mdl, name, code)
%  MATLAB Function 블록의 본문을 넣는다 (프로그램 조립용 관용구)
root = sfroot;
blk = root.find('-isa', 'Stateflow.EMChart', '-and', 'Path', [mdl '/' name]);
blk.Script = code;
end
