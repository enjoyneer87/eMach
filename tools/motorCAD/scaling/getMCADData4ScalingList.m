function BuildList = getMCADData4ScalingList(parentPath, scaleFactor)
    MotFileList = findMOTFiles(parentPath)';
    MotFileList = removeAutoSaveFiles(MotFileList);
    MotFileList = MotFileList';
    MotFileList = MotFileList(~contains(MotFileList, 'Scale'));
    % MotFileList = MotFileList(~contains(MotFileList, 'SL'));
    MotFileList = MotFileList(~contains(MotFileList, 'MCAD'));

    % 빌드 리스트를 미리 초기화
    BuildList = repmat(struct('MotFilePath', [], 'SatDate', [], 'SLScaledMachineData', [], 'SLLabTable', [], 'BuildingData', [], 'refTable', []), numel(MotFileList), 1);

    % MATLAB 병렬 풀을 시작 (필요한 경우)
    if isempty(gcp('nocreate'))
        parpool;  % Default pool
    end

    % 루프를 병렬로 실행
    parfor MotFileIndex = 1:length(MotFileList)
        % 각 MOT 파일에 대한 데이터 처리
        [BuildingData, filteredTable] = getMCADData4ScalingFromMotFile(MotFileList{MotFileIndex});
        [SLScaledMachineData, SLLabTable, refTable] = scaleTable4LabTable(scaleFactor, filteredTable, BuildingData);

        % 결과 구조체 업데이트
        if ~isempty(BuildingData.LabModel_Saturation_Date{:})
            BuildList(MotFileIndex).MotFilePath = MotFileList{MotFileIndex};
            BuildList(MotFileIndex).SatDate = BuildingData.LabModel_Saturation_Date{:};
            BuildList(MotFileIndex).SLScaledMachineData = SLScaledMachineData;
            BuildList(MotFileIndex).SLLabTable = SLLabTable;
            BuildList(MotFileIndex).BuildingData = BuildingData;
            BuildList(MotFileIndex).refTable = refTable;
        end
    end
end
