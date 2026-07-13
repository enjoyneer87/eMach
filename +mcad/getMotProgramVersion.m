function v = getMotProgramVersion(motPath)
%MCAD.GETMOTPROGRAMVERSION  .mot 파일에서 Motor-CAD 버전 필드 추출
%
%   v = mcad.getMotProgramVersion(motPath)
%
%   .mot 파일에 기록되는 3개의 버전 필드를 읽는다 (모두 [Header] 계열):
%     Program_Version          : 이 .mot 텍스트를 쓴 Motor-CAD 앱 버전 (항상 존재)
%                                → ActiveX 파라미터 '스키마' 버전 = 카탈로그 대조 기준
%     MOTFile_Program_Version  : 현재 로드된 mot 을 저장한 버전 (런타임 성격, 없을 수 있음)
%     Version_Lab              : Lab 모델 데이터 버전 (Lab 파라미터 추출 시 호환성 지표)
%
%   반환 struct
%   -----------
%   v.programVersion          : 'Program_Version' 원문 (예: '2026.1.1.1') | ''
%   v.motFileProgramVersion   : 'MOTFile_Program_Version' 원문 | ''
%   v.versionLab              : 'Version_Lab' 원문 (예: '2026.1.1') | ''
%   v.raw                     : 대표 버전 원문 (우선순위: Program_Version →
%                               MOTFile_Program_Version → Version_Lab) | ''
%   v.majorMinor              : 대표 버전의 major.minor (예: '2026.1') | ''
%   v.source                  : 대표 버전이 어느 필드에서 왔는지 (필드명) | ''
%
%   See also: mcad.checkMotCatalogVersion, mcad.loadActiveXCatalog

    v = struct('programVersion','', 'motFileProgramVersion','', 'versionLab','', ...
               'raw','', 'majorMinor','', 'source','');

    if nargin < 1 || isempty(motPath) || ~exist(motPath, 'file')
        return;
    end

    txt = fileread(motPath);

    % 라인 시작 앵커('lineanchors')로 정확히 매칭
    %   주의: 'MOTFile_Program_Version' 은 'Program_Version' 을 부분문자열로 포함하므로
    %         반드시 줄 시작(^)에 고정해 서로 오인하지 않게 한다.
    v.programVersion        = grabVal(txt, 'Program_Version');
    v.motFileProgramVersion = grabVal(txt, 'MOTFile_Program_Version');
    v.versionLab            = grabVal(txt, 'Version_Lab');

    % 대표 버전 선정 (우선순위)
    candidates = { v.programVersion,        'Program_Version'
                   v.motFileProgramVersion, 'MOTFile_Program_Version'
                   v.versionLab,            'Version_Lab' };
    for i = 1:size(candidates, 1)
        if ~isempty(candidates{i,1})
            v.raw    = candidates{i,1};
            v.source = candidates{i,2};
            mm = regexp(v.raw, '(\d+)\.(\d+)', 'tokens', 'once');
            if ~isempty(mm)
                v.majorMinor = sprintf('%s.%s', mm{1}, mm{2});
            end
            break;
        end
    end
end


function val = grabVal(txt, name)
%GRABVAL  txt 에서 '^<name> = <value>' 의 value 추출 (줄 시작 고정)
    pat = ['^' regexptranslate('escape', name) '\s*=\s*(\S+)'];
    tok = regexp(txt, pat, 'tokens', 'once', 'lineanchors');
    if isempty(tok)
        val = '';
    else
        val = strtrim(tok{1});
    end
end
