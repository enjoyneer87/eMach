function mdlFile = build_e10_stage2c(dataFile, outDir, harnessFile)
%BUILD_E10_STAGE2C  단계 2c — sim_e10_stage2 (스크립트 스위칭 시뮬레이터)의 Simscape Electrical 교차 확인 모델.
%
%   MathWorks 예제 "HEV PMSM Drive Test Harness" 를 복사해 다음과 같이 바꾼다.
%     PMSM   : FEM-Parameterized PMSM 을 fem_motor_dq0 변형("3-D flux linkage data", DQcartesian)으로.
%              Lab ψd(id,iq), ψq(id,iq) 를 회전자 각도 축으로 복제(각도 무관), ψ0 = 0, N = 4,
%              Rs = S.machine.Rs_80C, 철손 none, 토크 = Lab 축 토크표 T_shaft(id,iq) (각도 복제),
%              보간 linear (스크립트의 griddedInterpolant linear 와 같게).
%     기계   : 토크원 + 관성 동력계 -> 이상 각속도원 16000 rpm 고정, 이상 토크 센서로 축 토크 측정.
%     DC 링크: 720 V (S.machine.Vdc), 직렬 1 mΩ + 1 mF (원 하니스 구조 유지, 전압 강하 무시 수준).
%     인버터 : 원 하니스의 IGBT+게이트 드라이버 대신 Ideal Semiconductor Switch(Ron 1e-5 Ω, Goff 1e-8 S)
%              + 역병렬 Diode(piecewise linear, Vf 0.1 mV(0 불가), Ron 1e-5 Ω) — 전도 강하 ~0 (스크립트와 같게).
%     데드타임: 진짜 상보 게이트 블랭킹 — 상/하 게이트 각각 켜짐 가장자리만 td 늦춘다.
%              블랭킹 동안 누가 도통하는지는 다이오드(= 실제 전류 방향)가 정한다.
%     제어기 : 이산 Ts = 50 µs MATLAB Function 'Ctrl' = sim_e10_stage2 제어기(디커플링 dq PI, 역계산
%              안티와인드업, |v| ≤ Vmax 원 클램프, T*->(id*,iq*) 표, 지연 보상 ωe(n_delay+0.5)Ts)
%              -> Unit Delay(1 샘플 연산 지연) -> 'Mod' = SVPWM(min-max 주입) + 10 kHz 중앙정렬
%              삼각파·양 끝 갱신 + 블랭킹. Mod 는 이 반주기 안의 게이트 전환 시각(절대 시각)을 내보내고,
%              연속 시간 비교기(Clock > E, 영교차 검출)가 가변 스텝 솔버에서 그 시각을 정확히 잡는다.
%   파라미터(모델 워크스페이스): Tref_Nm (최종 토크 지령, 5 ms 에서 계단), td_s (데드타임 s), Tstop.
%   run_e10_stage2c 가 Simulink.SimulationInput 으로 바꿔 가며 직렬 실행한다.

if nargin < 1 || isempty(dataFile), dataFile = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive\e10_stage1_data_16000_shaft.mat'; end
if nargin < 2 || isempty(outDir), outDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive\stage2c'; end
if nargin < 3 || isempty(harnessFile)
    harnessFile = 'D:\KangDH\Thesis\e10\work_lab_pc1\mw_examples\ex1\HEVPMSMDriveTestHarness.slx';
end
mdl = 'e10_stage2c';
if ~exist(outDir, 'dir'), mkdir(outDir); end
mdlFile = fullfile(outDir, [mdl '.slx']);
if bdIsLoaded(mdl), close_system(mdl, 0); end
copyfile(harnessFile, mdlFile, 'f');
fileattrib(mdlFile, '+w');
load_system(mdlFile);
for p = {'PreLoadFcn', 'PostLoadFcn', 'InitFcn', 'StartFcn', 'StopFcn', 'CloseFcn'}
    set_param(mdl, p{1}, '');
end

% ------------------------------------------------------------------ 데이터·파라미터
S = load(dataFile);
m = S.machine;
N = m.p;  Ts = 0.5e-4;  we = S.we;  Rph = m.Rs_80C;  Vdc = m.Vdc;
P = struct();
P.Ts = Ts;  P.we = we;  P.Rph = Rph;  P.Vdc = Vdc;  P.Vmax = m.Vph_lim*sqrt(2);
P.Ld = 0.85e-3;  P.Lq = 1.6e-3;  P.lam = S.fd_vec(end);
P.Kpd = 8.50;  P.Kpq = 16.00;
P.Kid = P.Kpd/(P.Ld/Rph);  P.Kiq = P.Kpq/(P.Lq/Rph);  P.Kaw = 1/(P.Ld/Rph);
nDel = 1;
P.thc = we*(nDel + 0.5)*Ts;                      % 지연 보상 (delay_comp = 1)
P.ffRef = 0;                                     % 디커플링: 0 측정 전류, 1 기준 전류
P.Tv = S.T_ref_vec(:);  P.idRef = S.id_ref_current(:);  P.iqRef = S.iq_ref_current(:);
% 초기 상태: 첫 기준점(T* = 0)의 정상상태 (sim_e10_stage2 와 같음)
id0 = interp1(P.Tv, P.idRef, 0);  iq0 = interp1(P.Tv, P.iqRef, 0);
GFd = griddedInterpolant({S.iq_pk, S.id_pk}, S.Fd, 'linear', 'nearest');
GFq = griddedInterpolant({S.iq_pk, S.id_pk}, S.Fq, 'linear', 'nearest');
fl0 = [GFd(iq0, id0); GFq(iq0, id0)];
v0 = [Rph*id0 - we*fl0(2); Rph*iq0 + we*fl0(1)];
P.X0 = [v0(1) + we*P.Lq*iq0; v0(2) - we*(P.Ld*id0 + P.lam)];   % 적분기 정상상태 초기화
vab0 = v0;                                                   % θ = 0 에서의 αβ = dq

xdeg = 0:15:90;                                  % 회전자 각도 격자 (기계 deg) — 값은 각도 무관 복제
nx = numel(xdeg);
E10 = struct();
% 블록은 id 벡터가 0 을 포함하고 ± 대칭이기를 요구한다. Lab 맵은 id = -650..0 뿐이라
% id > 0 쪽을 붙인다: ψd 는 가장자리 기울기로 선형 외삽, ψq·토크는 id = 0 값 유지(nearest) —
% ψq 를 선형 외삽하면 id > 170 A 에서 Lq < 0 이 되어 블록이 경고한다. 이 운전점들은
% id ≈ -190..-290 A 라 id > 0 영역에는 닿지 않는다.
idP = S.id_pk(:).';  dId = idP(2) - idP(1);
assert(abs(idP(end)) < 1e-9, 'Lab id grid must end at 0');
idExt = [idP, dId:dId:-idP(1)];
[IQg, IDg] = ndgrid(S.iq_pk, idExt);
FdX = griddedInterpolant({S.iq_pk, S.id_pk}, S.Fd, 'linear', 'linear');
FqX = griddedInterpolant({S.iq_pk, S.id_pk}, S.Fq, 'linear', 'nearest');
TX  = griddedInterpolant({S.iq_pk, S.id_pk}, S.T_shaft, 'linear', 'nearest');
E10.id = idExt;  E10.iq = S.iq_pk(:).';  E10.x = xdeg;
E10.fd = repmat(FdX(IQg, IDg).', [1 1 nx]);      % (iq,id) -> (id,iq,x)
E10.fq = repmat(FqX(IQg, IDg).', [1 1 nx]);
E10.f0 = zeros(size(E10.fd));
E10.T  = repmat(TX(IQg, IDg).', [1 1 nx]);       % 축 토크표 (스크립트 출력 토크와 같은 표)
E10.id0 = id0;  E10.iq0 = iq0;  E10.Rs = Rph;  E10.N = N;  E10.Vdc = Vdc;
E10.rpm = S.speed_rpm;  E10.wm = S.wm;

mws = get_param(mdl, 'ModelWorkspace');
mws.clear;
assignin(mws, 'P', P);
assignin(mws, 'E10', E10);
assignin(mws, 'Ts_c', Ts);
assignin(mws, 'vab0', vab0);
assignin(mws, 'Tref_Nm', 20);
assignin(mws, 'Tstep', 0.005);
assignin(mws, 'td_s', 0);
assignin(mws, 'Tstop', 0.08);
% 하니스 PMSM 블록의 비활성(3-D 편미분 변형) 파라미터도 컴파일 때 평가되므로 하니스 값을 그대로 둔다.
% dq0 변형은 이 값들을 쓰지 않는다.
H = harnessVars(fileparts(harnessFile));
for f = fieldnames(H).', assignin(mws, f{1}, H.(f{1})); end

% ------------------------------------------------------------------ 최상위 정리
keep = {'Current Sensor', 'ERef', 'FEM-Parameterized PMSM', 'MRRef PMSM', 'Open Circuit', 'R', ...
        'Solver Configuration', 'Three-Phase Inverter', 'V Src'};
top = find_system(mdl, 'SearchDepth', 1, 'Type', 'block');
for k = 1:numel(top)
    if strcmp(top{k}, mdl), continue; end
    nm = normName(get_param(top{k}, 'Name'));
    if ~any(strcmp(nm, keep)), delete_block(top{k}); end
end
ann = find_system(mdl, 'SearchDepth', 1, 'FindAll', 'on', 'Type', 'annotation');
for k = 1:numel(ann), try, delete(getSimulinkBlockHandle(ann(k))); catch, try, delete_block(ann(k)); catch, end, end, end
L = find_system(mdl, 'SearchDepth', 1, 'FindAll', 'on', 'Type', 'line');
for k = 1:numel(L), try, delete_line(L(k)); catch, end, end
blkPM  = findTop(mdl, 'FEM-Parameterized PMSM');
blkCS  = findTop(mdl, 'Current Sensor');
blkINV = findTop(mdl, 'Three-Phase Inverter');
blkV   = findTop(mdl, 'V Src');
blkR   = findTop(mdl, 'R');
blkSC  = findTop(mdl, 'Solver Configuration');
blkMR  = findTop(mdl, 'MRRef PMSM');
blkER  = findTop(mdl, 'ERef');
blkOC  = findTop(mdl, 'Open Circuit');
% PMSM 변형 선택: 'SourceFile' 이 저장되는 선택자다 ('ComponentPath' 는 메모리에서만 바뀌고
% 저장·재로드 때 하니스의 fem_motor_3D 로 되돌아간다 — 실제로 그 상태로 N = 6 이상 전동기가 돌았음).
set_param(blkPM, 'SourceFile', 'ee.electromech.pmsm.fem_motor.fem_motor_dq0');
set_param(blkPM, 'Name', 'PMSM Lab dq0');
blkPM = [mdl '/PMSM Lab dq0'];
% 하니스와 같은 전기·기계 결선을 명시적으로 다시 긋는다 (인버터 상 포트는 이름으로 찾는다)
invPh = get_param(blkINV, 'PortHandles');
pIdx = @(nm) subsysPortIndex(blkINV, nm);
for x = 1:3
    add_line(mdl, invPh.RConn(pIdx(char('A' + x - 1))), cpH(blkCS, 'L', x));   % 인버터 상 x -> 센서 입력 x
    add_line(mdl, cpH(blkCS, 'R', x + 1), cpH(blkPM, 'L', x));                  % 센서 출력 x -> 전동기 상 x
end
phPM = get_param(blkPM, 'PortHandles');
if numel(phPM.LConn) >= 4
    add_line(mdl, phPM.LConn(4), cpH(blkOC, 'L', 1));     % 중성점 포트가 있으면 하니스처럼 개방
else
    delete_block(blkOC);                                  % dq0 변형(중성점 비노출)은 포트가 3 개
end
add_line(mdl, cpH(blkPM, 'R', 2), cpH(blkMR, 'L', 1));
add_line(mdl, cpH(blkSC, 'R', 1), cpH(blkMR, 'L', 1));
add_line(mdl, cpH(blkV, 'L', 1), cpH(blkR, 'L', 1));
add_line(mdl, cpH(blkR, 'R', 1), invPh.LConn(pIdx('+')));
add_line(mdl, cpH(blkV, 'R', 1), invPh.LConn(pIdx('-')));
add_line(mdl, cpH(blkER, 'L', 1), cpH(blkV, 'R', 1));

% ------------------------------------------------------------------ PMSM: dq0 변형 파라미터
assert(strcmp(get_param(blkPM, 'SourceFile'), 'ee.electromech.pmsm.fem_motor.fem_motor_dq0'));
sp =@(varargin) set_param(blkPM, varargin{:});
sp('param_dq0', 'ee.enum.fem_motor.fluxTabulationOption.DQcartesian');
sp('winding_type_dq0', 'ee.enum.statorconnection.wye');
sp('expose_neutral_port', 'ee.enum.fem_motor.exposeNeutralPort.no');
sp('nPolePairs', 'E10.N');
sp('N', 'E10.N');                                % 다른 변형용 공통 극쌍 수도 맞춰 둔다
sp('parks_type', 'ee.enum.fem_motor.parksType.QleadsD_AphaseToDaxis');
sp('idVec2', 'E10.id', 'idVec2_unit', 'A');
sp('iqVec2', 'E10.iq', 'iqVec2_unit', 'A');
sp('xVec2', 'E10.x', 'xVec2_unit', 'deg');
sp('fluxD_dq0', 'E10.fd', 'fluxD_dq0_unit', 'Wb');
sp('fluxQ_dq0', 'E10.fq', 'fluxQ_dq0_unit', 'Wb');
sp('fluxA_dq0', 'E10.f0', 'fluxA_dq0_unit', 'Wb');
sp('Torque_dq0', 'E10.T', 'Torque_dq0_unit', 'N*m');
try, sp('calculate_torque_matrix', 'ee.enum.fem_motor.calculateTorqueMatrix.no'); catch e, warning(e.message); end
sp('interp_method', 'simscape.enum.interpolation.linear');
sp('Rs', 'E10.Rs', 'Rs_unit', 'Ohm');
sp('loss_param', 'ee.enum.fem_motor.ironLossesExtended.none');
sp('Inertia', '0.01', 'lam', '0');
sp('i_d_specify', 'on', 'i_d_priority', 'High', 'i_d', 'E10.id0', 'i_d_unit', 'A');
sp('i_q_specify', 'on', 'i_q_priority', 'High', 'i_q', 'E10.iq0', 'i_q_unit', 'A');
sp('angular_velocity_specify', 'on', 'angular_velocity_priority', 'High', ...
   'angular_velocity', 'E10.rpm', 'angular_velocity_unit', 'rpm');
sp('angular_position_specify', 'on', 'angular_position_priority', 'High', ...
   'angular_position', '0', 'angular_position_unit', 'rad');

% ------------------------------------------------------------------ DC 링크
set_param(blkV, 'dc_voltage', 'E10.Vdc');
set_param(blkR, 'R', '1e-3');
set_param(blkSC, 'DoDC', 'off', 'UseLocalSolver', 'off', 'LocalSolverSampleTime', '1e-6');

% ------------------------------------------------------------------ 인버터 재구성 (포트·DC 커패시터만 유지)
inv = blkINV;
L = find_system(inv, 'SearchDepth', 1, 'FindAll', 'on', 'Type', 'line');
for k = 1:numel(L), try, delete_line(L(k)); catch, end, end
ib = find_system(inv, 'SearchDepth', 1, 'Type', 'block');
for k = 1:numel(ib)
    if strcmp(ib{k}, inv), continue; end
    nm = get_param(ib{k}, 'Name');
    if ~any(strcmp(nm, {'G', 'A', 'B', 'C', '+', '-', ' C'})), delete_block(ib{k}); end
end
cap = [inv '/ C'];
set_param(cap, 'c', '1', 'c_unit', 'mF', 'r', '1e-6', 'vc', 'E10.Vdc', 'vc_unit', 'V');
try, set_param(cap, 'vc_specify', 'on', 'vc_priority', 'High'); catch, end
pP = pport([inv '/+']);  pN = pport([inv '/-']);
add_line(inv, pP, cpH(cap, 'L', 1));
add_line(inv, pN, cpH(cap, 'R', 1));
dm = add_block('simulink/Signal Routing/Demux', [inv '/DemuxG'], 'Outputs', '6', 'Position', [80 40 85 400]);
add_line(inv, 'G/1', 'DemuxG/1');
swLib = sprintf('ee_lib/Semiconductors &\nConverters/Ideal Semiconductor\nSwitch');
dLib  = sprintf('ee_lib/Semiconductors &\nConverters/Diode');
phs = {'A', 'B', 'C'};
for x = 1:3
    pX = pport([inv '/' phs{x}]);
    for u = 1:2                                  % 1 = 상단, 2 = 하단
        k = 2*(x-1) + u;
        y0 = 40 + 120*(k-1);
        cv = add_block('nesl_utility/Simulink-PS Converter', sprintf('%s/SPS%d', inv, k), 'Position', [140 y0 170 y0+30]);
        set_param(cv, 'Unit', '1');
        setFilt(cv);
        sw = add_block(swLib, sprintf('%s/SW%d', inv, k), 'Position', [240 y0 280 y0+40]);
        set_param(sw, 'Ron', '1e-5', 'Goff', '1e-8', 'Vth', '0.5');
        try, set_param(sw, 'diode_param', 'ee.enum.semiconductors.protectionDiode.external'); catch, end
        dd = add_block(dLib, sprintf('%s/D%d', inv, k), 'Position', [330 y0 370 y0+30]);
        set_param(dd, 'ModelType', 'ee.enum.diode.modelType.pwl', 'Vf', '1e-4', 'Ron', '1e-5', 'Goff', '1e-8');
        try, set_param(dd, 'fidelity_level', 'ee.enum.diode.fidelity.idealSwitch'); catch, end
        try, set_param(dd, 'C_param', 'ee.enum.diode.capParam.fixed', 'CJ', '0'); catch, end
        try, set_param(dd, 'Q_param', 'ee.enum.diode.recoveryParam.off'); catch, end
        add_line(inv, sprintf('DemuxG/%d', k), sprintf('SPS%d/1', k));
        add_line(inv, cpH(cv, 'R', 1), cpH(sw, 'L', 1));          % 게이트 (PS)
        if u == 1
            add_line(inv, cpH(sw, 'R', 1), pP);   add_line(inv, cpH(sw, 'R', 2), pX);
            add_line(inv, cpH(dd, 'L', 1), pX);   add_line(inv, cpH(dd, 'R', 1), pP);   % 양극=상, 음극=+
        else
            add_line(inv, cpH(sw, 'R', 1), pX);   add_line(inv, cpH(sw, 'R', 2), pN);
            add_line(inv, cpH(dd, 'L', 1), pN);   add_line(inv, cpH(dd, 'R', 1), pX);   % 양극=-, 음극=상
        end
    end
end

% ------------------------------------------------------------------ 기계: 이상 각속도원 + 토크 센서
lib = @(s) sprintf(s);
wsrc = add_block(lib('fl_lib/Mechanical/Mechanical Sources/Ideal Angular\nVelocity Source'), [mdl '/Speed Source'], 'Position', [1200 300 1240 340]);
tsen = add_block('fl_lib/Mechanical/Mechanical Sensors/Ideal Torque Sensor', [mdl '/Torque Sensor'], 'Position', [1100 300 1140 340]);
mrw  = add_block(blkMR, [mdl '/MRRef Speed'], 'Position', [1280 380 1310 410]);
wcmd = add_block('simulink/Sources/Constant', [mdl '/wm'], 'Value', 'E10.wm', 'Position', [1120 200 1170 230]);
wsps = add_block('nesl_utility/Simulink-PS Converter', [mdl '/SPS w'], 'Position', [1190 200 1220 230]);
set_param(wsps, 'Unit', 'rad/s');  setFilt(wsps);
add_line(mdl, 'wm/1', 'SPS w/1');
% 각속도원: S 포트(물리 신호)를 연결 시험으로 찾는다
wp = [cpH(wsrc, 'L', 1), cpH(wsrc, 'R', 1), cpH(wsrc, 'R', 2)];
iS = connectFirst(mdl, cpH(wsps, 'R', 1), wp);
wMech = wp(setdiff(1:3, iS));                    % [R, C] 순서 가정 — run 에서 속도 부호로 확인
% 토크 센서: T 출력 포트를 찾는다
tq2s = add_block('nesl_utility/PS-Simulink Converter', [mdl '/PS2S T'], 'Position', [1100 420 1130 450]);
set_param(tq2s, 'Unit', 'N*m');
tp = [cpH(tsen, 'L', 1), cpH(tsen, 'R', 1), cpH(tsen, 'R', 2)];
iT = connectFirst(mdl, cpH(tq2s, 'L', 1), tp);
tMech = tp(setdiff(1:3, iT));                    % [R, C]
pmR = cpH(blkPM, 'R', 1);                        % 회전자
add_line(mdl, pmR, tMech(1));
add_line(mdl, tMech(2), wMech(1));
add_line(mdl, wMech(2), cpH(mrw, 'L', 1));

% ------------------------------------------------------------------ 측정·제어
cs2s = add_block('nesl_utility/PS-Simulink Converter', [mdl '/PS2S I'], 'Position', [700 520 730 550]);
set_param(cs2s, 'Unit', 'A');
add_line(mdl, cpH(blkCS, 'R', 1), cpH(cs2s, 'L', 1));
add_block('simulink/Discrete/Zero-Order Hold', [mdl '/ZOH I'], 'SampleTime', 'Ts_c', 'Position', [760 520 790 550]);
add_line(mdl, 'PS2S I/1', 'ZOH I/1');
add_block('simulink/Sources/Step', [mdl '/Tref'], 'Time', 'Tstep', 'Before', '0', 'After', 'Tref_Nm', ...
          'SampleTime', 'Ts_c', 'Position', [760 600 790 630]);
add_block('simulink/User-Defined Functions/MATLAB Function', [mdl '/Ctrl'], 'Position', [840 510 960 640]);
setMatlabFcn(mdl, 'Ctrl', ctrlCode(), {'P'});
add_line(mdl, 'ZOH I/1', 'Ctrl/1');
add_line(mdl, 'Tref/1', 'Ctrl/2');
add_block('simulink/Discrete/Unit Delay', [mdl '/Comp Delay'], 'InitialCondition', 'vab0', 'SampleTime', 'Ts_c', ...
          'Position', [1000 520 1040 560]);
add_line(mdl, 'Ctrl/1', 'Comp Delay/1');
add_block('simulink/Sources/Constant', [mdl '/td'], 'Value', 'td_s', 'Position', [1000 600 1040 630]);
add_block('simulink/User-Defined Functions/MATLAB Function', [mdl '/Mod'], 'Position', [1080 510 1200 650]);
setMatlabFcn(mdl, 'Mod', modCode(), {'P'});
add_line(mdl, 'Comp Delay/1', 'Mod/1');
add_line(mdl, 'td/1', 'Mod/2');
add_block('simulink/Sources/Clock', [mdl '/Clock'], 'Position', [1080 690 1110 720]);
for j = 1:3
    add_block('simulink/Logic and Bit Operations/Relational Operator', sprintf('%s/Cmp%d', mdl, j), ...
              'Operator', '>', 'ZeroCross', 'on', 'Position', [1250 500+60*j 1280 530+60*j]);
    add_line(mdl, 'Clock/1', sprintf('Cmp%d/1', j));
    add_line(mdl, sprintf('Mod/%d', j+1), sprintf('Cmp%d/2', j));
end
add_block('simulink/Signal Attributes/Data Type Conversion', [mdl '/g0 bool'], 'OutDataTypeStr', 'boolean', ...
          'Position', [1250 500 1280 530]);
add_line(mdl, 'Mod/1', 'g0 bool/1');
add_block('simulink/Logic and Bit Operations/Logical Operator', [mdl '/Gate XOR'], 'Operator', 'XOR', ...
          'Inputs', '4', 'Position', [1320 500 1350 720]);
add_line(mdl, 'g0 bool/1', 'Gate XOR/1');
for j = 1:3, add_line(mdl, sprintf('Cmp%d/1', j), sprintf('Gate XOR/%d', j+1)); end
add_block('simulink/Signal Attributes/Data Type Conversion', [mdl '/gate dbl'], 'OutDataTypeStr', 'double', ...
          'Position', [1380 590 1410 620]);
add_line(mdl, 'Gate XOR/1', 'gate dbl/1');
add_line(mdl, 'gate dbl/1', [get_param(blkINV, 'Name') '/1']);

% ------------------------------------------------------------------ 기록
add_block('simulink/Continuous/Integrator', [mdl '/T int'], 'InitialCondition', '0', 'Position', [1160 420 1190 450]);
add_line(mdl, 'PS2S T/1', 'T int/1');
toWs(mdl, 'log Tint', 'Tint_log', [1220 420 1300 450]);
add_line(mdl, 'T int/1', 'log Tint/1');
toWs(mdl, 'log diag', 'diag_log', [1000 680 1060 710]);
add_line(mdl, 'Ctrl/2', 'log diag/1');

% ------------------------------------------------------------------ 솔버
set_param(mdl, 'SolverType', 'Variable-step', 'Solver', 'ode23t', 'StopTime', 'Tstop', ...
          'MaxStep', '5e-6', 'RelTol', '1e-4', 'AbsTol', 'auto', 'ZeroCrossControl', 'UseLocalSettings', ...
          'SimscapeLogType', 'none', 'ReturnWorkspaceOutputs', 'on', 'SaveTime', 'off', 'SaveOutput', 'off', ...
          'SaveState', 'off', 'SignalLogging', 'off', 'LimitDataPoints', 'off');
try, set_param(mdl, 'MaxConsecutiveZCsMsg', 'none'); catch, end
try, set_param(mdl, 'MaxConsecutiveZCs', '100000'); catch, end
save_system(mdl, mdlFile);
fprintf('model saved: %s\n', mdlFile);
end

% ================================================================== MATLAB Function 본문
function c = ctrlCode()
c = strjoin({ ...
'function [vab, dg] = ctrl(iabc, Tr, P)'
'% sim_e10_stage2 제어기 (pi_dec, 약자속 트림 끔). 샘플 시각 t0 = k Ts, 각도 th0 = we t0 (th_err = 0).'
'persistent X k'
'if isempty(X), X = P.X0; k = 0; end'
't0 = k*P.Ts;  k = k + 1;'
'th0 = P.we*t0;'
'ial = (2*iabc(1) - iabc(2) - iabc(3))/3;'
'ibe = (iabc(2) - iabc(3))/sqrt(3);'
'c = cos(th0);  s = sin(th0);'
'idm =  c*ial + s*ibe;'
'iqm = -s*ial + c*ibe;'
'Tc = min(max(Tr, 0), P.Tv(end));'
'idr = interp1(P.Tv, P.idRef, Tc);'
'iqr = interp1(P.Tv, P.iqRef, Tc);'
'ed = idr - idm;  eq = iqr - iqm;'
'% 디커플링: 기본은 측정 전류, P.ffRef = 1 이면 기준 전류 (고조파 전류가 we*L 로 증폭되지 않게)'
'if P.ffRef > 0, idf = idr; iqf = iqr; else, idf = idm; iqf = iqm; end'
'vud = P.Kpd*ed + X(1) - P.we*P.Lq*iqf;'
'vuq = P.Kpq*eq + X(2) + P.we*(P.Ld*idf + P.lam);'
'vmag = sqrt(vud^2 + vuq^2);'
'if vmag > P.Vmax'
'    vsd = vud*P.Vmax/vmag;  vsq = vuq*P.Vmax/vmag;  sat = 1;'
'else'
'    vsd = vud;  vsq = vuq;  sat = 0;'
'end'
'X(1) = X(1) + P.Ts*(P.Kid*ed + P.Kaw*(vsd - vud));'
'X(2) = X(2) + P.Ts*(P.Kiq*eq + P.Kaw*(vsq - vuq));'
'cc = cos(P.thc);  sc = sin(P.thc);'
'vcd = cc*vsd - sc*vsq;  vcq = sc*vsd + cc*vsq;'
'vab = [c*vcd - s*vcq; s*vcd + c*vcq];'
'dg = [t0; idm; iqm; sqrt(vsd^2 + vsq^2); sat; idr; iqr];'
}, newline);
end

function c = modCode()
c = strjoin({ ...
'function [g0, E1, E2, E3] = modg(vab, td, P)'
'% SVPWM (min-max 주입) + 10 kHz 중앙정렬 삼각파, 양 끝 갱신 (Ts = Tpwm/2), 상보 게이트 블랭킹.'
'% 지령 폴 상태 cmd: 상승 반주기 = 시작 (d>=1), (1-d)Ts 에 1 / 하강 반주기 = 시작 (d>0), d Ts 에 0.'
'% 상단 게이트 = cmd 가 1 로 td 이상 유지된 동안, 하단 게이트 = cmd 가 0 으로 td 이상 유지된 동안.'
'% 출력: g0 = 반주기 시작(t0+) 게이트 상태 [au al bu bl cu cl], E1..E3 = 반주기 안 전환 시각(절대, 없으면 먼 미래).'
'persistent k cPrev tChg'
'if isempty(k), k = 0; cPrev = zeros(3,1); tChg = -ones(3,1); end'
'Ts = P.Ts;  t0 = k*Ts;  tE = t0 + Ts;  rising = (mod(k, 2) == 0);  k = k + 1;'
'va = vab(1);  vb = -vab(1)/2 + sqrt(3)/2*vab(2);  vc = -vab(1)/2 - sqrt(3)/2*vab(2);'
'vabc = [va; vb; vc];'
'vzs = -(max(vabc) + min(vabc))/2;'
'duty = 0.5 + (vabc + vzs)/P.Vdc;'
'duty = min(max(duty, 0), 1);'
'g0 = zeros(6,1);  E1 = (tE + 10*Ts)*ones(6,1);  E2 = E1;  E3 = E1;'
'tol = 1e-10;'
'for x = 1:3'
'    d = duty(x);'
'    chT = zeros(3,1);  chV = zeros(3,1);'
'    chT(1) = tChg(x);  chV(1) = cPrev(x);  n = 1;'
'    if rising, s0 = double(d >= 1); else, s0 = double(d > 0); end'
'    if s0 ~= cPrev(x), n = n + 1; chT(n) = t0; chV(n) = s0; end'
'    if d > 0 && d < 1'
'        n = n + 1;'
'        if rising, chT(n) = t0 + (1 - d)*Ts; chV(n) = 1; else, chT(n) = t0 + d*Ts; chV(n) = 0; end'
'    end'
'    cand = zeros(7,1);  nc = 1;  cand(1) = t0;'
'    for j = 1:n'
'        if chT(j) > t0 && chT(j) < tE, nc = nc + 1; cand(nc) = chT(j); end'
'        te = chT(j) + td;'
'        if te > t0 && te < tE, nc = nc + 1; cand(nc) = te; end'
'    end'
'    cs = sort(cand(1:nc));'
'    for u = 1:2'
'        want = 2 - u;                             % 상단: cmd = 1, 하단: cmd = 0'
'        gi = 2*(x-1) + u;'
'        gcur = gateAt(cs(1), chT, chV, n, want, td, tol);'
'        g0(gi) = gcur;  nt = 0;'
'        for j = 2:numel(cs)'
'            gn = gateAt(cs(j), chT, chV, n, want, td, tol);'
'            if gn ~= gcur'
'                nt = nt + 1;  gcur = gn;'
'                if nt == 1, E1(gi) = cs(j); elseif nt == 2, E2(gi) = cs(j); elseif nt == 3, E3(gi) = cs(j); end'
'            end'
'        end'
'    end'
'    cPrev(x) = chV(n);  tChg(x) = chT(n);'
'end'
'end'
''
'function g = gateAt(tau, chT, chV, n, want, td, tol)'
'j = 1;'
'for i = 1:n'
'    if chT(i) <= tau + tol, j = i; end'
'end'
'g = double(chV(j) == want && (tau - chT(j)) >= td - tol);'
'end'
}, newline);
end

% ================================================================== 도우미
function H = harnessVars(harnessDir)
% 하니스 파라미터 스크립트를 격리된 함수 작업공간에서 실행해 비활성 파라미터용 변수만 꺼낸다.
here = pwd;  cleanup = onCleanup(@() cd(here));
cd(harnessDir);
HEVPMSMDriveTestHarnessParameters;
H = struct('xVec', xVec, 'idVec', idVec, 'iqVec', iqVec, 'N', N, ...
           'dfluxAdiaMatrix', dfluxAdiaMatrix, 'dfluxAdibMatrix', dfluxAdibMatrix, ...
           'dfluxAdicMatrix', dfluxAdicMatrix, 'dfluxAdxMatrix', dfluxAdxMatrix, 'TorqueMatrix', TorqueMatrix);
end

function nm = normName(nm)
nm = strtrim(regexprep(strrep(nm, newline, ' '), '\s+', ' '));
end

function b = findTop(mdl, name)
top = find_system(mdl, 'SearchDepth', 1, 'Type', 'block');
b = '';
for k = 1:numel(top)
    if strcmp(normName(get_param(top{k}, 'Name')), name), b = top{k}; return; end
end
error('block not found: %s', name);
end

function idx = subsysPortIndex(sub, name)
% 서브시스템 물리 포트(PMIOPort) 이름 -> 그 쪽(왼/오른) 포트 번호
pm = find_system(sub, 'SearchDepth', 1, 'BlockType', 'PMIOPort');
nm = get_param(pm, 'Name');  sd = get_param(pm, 'Side');  pn = str2double(get_param(pm, 'Port'));
me = find(strcmp(nm, name), 1);
same = strcmp(sd, sd{me});
[~, order] = sort(pn(same));
cand = find(same);  cand = cand(order);
idx = find(cand == me);
end

function h = cpH(blk, side, idx)
ph = get_param(blk, 'PortHandles');
if side == 'L', h = ph.LConn(idx); else, h = ph.RConn(idx); end
end

function h = pport(blk)
ph = get_param(blk, 'PortHandles');
h = [ph.LConn ph.RConn];  h = h(1);
end

function i = connectFirst(sys, h, cands)
for i = 1:numel(cands)
    try
        add_line(sys, h, cands(i));
        return
    catch
    end
end
error('no compatible port');
end

function setFilt(cv)
try
    set_param(cv, 'FilteringAndDerivatives', 'zero');
catch
    mo = get_param(cv, 'MaskObject');  p = mo.getParameter('FilteringAndDerivatives');
    opts = p.TypeOptions;  disp(opts);
    set_param(cv, 'FilteringAndDerivatives', opts{end});
end
end

function toWs(mdl, name, var, pos)
add_block('simulink/Sinks/To Workspace', [mdl '/' name], 'VariableName', var, 'SaveFormat', 'Array', ...
          'SampleTime', 'Ts_c', 'MaxDataPoints', 'inf', 'Position', pos);
end

function setMatlabFcn(mdl, name, code, params)
rt = sfroot;
ch = rt.find('-isa', 'Stateflow.EMChart', 'Path', [mdl '/' name]);
ch.Script = code;
for k = 1:numel(params)
    d = ch.find('-isa', 'Stateflow.Data', 'Name', params{k});
    d.Scope = 'Parameter';
    try, d.Tunable = false; catch, end
end
end
