function ActiveXParametersStruct = genMcadActiveXParameterList(txtPath, matPath)
%MCAD.GENMCADACTIVEXPARAMETERLIST  Motor-CAD ActiveX 파라미터 카탈로그(.mat) 생성기
%
%   ActiveXParametersStruct = mcad.genMcadActiveXParameterList(txtPath)
%       → txt(파라미터 리스트 export)를 읽어 카테고리별 struct 로 변환만 (저장 안 함)
%
%   mcad.genMcadActiveXParameterList(txtPath, matPath)
%       → 변환 후 matPath 에 'ActiveXParametersStruct' 변수로 저장
%
%   목적
%   ----
%   Motor-CAD GUI 에서 "Scripting → Export ActiveX Parameters" 로 내보낸
%   버전별 파라미터 리스트(예: ActiveXParametersMotorCADv261.txt)를
%   getMcadActiveXTableFromMotFile 이 쓰는 카탈로그(.mat)로 만든다.
%
%   카탈로그는 .mot 파싱 시 "어떤 (Category, AutomationName) 이 유효한지"를
%   정의하는 '스키마' 역할을 한다. Motor-CAD 버전업으로 신규 파라미터/카테고리가
%   생기면, 새 버전 txt 로 이 함수를 다시 돌려 카탈로그를 갱신해야 누락이 없다.
%
%   txt 포맷 (CSV, 헤더 포함)
%   ------------------------
%   Number, Input/Output, Automation Name, Category, Units,
%   Current Value, Default Value, Modified, Data Type, Description
%
%   See also: mcad.loadActiveXCatalog, readMcadActiveX2Table,
%             getMcadActiveXTableFromMotFile

    if nargin < 1 || isempty(txtPath)
        error('mcad:genMcadActiveXParameterList:noTxt', ...
              'txtPath(파라미터 리스트 txt 경로)를 지정해야 합니다.');
    end
    if ~exist(txtPath, 'file')
        error('mcad:genMcadActiveXParameterList:txtNotFound', ...
              'txt 파일이 존재하지 않습니다: %s', txtPath);
    end

    % 1) txt → table (Category 정규화 + categorical 화는 readMcadActiveX2Table 이 수행)
    ActiveXParameters = readMcadActiveX2Table(txtPath);

    % 2) Category 별로 테이블 분할 → struct (createCategoryStruct 로직 인라인)
    %    SkkuEMLabProject 경로 의존 없이 self-contained 하게 동작하도록 인라인함.
    if iscategorical(ActiveXParameters.Category)
        uniqueCategories = categories(ActiveXParameters.Category);
    else
        uniqueCategories = unique(cellstr(ActiveXParameters.Category));
    end

    ActiveXParametersStruct = struct();
    nCat = 0; nVar = 0;
    for i = 1:numel(uniqueCategories)
        category = uniqueCategories{i};
        rows = (ActiveXParameters.Category == category);
        if ~any(rows)
            continue;   % categorical 에 등록만 되고 행이 없는 카테고리는 건너뜀
        end
        % MATLAB 유효 필드명으로 변환 (혹시 모를 잔여 특수문자 방어)
        fieldName = matlab.lang.makeValidName(category);
        ActiveXParametersStruct.(fieldName) = ActiveXParameters(rows, :);
        nCat = nCat + 1;
        nVar = nVar + sum(rows);
    end

    fprintf('genMcadActiveXParameterList: %s\n', txtPath);
    fprintf('  → %d 카테고리, %d 파라미터 파싱 완료\n', nCat, nVar);

    % 3) 저장 (요청 시)
    if nargin >= 2 && ~isempty(matPath)
        save(matPath, 'ActiveXParametersStruct');
        fprintf('  → 카탈로그 저장: %s\n', matPath);
    end
end
