function saveWorkspaceToMatFile(outputFileName)
    % outputFileName: 저장할 .mat 파일의 이름 (예: 'myWorkspace.mat')

    % 작업 공간의 모든 변수들 가져오기
    workspaceVars = whos;

    % 변수들을 저장할 구조체 생성
    dataStruct = struct();

    % 각 변수를 구조체에 추가
    for i = 1:numel(workspaceVars)
        varName = workspaceVars(i).name;
        varValue = evalin('base', varName);
        dataStruct.(varName) = varValue;
    end

    % .mat 파일로 저장
    save(outputFileName, '-struct', 'dataStruct');

    disp(['작업 공간의 변수들이 "', outputFileName, '" 파일로 저장되었습니다.']);
end
