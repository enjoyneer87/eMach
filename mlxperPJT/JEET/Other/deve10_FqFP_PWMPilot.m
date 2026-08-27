%% deve10_FqFP_PWMPilot --- PWM 대역분할 M2 파일럿 (JMAG FP-Fq 경로)
% 작성 2026-08-27.  paper2/PWM_BANDSPLIT_PLAN.md 4절의 M2.
%
% 배경: Motor-CAD 라이선스 불가 → JMAG 경로로 전환 (저자 지시).
% 0단계 선별(run_bandsplit_screen.py)의 판정 = 정현파 조화 꼬리는 혼합
% 산물이라 전달함수 프로브로 부적격, **주입 스펙트럼 실험**이 필요.
% FP(고정 투자율) + Fq(주파수) 해석이 정확히 그 실험이다:
%   온로드 동작점에서 투자율을 얼려 두고, 임의 주파수의 단위 전류를
%   주입해 선형 응답(도체별 줄손실)을 읽는다.
%
% 계보 (2024년 자산 재사용):
%   deve10_FqFPSCL.m           --- FP-Fq 스윕 원형 (200 Hz ~ 20 kRPM 등가)
%   FqSetting.py               --- FrozenPermeability 조건과 참조 케이스
%                                  배선 (D:\KangDH\Thesis\e10\JMAG)
%   devSettingProbeJouleLoss.m --- 도체별 줄손실 프로브
%   exportJMAGAllCaseTables.m  --- 케이스 표 일괄 export
%
% 대상 프로젝트 (포트 38100 = 이 PC):
%   REF_e10_WTPM_PatternD_R1_FqMap_MSFp.jproj
%   SCL_e10_WTPM_PatternD_R1_16kMapZM_FqwMSFP.jproj
%
% 파일럿 목표 (본 캠페인 아님):
%   P1  주파수 목록을 캐리어 대역까지 확장해 Fq 해석이 도는지 확인
%   P2  도체별 줄손실 → AF_hi(f) = P_TS,fq / P_cap(f) 1차 곡선
%   P3  REF vs SCL 같은 f 에서 비교 → k_r 스케일링 (H2 1차 판정)
%   (H1 판정은 MQS 과도 1점과의 교차가 필요 --- P4, 아래 주석)

%% 경로 분기 (기존 관례)
PortNumber=getPCRDPPortNumber();
if PortNumber==38100
    defaultPath='D:\KangDH\Thesis\e10\JMAG';
    outPath='D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\map_exports\e10\pwm_pilot\';
elseif PortNumber==38002
    defaultPath='Z:/Simulation/JEETACLossValid_e10_v24/JMAG';
    outPath='Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\JEET\map_exports\e10\pwm_pilot\';
end
if ~exist(outPath,'dir'); mkdir(outPath); end

%% 파일럿 주파수 목록 [Hz]
% 저대역 앵커 3점 (기존 Fq 스윕과 겹쳐 연속성 확인) +
% 캐리어 3대역 x {측대역-500, 캐리어, +500}
freqEList=[ 500 1000 2000 ...
            4500 5000 5500 ...
            9500 10000 10500 ...
            19500 20000 20500 ]';
maxNoiter=repmat(50,numel(freqEList),1);

%% 대상 프로젝트
JPJTList=findJPJTFiles(defaultPath);
PilotList=[ JPJTList(contains(JPJTList,'REF','IgnoreCase',true) & ...
                     contains(JPJTList,'MSFp','IgnoreCase',true)); ...
            JPJTList(contains(JPJTList,'SCL','IgnoreCase',true) & ...
                     contains(JPJTList,'FqwMSFP','IgnoreCase',true)) ];
assert(~isempty(PilotList),'FP-Fq 프로젝트를 못 찾았다: %s',defaultPath)
disp(PilotList)

%% 실행
app=callJmag;
for PJTIndex=1:numel(PilotList)
    app.Load(PilotList{PJTIndex})
    app.Show
    curStudyObj=app.GetCurrentStudy;
    curStName=char(curStudyObj.GetName());
    assert(contains(curStName,'Fq','IgnoreCase',true), ...
        'Fq 스터디가 아니다: %s',curStName)

    % --- FrozenPermeability 참조 확인 -----------------------------------
    % FqSetting.py 가 배선해 둔 FP 조건의 참조 케이스(온로드 MS 해)가
    % 정격점(460/920 A, beta 36deg)인지 케이스 표에서 확인할 것.
    % 참조가 무부하 해면 주입 응답의 포화 상태가 달라진다.

    % --- 주파수 케이스 확장 --------------------------------------------
    StudyObj=curStudyObj;
    for k=1:numel(freqEList)
        StudyObj.GetStep().SetValue('Frequency',freqEList(k));   % 단일 케이스 실행형
        StudyObj.RunAllCases();
        % 케이스별 설정이 설계표(DesignTable) 기반이면 위 두 줄 대신
        % 설계표에 Frequency 열을 추가해 12케이스 일괄 실행:
        %   dt=StudyObj.GetDesignTable();
        %   dt.AddParameterVariableName('Frequency Analysis: Frequency');
        %   ... (deve10_FqFPSCL.m 의 케이스 확장 블록 참조)
    end

    % --- 도체별 줄손실 export ------------------------------------------
    % 프로브가 이미 있으면 재사용, 없으면 devSettingProbeJouleLoss 로 생성.
    exportJMAGAllCaseTables(app,'PWMPilot');
end

%% 후처리 (MATLAB 밖)
% export CSV -> run_pwm_pilot_score.py (작성 예정):
%   AF_hi(f) = P_fq(f) / P_cap(f),  P_cap = CAL*prox_g2(f, S_unit, dims)
%   판정 P2: AF_hi 가 f 에 평탄한가 (0단계에서 못 한 진짜 H1 선별)
%   판정 P3: AF_hi^SCL(f) vs AF_hi^REF(f) --- k_r 의존
%
%% P4 (별도 실행) --- MQS 과도 교차 검증 1점
% deve10_JMAG_MQS_ACLoss.m 계보로 REF 정격 1점에
% 기본파 + 캐리어 1톤(10 kHz, 진폭 5% I1) 중첩 전류를 주입,
% FP-Fq 중첩 예측과 총손실 비교 --- 선형 중첩(H1)의 직접 판정.
