function result = getBuildListResultFromBuildList(BuildList)
  result = {}; % 결과를 저장할 빈 cell 배열 생성
  for caseNum = 1:length(BuildList)
    %% 결과가 있는   
    % BuildData4Check 추출
    BuildDate4Check = strsplit(BuildList{caseNum, 1}, '=');
    buildListMotFilePath = strsplit(BuildList{caseNum, 2}, '=');

    % motFileName, motFileDir 추출
    % partsNameBuildList = strsplit(BuildList{caseNum, 2}, filesep);
    if length(buildListMotFilePath) > 1 && ~isempty(buildListMotFilePath{2})

        BuildDate = BuildDate4Check{end};
        buildListMotFilePath = buildListMotFilePath{2};
        buildListMotFileDir = fileparts(buildListMotFilePath);
        [~, buildListMotFileName, ~] = fileparts(BuildList{caseNum, 2});
        result{end+1, 1} = BuildDate;
        result{end, 5} = buildListMotFilePath;
        result{end, 6} = buildListMotFileDir;
        result{end, 2} = buildListMotFileName;
        result{end, 3} = buildListMotFileName;
        result{end, 4} = caseNum;
    end
    % BuildData4Check의 마지막 요소 추출


    % BuildData가 비어있지 않은 경우 결과에 추가
    % if ~isempty(BuildData) && ~isempty(buildListMotFileDirName)

    
  end
end
