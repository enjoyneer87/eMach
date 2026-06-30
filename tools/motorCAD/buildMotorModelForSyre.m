
%% ═══════════════════════════════════════════════════════════════════════════════
%% 하위 함수: SyRE 호환 motorModel 구조체 초기화
%% ═══════════════════════════════════════════════════════════════════════════════
function motorModel = buildMotorModelForSyre(matPath)
m = load(matPath);
motorModel = struct();
motorModel.FluxMap_dq = m.FluxMap_dq;
if isfield(m, 'IronPMLossMap_dq')
    motorModel.IronPMLossMap_dq = m.IronPMLossMap_dq;
end

% 1) 기본 모터 하드웨어 파라미터 설정
motorModel.data.motorType = 'PM';
motorModel.data.axisType  = 'PM';   % SyRE 표준 PM 규약 (Id<0 감자, Iq>0 토크)
%   ※ axisType='dq'는 calcTnPoint.m switch에 case 없어 IHWC 오류 발생
%     eMach/tools/syre/calcTnPoint.m 패치버전이 'dq' case를 추가하나
%     Tem(Id==0)=0 처리(line 83~88)가 'PM'에서만 물리적으로 정확하므로 'PM' 유지
motorModel.data.pathname  = [fileparts(matPath) filesep];

[~, name, ~] = fileparts(matPath);
motorModel.data.motorName = name;
motorModel.data.p         = 4;          % 극쌍수 (e10 = 8P -> p=4)
motorModel.data.Rs        = 0.063783;   % Stator DC resistance at 20C (Ohm)
motorModel.data.n0        = 500;
motorModel.data.nmax      = 16000;
motorModel.data.Imax      = 650.54;     % Peak Phase Current (460 * sqrt(2) A_pk)
motorModel.data.Vdc       = 720;        % DC Link Voltage (V_pk_max * sqrt(3) V)
motorModel.data.tempCu    = 20;         % Target temp for Rs (20 C)
motorModel.data.tempPM    = 80;
motorModel.data.n3phase   = 1;
motorModel.data.l         = 0.150;      % Active stack length [m] (e10 = 150mm)
motorModel.data.lend      = 0.040;      % End winding length [m] (40mm)
motorModel.dataSet.TypeOfRotor = 'PM';
motorModel.dataSet.RatedCurrent = 460;
motorModel.dataSet.NumOfPolePairs = 4;
motorModel.dataSet.Rs = 0.063783;
motorModel.dataSet.TargetCopperTemp = 20;
motorModel.dataSet.tempPP = 80;
motorModel.dataSet.TurnsInSeries = 1;
motorModel.dataSet.StackLength = 0.150;
motorModel.dataSet.EndWindingsLength = 0.040;
motorModel.dataSet.StatorOuterRadius = 1;

% 2) scaleFactors / skewData (스케일링/스큐 미적용 기본값)
motorModel.tmpScale.Lld = 0;
motorModel.tmpScale.Llq = 0;
motorModel.tmpScale.Ns  = 1;
motorModel.tmpScale.l   = 1;
motorModel.tmpScale.R   = 1;
motorModel.tmpSkew.thSkw = 0;
motorModel.tmpSkew.nSlice = 1;
motorModel.tmpSkew.nPoints = 51;

% 3) TnSetup (Tw) 효율맵 분석 조건 설정
Tw.nCurrent         = 1;
Tw.nmin             = 0;
Tw.nmax             = 16000;
Tw.nstep            = 17;        % 속도 17포인트
Tw.Tmin             = 0;
Tw.Tmax             = 500;
Tw.Tstep            = 21;        % 토크 21포인트
Tw.temperature      = 20;
Tw.MechLoss         = 0;
if isfield(m, 'IronPMLossMap_dq')
    Tw.IronLossFlag   = 'Yes';
    Tw.PMLossFlag     = 'Yes';
else
    Tw.IronLossFlag   = 'No';
    Tw.PMLossFlag     = 'No';
end
Tw.IronLossFactor   = 1;
Tw.PMLossFactor     = 1;

% AC loss (SkinEffect) 플래그 — FluxMap_dq에 AC 손실 데이터가 있으면 자동 활성화
if isfield(m.FluxMap_dq, 'Pac_total_kW') && isfield(m.FluxMap_dq, 'speed_vec')
    Tw.SkinEffectFlag   = 'Yes';
    Tw.SkinEffectMethod = 'LUT';   % interp1(f, k, freq) 방식
else
    Tw.SkinEffectFlag   = 'No';
    Tw.SkinEffectMethod = 'LUT';
end

Tw.Control          = 'Max efficiency'; % 최대 효율 제어 법칙 탐색
Tw.ASCsafeFlag      = 'No';

motorModel.TnSetup = Tw;

% 4) acLossFactor 빌드 (FluxMap_dq에 AC 손실 데이터가 있으면 자동 변환)
%    ─ calcRsTempFreq(Rs0,temp0,l,lend,acLossFactor,method,temp,freq) 호출 시 사용
%    ─ kAC = Rac_slot/Rdc_slot (슬롯 내 활성 도체의 AC/DC 저항 비율)
%    ─ Is^2 가중 평균으로 (Id,Iq) 의존성을 속도 의존성으로 근사
if isfield(m.FluxMap_dq, 'Pac_total_kW') && isfield(m.FluxMap_dq, 'speed_vec')
    fprintf('buildMotorModelForSyre: AC 손실 데이터 검출 → acLossFactor 빌드 중...\n');
    motorModel.acLossFactor = mcad.buildAcLossFactor( ...
        m.FluxMap_dq, ...
        motorModel.data.Rs, ...
        motorModel.data.tempCu, ...
        motorModel.data.l, ...
        motorModel.data.lend, ...
        motorModel.data.p);
else
    motorModel.acLossFactor = [];
end

% 5) 기본 플레이스홀더 설정
motorModel.FluxMap_dqt         = [];
motorModel.DemagnetizationLimit = [];
motorModel.controlTrajectories = [];
motorModel.IncInductanceMap_dq = [];
motorModel.FluxMapInv_dq       = [];
motorModel.FluxMapInv_dqt      = [];
motorModel.SyreDrive           = [];
motorModel.WaveformSetup       = [];
motorModel.dataSet.pShape.rotor  = [];
motorModel.dataSet.pShape.stator = [];
motorModel.dataSet.pShape.magnet = [];
motorModel.dataSet.pShape.slot   = [];
motorModel.dataSet.pShape.flag   = 0;
motorModel.dataSet.custom        = 0;
end
