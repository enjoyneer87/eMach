function result = getBuildListResultFromBuildList(BuildList)
  result = {}; % 결과를 저장할 빈 cell 배열 생성
  for caseNum = 1:length(BuildList)
    % BuildData4Check 추출
    BuildData4Check = strsplit(BuildList{caseNum, 1}, '=');

    % motFileName, motFileDir 추출
    partsNameBuildList = strsplit(BuildList{caseNum, 2}, filesep);
    buildListMotFileDirName = partsNameBuildList{end - 1};
    [~, buildListMotFileName, ~] = fileparts(BuildList{caseNum, 2});

    % BuildData4Check의 마지막 요소 추출
    BuildData = BuildData4Check{end};

    % BuildData가 비어있지 않은 경우 결과에 추가
    if ~isempty(BuildData)
      result{end+1, 1} = BuildData;
      result{end, 2} = buildListMotFileDirName;
      result{end, 3} = buildListMotFileName;
      result{end, 4} = caseNum;
    end
  end
end
