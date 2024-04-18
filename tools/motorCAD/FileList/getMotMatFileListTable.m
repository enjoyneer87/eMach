function tbl = getMotMatFileListTable(parentPath)
    % Mot 파일과 Mat 파일을 찾기
    motFileList = findMOTFiles(parentPath)';
    matFileList = findMatFiles(parentPath)';

    % Mot 파일 중 AutoSave가 포함되지 않은 파일 선택
    motFileList = motFileList(~contains(motFileList, 'AutoSave'));

    % Mat 파일 종류별 분류
    isDriveMat = contains(matFileList, 'drive');
    isElecMat = contains(matFileList, 'elecdata');
    isSatuMat = contains(matFileList, 'Satu', 'IgnoreCase', true);

    % 각 파일 종류별 목록 생성
    driveMatFiles = matFileList(isDriveMat);
    elecMatFiles = matFileList(isElecMat);
    satuMatFiles = matFileList(isSatuMat);
    otherMatFiles = matFileList(~(isDriveMat | isElecMat | isSatuMat));

    % 파일명, 파일종류, 상대경로, 상위경로를 저장할 변수 초기화
    allFiles = [motFileList; driveMatFiles; elecMatFiles; satuMatFiles; otherMatFiles];
    numFiles = numel(allFiles);
    fileNames = cell(numFiles, 1);
    fileTypes = cell(numFiles, 1);
    fileDirs = cell(numFiles, 1);
    parentPaths = cell(numFiles, 1); % 상위 경로 저장을 위한 셀 배열 초기화

    % 파일 정보 추출
    for i = 1:numFiles
        [path, name, ext] = fileparts(allFiles{i});
        fileNames{i} = [name ext]; % 확장자를 포함한 파일 이름
        relativeDir = strrep(path, parentPath,''); % 상대 디렉토리 추출 
        fileDirs{i} = relativeDir;
        parentPaths{i} = parentPath; % 모든 파일에 대해 상위 경로 저장

        % 파일 타입 설정
        if i <= numel(motFileList)
            fileTypes{i} = 'motFile';
        elseif i <= numel(motFileList) + numel(driveMatFiles)
            fileTypes{i} = 'DutyCycleMatFile';
        elseif i <= numel(motFileList) + numel(driveMatFiles) + numel(elecMatFiles)
            fileTypes{i} = 'ElecMatFile';
        elseif i <= numel(motFileList) + numel(driveMatFiles) + numel(elecMatFiles) + numel(satuMatFiles)
            fileTypes{i} = 'SatuMatFile';
        else
            fileTypes{i} = 'OtherMatFile';
        end
    end

    % 결과를 테이블로 조합
    tbl = table(fileNames, fileTypes, fileDirs, parentPaths, ...
                'VariableNames', {'FileName', 'FileType', 'FileDir', 'ParentPath'});
end

