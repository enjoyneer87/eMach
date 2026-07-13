function tf = checkMotCatalogVersion(motPath, catalogVersion)
%MCAD.CHECKMOTCATALOGVERSION  .mot 버전 ↔ 카탈로그 버전 일치 검사(경고)
%
%   tf = mcad.checkMotCatalogVersion(motPath, catalogVersion)
%
%   .mot 파일의 Program_Version 과, 현재 사용 중인 ActiveX 카탈로그(.mat)의
%   버전이 같은 Motor-CAD 버전인지 대조한다. 다르면 warning 을 띄운다
%   (파라미터 누락/오매칭 위험을 사전에 알림). 하드 에러는 내지 않는다.
%
%   Inputs
%   ------
%   motPath        : .mot 파일 경로
%   catalogVersion : 카탈로그 버전 토큰 (예: '261')
%                    — mcad.loadActiveXCatalog 의 2번째 출력값
%
%   Output
%   ------
%   tf : true(일치/판정불가) | false(불일치 경고됨)
%
%   See also: mcad.getMotProgramVersion, mcad.loadActiveXCatalog

    tf = true;

    motV = mcad.getMotProgramVersion(motPath);
    if isempty(motV.majorMinor)
        % .mot 에서 버전을 못 읽음 → 검사 생략(조용히)
        return;
    end

    % .mot 에 기록된 버전 필드들을 함께 표시 (존재하는 것만)
    parts = {};
    if ~isempty(motV.programVersion)
        parts{end+1} = sprintf('Program_Version=%s', motV.programVersion);
    end
    if ~isempty(motV.motFileProgramVersion)
        parts{end+1} = sprintf('MOTFile_Program_Version=%s', motV.motFileProgramVersion);
    end
    if ~isempty(motV.versionLab)
        parts{end+1} = sprintf('Version_Lab=%s', motV.versionLab);
    end
    fprintf('  [버전] .mot: %s  (대표: %s=%s)\n', ...
            strjoin(parts, ', '), motV.source, motV.raw);

    expected = catalogTokenToMotMajorMinor(catalogVersion);

    if isempty(expected)
        % 카탈로그 토큰↔.mot버전 대조표에 없는 버전 → 정보만 출력
        fprintf('  [버전] .mot Program_Version=%s ↔ 카탈로그 v%s (대조표 미등록, 검사 생략)\n', ...
                motV.raw, catalogVersion);
        return;
    end

    if strcmp(motV.majorMinor, expected)
        fprintf('  [버전확인] .mot=%s ↔ 카탈로그 v%s (%s): 일치\n', ...
                motV.raw, catalogVersion, expected);
    else
        tf = false;
        warning('mcad:checkMotCatalogVersion:mismatch', ...
            ['.mot 파일 버전(%s)과 카탈로그 버전(v%s ≈ %s)이 다릅니다.\n' ...
             '         → 파라미터 누락/오매칭 위험. 해당 버전의 ' ...
             'ActiveXParametersMotorCADv<ver>.txt 를 준비해\n' ...
             '         mcad.loadActiveXCatalog(''<ver>'') 로 맞추는 것을 권장합니다.'], ...
            motV.raw, catalogVersion, expected);
    end
end


function mm = catalogTokenToMotMajorMinor(token)
%CATALOGTOKENTOMOTMAJORMINOR  카탈로그 토큰 → 기대되는 .mot major.minor
%   알려진 매핑만 반환. 신규 버전은 여기 한 줄 추가.
%   (예: 토큰 '261' = Motor-CAD 2026.1)
    if nargin < 1 || isempty(token)
        mm = '';
        return;
    end
    token = char(token);
    map = {
        '261' , '2026.1'
        '251' , '2025.1'
        '2522', '2025.2'
        '212' , '2021.2'
    };
    idx = find(strcmp(map(:,1), token), 1);
    if isempty(idx)
        mm = '';
    else
        mm = map{idx, 2};
    end
end
