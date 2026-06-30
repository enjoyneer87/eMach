
%% ═══════════════════════════════════════════════════════════════════════════════
%% buildMotorModelForSyre — SyRE 호환 motorModel 구조체 초기화
%%
%% 사용법
%%   motorModel = buildMotorModelForSyre(matPath)
%%       → MAT 파일만 사용 (기본 파라미터 필수 하드코딩)
%%
%%   motorModel = buildMotorModelForSyre(matPath, motFilePath)
%%       → MOT 파일에서 파라미터 자동 추출
%%
%%   motorModel = buildMotorModelForSyre(matPath, ActiveXParametersStruct)
%%       → 이미 로드된 ActiveX 구조체 사용
%%
%% 파라미터 추출 소스 (Motor-CAD → SyRE)
%%   Pole_Number               → data.p     (극쌍수 = 극수/2)
%%   Resistance_MotorLAB       → data.Rs    (DC 상저항, Ω)
%%   Stator_Lam_Length         → data.l     (활성 스택 길이, m)
%%   EndWindingResistance_Lab  → data.lend  (엔드와인딩 길이, 저항비 × l)
%%   DCBusVoltage              → data.Vdc   (DC 링크 전압, V)
%%   MaxModelCurrent_RMS       → data.Imax  (피크 전류, A_pk)
%%   SpeedMax_MotorLAB         → data.nmax  (최대속도, rpm)
%%   Twdg_MotorLAB             → data.tempCu (권선 기준온도, °C)
%% ═══════════════════════════════════════════════════════════════════════════════
function motorModel = buildMotorModelForSyre(matPath, motPathOrAX)

%% ── 0. Motor-CAD 파라미터 추출 ───────────────────────────────────────────────
if nargin >= 2 && ~isempty(motPathOrAX)
    fprintf('buildMotorModelForSyre: Motor-CAD 파라미터 추출 중...\n');
    % [FIX] ActiveX 카탈로그를 .mot 경로에서 '한 번만' 파싱한 뒤 두 추출기에 동일
    %       struct 를 전달한다. getMCADBuildingDataFromMotFile 은 path→struct 변환
    %       가드가 없어 raw 경로를 넘기면 fieldnames(char) 에러로 즉시 실패한다.
    %       (표준 호출 규약: getMCADData4ScalingFromMotFile.m line 4/10/11 과 동일)
    if ischar(motPathOrAX) || isstring(motPathOrAX)
        AX = mcad.getMcadActiveXTableFromMotFile(char(motPathOrAX));
    else
        AX = motPathOrAX;   % 이미 파싱된 ActiveX 카탈로그 struct
    end
    MachineData  = getMcadMachineDataFromMotFile(AX);
    BuildingData = getMCADBuildingDataFromMotFile(AX);

    % 극쌍수
    p = safeGet(MachineData, {'Geometry','Pole_Number'}, NaN) / 2;

    % DC 상저항 @ Lab 기준온도 (Ω)
    Rs0 = safeGet(MachineData, {'LossModelTemperature','Resistance_MotorLAB'}, NaN);

    % 엔드와인딩 저항 (Ω) → lend/l 비율 계산용
    R_ew  = safeGet(MachineData, {'LossModelTemperature','EndWindingResistance_Lab'}, NaN);
    R_act = safeGet(MachineData, {'LossModelTemperature','ResistanceActivePart'},     NaN);

    % 활성 스택 길이 (mm → m)
    l_mm = safeGet(MachineData, {'Geometry','Stator_Lam_Length'}, NaN);
    l    = l_mm / 1000;

    % 엔드와인딩 등가 길이 (저항 비율 × 스택길이)
    %   R_ew/R_act = lend/l  →  lend = l × R_ew/R_act
    if ~isnan(R_ew) && ~isnan(R_act) && R_act > 0
        lend = l * R_ew / R_act;
    else
        lend = NaN;
    end

    % DC 링크 전압 (V)
    Vdc = safeGet(MachineData, {'Geometry','DCBusVoltage'}, NaN);

    % 최대 전류 (RMS → Peak)
    I_rms = safeGet(BuildingData, {'MotorCADGeo','MaxModelCurrent_RMS_MotorLAB'}, NaN);
    if isnan(I_rms)
        % 폴백: CurrentSpec_MotorLAB (RMS가 없을 때)
        I_rms = safeGet(BuildingData, {'MotorCADGeo','CurrentSpec_MotorLAB'}, NaN);
    end
    Imax = I_rms * sqrt(2);   % A_pk

    % 최대 속도 (rpm)
    nmax = safeGet(BuildingData, {'MotorCADGeo','SpeedMax_MotorLAB'}, NaN);

    % 권선 기준 온도 (°C)
    tempCu = safeGet(BuildingData, {'T0data','Twdg_MotorLAB'}, NaN);
    if isnan(tempCu)
        tempCu = safeGet(MachineData, {'LossModelTemperature','Twdg_MotorLAB'}, NaN);
    end

    % NaN 파라미터 경고 후 기본값 적용
    [p, Rs0, l, lend, Vdc, Imax, nmax, tempCu] = applyDefaults(...
        p, Rs0, l, lend, Vdc, Imax, nmax, tempCu);

    fprintf('  p=%d  Rs=%.4fΩ  l=%.3fm  lend=%.3fm\n', p, Rs0, l, lend);
    fprintf('  Vdc=%.0fV  Imax=%.1fA_pk  nmax=%.0frpm  tempCu=%.0f°C\n', Vdc, Imax, nmax, tempCu);
else
    % ── 폴백: 하드코딩 기본값 (e10Turn6V261 기준) ────────────────────────────
    fprintf('buildMotorModelForSyre: MOT 파일 없음 → 하드코딩 기본값 사용\n');
    p      = 4;            % 극쌍수 (8P → p=4)
    Rs0    = 0.063783;     % DC 상저항 at 20°C (Ω)
    l      = 0.150;        % 활성 스택 길이 (m)
    lend   = 0.040;        % 엔드와인딩 등가 길이 (m)
    Vdc    = 720;          % DC 링크 전압 (V)
    Imax   = 650.54;       % 피크 전류 = 460√2 (A_pk)
    nmax   = 16000;        % 최대 속도 (rpm)
    tempCu = 20;           % 기준 온도 (°C)
end

%% ── 1. MAT 파일 로드 ─────────────────────────────────────────────────────────
m = load(matPath);
motorModel = struct();
motorModel.FluxMap_dq = m.FluxMap_dq;
if isfield(m, 'IronPMLossMap_dq')
    motorModel.IronPMLossMap_dq = m.IronPMLossMap_dq;
end

%% ── 2. 기본 모터 파라미터 ───────────────────────────────────────────────────
motorModel.data.motorType = 'PM';
motorModel.data.axisType  = 'PM';
%   ※ 'PM': Tem(Iq==0)=0 (물리적으로 정확)
%            T=0 탐색을 Iq=0 축에서 수행 (올바름)
%      'dq': Tem(Id==0)=0 → Id=0에서 토크 소거 오류, T=0 탐색 방향도 틀림
motorModel.data.pathname  = [fileparts(matPath) filesep];

[~, name, ~] = fileparts(matPath);
motorModel.data.motorName = name;

motorModel.data.p         = p;
motorModel.data.Rs        = Rs0;
motorModel.data.n0        = 0;
motorModel.data.nmax      = nmax;
motorModel.data.Imax      = Imax;
motorModel.data.Vdc       = Vdc;
motorModel.data.tempCu    = tempCu;
motorModel.data.tempPM    = 80;
motorModel.data.n3phase   = 1;
motorModel.data.l         = l;
motorModel.data.lend      = lend;

motorModel.dataSet.TypeOfRotor         = 'PM';
motorModel.dataSet.RatedCurrent        = Imax / sqrt(2);   % A_rms
motorModel.dataSet.NumOfPolePairs      = p;
motorModel.dataSet.Rs                  = Rs0;
motorModel.dataSet.TargetCopperTemp    = tempCu;
motorModel.dataSet.tempPP              = 80;
motorModel.dataSet.TurnsInSeries       = 1;
motorModel.dataSet.StackLength         = l;
motorModel.dataSet.EndWindingsLength   = lend;
motorModel.dataSet.StatorOuterRadius   = 1;

%% ── 3. 스케일링·스큐 기본값 ─────────────────────────────────────────────────
motorModel.tmpScale.Lld     = 0;
motorModel.tmpScale.Llq     = 0;
motorModel.tmpScale.Ns      = 1;
motorModel.tmpScale.l       = 1;
motorModel.tmpScale.R       = 1;
motorModel.tmpSkew.thSkw    = 0;
motorModel.tmpSkew.nSlice   = 1;
motorModel.tmpSkew.nPoints  = 51;

%% ── 4. TnSetup (효율맵 계산 조건) ──────────────────────────────────────────
Tw.nCurrent   = 1;
Tw.nmin       = 0;
Tw.nmax       = nmax;
Tw.nstep      = 17;
Tw.Tmin       = 0;
Tw.Tmax       = 500;
Tw.Tstep      = 21;
Tw.temperature= tempCu;
Tw.MechLoss   = 0;

if isfield(m, 'IronPMLossMap_dq')
    Tw.IronLossFlag = 'Yes';
    Tw.PMLossFlag   = 'Yes';
else
    Tw.IronLossFlag = 'No';
    Tw.PMLossFlag   = 'No';
end
Tw.IronLossFactor = 1;
Tw.PMLossFactor   = 1;

% SkinEffect: FluxMap_dq에 AC 손실 데이터 있으면 자동 활성화
hasAcLoss = isfield(m.FluxMap_dq, 'Pac_total_kW') && isfield(m.FluxMap_dq, 'speed_vec');
if hasAcLoss
    Tw.SkinEffectFlag   = 'Yes';
    Tw.SkinEffectMethod = 'LUT';
else
    Tw.SkinEffectFlag   = 'No';
    Tw.SkinEffectMethod = 'LUT';
end

Tw.Control      = 'Max efficiency';
Tw.ASCsafeFlag  = 'No';
motorModel.TnSetup = Tw;

%% ── 5. acLossFactor 빌드 ────────────────────────────────────────────────────
%   FluxMap_dq.Pac_total_kW (3D) → SyRE acLossFactor (speed-dependent kAC)
%   kAC = Rac_slot / Rdc_slot, SyRE calcRsTempFreq에서 사용
if hasAcLoss
    fprintf('buildMotorModelForSyre: acLossFactor 빌드 중...\n');
    motorModel.acLossFactor = mcad.buildAcLossFactor( ...
        m.FluxMap_dq, Rs0, tempCu, l, lend, p);
else
    motorModel.acLossFactor = [];
end

%% ── 6. 플레이스홀더 ─────────────────────────────────────────────────────────
motorModel.FluxMap_dqt          = [];
motorModel.DemagnetizationLimit = [];
motorModel.controlTrajectories  = [];
motorModel.IncInductanceMap_dq  = [];
motorModel.FluxMapInv_dq        = [];
motorModel.FluxMapInv_dqt       = [];
motorModel.SyreDrive            = [];
motorModel.WaveformSetup        = [];
motorModel.dataSet.pShape.rotor  = [];
motorModel.dataSet.pShape.stator = [];
motorModel.dataSet.pShape.magnet = [];
motorModel.dataSet.pShape.slot   = [];
motorModel.dataSet.pShape.flag   = 0;
motorModel.dataSet.custom        = 0;
end


%% ── 로컬 헬퍼: 안전한 중첩 필드 접근 ────────────────────────────────────────
function val = safeGet(s, fields, default)
%SAFEGET  중첩 구조체 필드를 안전하게 읽기 (없으면 default 반환)
val = default;
cur = s;
for i = 1:numel(fields)
    if isstruct(cur) && isfield(cur, fields{i})
        cur = cur.(fields{i});
    else
        return;
    end
end
if isnumeric(cur) && isscalar(cur) && ~isnan(cur)
    val = double(cur);
end
end


%% ── 로컬 헬퍼: NaN 파라미터 경고 + 기본값 ───────────────────────────────────
function [p, Rs0, l, lend, Vdc, Imax, nmax, tempCu] = applyDefaults(p, Rs0, l, lend, Vdc, Imax, nmax, tempCu)
defaults = struct('p',4, 'Rs0',0.063783, 'l',0.150, 'lend',0.040, ...
                  'Vdc',720, 'Imax',650.54, 'nmax',16000, 'tempCu',20);
names    = {'p','Rs0','l','lend','Vdc','Imax','nmax','tempCu'};
vals     = {p, Rs0, l, lend, Vdc, Imax, nmax, tempCu};
for k = 1:numel(names)
    if isnan(vals{k})
        defVal = defaults.(names{k});
        warning('buildMotorModelForSyre: %s를 Motor-CAD에서 읽지 못함 → 기본값 %.4g 사용', ...
                names{k}, defVal);
        vals{k} = defVal;
    end
end
[p, Rs0, l, lend, Vdc, Imax, nmax, tempCu] = deal(vals{:});
end
