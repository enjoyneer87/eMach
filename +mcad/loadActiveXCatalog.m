function [ActiveXParametersStruct, version] = loadActiveXCatalog(version)
%MCAD.LOADACTIVEXCATALOG  버전별 Motor-CAD ActiveX 파라미터 카탈로그 로드(+자동 캐시)
%
%   [ActiveXParametersStruct, version] = mcad.loadActiveXCatalog()      % 기본 버전(261)
%   ActiveXParametersStruct            = mcad.loadActiveXCatalog('261') % 버전 명시
%
%   2번째 출력 version 은 실제 로드한 카탈로그의 버전 토큰(char, 예: '261').
%   → mcad.checkMotCatalogVersion 으로 .mot 버전과 대조할 때 사용.
%
%   설계 원칙 (Motor-CAD 버전업 관리)
%   --------------------------------
%   * Source of truth = 사람이 읽을 수 있고 버전명이 박힌 txt:
%       eMach/ActiveXParametersMotorCADv<version>.txt   (git 에 커밋)
%   * .mat 은 단순 '빌드 캐시'. txt 보다 오래됐거나 없으면 자동 재생성한다.
%       eMach/tools/mcadActiveXparameterList_v<version>.mat
%   * 같은 세션 내 반복 호출은 persistent 캐시로 즉시 반환 (파일 IO 0회).
%
%   이렇게 하면:
%     (1) "오래된 .mat" 으로 인한 파라미터 누락 → txt 갱신만으로 해결
%     (2) 경로상 동명 .mat 2개(tools\, SkkuEMLabProject\) 모호성 → 절대경로로 제거
%     (3) 수동 재생성 부담 → txt 교체 시 다음 실행에서 자동 반영
%
%   새 Motor-CAD 버전 적용 절차
%   --------------------------
%     1) MCAD GUI: Scripting → Export ActiveX Parameter List
%     2) eMach/ActiveXParametersMotorCADv<새버전>.txt 로 저장(커밋)
%     3) loadActiveXCatalog('<새버전>') 호출 또는 기본 버전 상수만 갱신
%
%   See also: mcad.genMcadActiveXParameterList, getMcadActiveXTableFromMotFile

    persistent CACHE
    if isempty(CACHE); CACHE = struct(); end

    if nargin < 1 || isempty(version)
        version = '261';   % 이 프로젝트 기준 Motor-CAD 버전 (26.1)
    end
    version = char(version);
    cacheKey = matlab.lang.makeValidName(['v' version]);

    % 0) 세션 캐시 hit → 즉시 반환
    if isfield(CACHE, cacheKey)
        ActiveXParametersStruct = CACHE.(cacheKey);
        return;
    end

    % 경로 해석: 이 파일은 eMach/+mcad/ 아래 → 상위가 eMach 루트
    emachRoot = fileparts(fileparts(mfilename('fullpath')));
    txtPath = fullfile(emachRoot, sprintf('ActiveXParametersMotorCADv%s.txt', version));
    matPath = fullfile(emachRoot, 'tools', sprintf('mcadActiveXparameterList_v%s.mat', version));

    ActiveXParametersStruct = [];

    % 1) txt 가 있으면: .mat 이 없거나 txt 보다 오래됐을 때 재생성
    if exist(txtPath, 'file')
        regen = ~exist(matPath, 'file') || isStale(matPath, txtPath);
        if regen
            fprintf('loadActiveXCatalog: v%s 카탈로그 재생성(txt→mat)...\n', version);
            ActiveXParametersStruct = mcad.genMcadActiveXParameterList(txtPath, matPath);
        else
            S = load(matPath);
            ActiveXParametersStruct = S.ActiveXParametersStruct;
        end
    elseif exist(matPath, 'file')
        % txt 없이 캐시 .mat 만 있는 경우
        S = load(matPath);
        ActiveXParametersStruct = S.ActiveXParametersStruct;
    end

    % 2) 레거시 폴백: 버전별 산출물이 전혀 없으면 기존 .mat 을 path 에서 로드
    if isempty(ActiveXParametersStruct)
        warning('mcad:loadActiveXCatalog:fallback', ...
            ['v%s 카탈로그(txt/mat)를 찾지 못해 레거시 mcadActiveXparameterList.mat ' ...
             '으로 폴백합니다. (구버전 카탈로그일 수 있음)'], version);
        S = load('mcadActiveXparameterList.mat');
        ActiveXParametersStruct = S.ActiveXParametersStruct;
    end

    % 3) 세션 캐시에 저장
    CACHE.(cacheKey) = ActiveXParametersStruct;
end


function tf = isStale(matPath, txtPath)
%ISSTALE  .mat 이 txt 보다 오래됐으면 true (재생성 필요)
    dm = dir(matPath);
    dt = dir(txtPath);
    if isempty(dm) || isempty(dt)
        tf = true;
    else
        tf = dm.datenum < dt.datenum;
    end
end
