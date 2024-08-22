function scaleList2Build = getMCADData4ScalingList(input2GetData)
%% dev
% input2GetData=OriginFileList
%% input 조건
if isstring(input2GetData)
    MotFileList = findMOTFiles(input2GetData)';
    MotFileList = removeAutoSaveFiles(MotFileList)';
    MotFileList = MotFileList(~contains(MotFileList, 'Scale'));
    MotFileList = MotFileList(~contains(MotFileList, 'SL'));
    MotFileList = MotFileList(~contains(MotFileList, 'MCAD'));
elseif istable(input2GetData)
    MotFileDirList=fullfile(input2GetData.ParentPath,input2GetData.FileDir);
    MotFileList   =fullfile(MotFileDirList,input2GetData.FileName);
elseif iscell(input2GetData)
    MotFileList=input2GetData;
end

%% 빌드 리스트를 미리 초기화
    % BuildList = repmat(struct('MotFilePath', [], 'SatDate', [], 'SLScaledMachineData', [], 'SLLabTable', [], 'BuildingData', [], 'refTable', []), numel(MotFileList), 1);

    scaleList2Build = repmat(struct('MotFilePath', [], 'SatDate', [], 'BuildingData', [], 'refTable', []), numel(MotFileList), 1);

%% MATLAB 병렬 풀을 시작 (필요한 경우)
    if isempty(gcp('nocreate'))
        parpool;  % Default pool
    end

    % 루프를 병렬로 실행
    parfor MotFileIndex = 1:length(MotFileList)

    % for MotFileIndex = 1:length(MotFileList)
        % 각 MOT 파일에 대한 데이터 처리
        disp(MotFileList{MotFileIndex})
        [Data2Scaling4Building, filteredLabTable4Scaling] = getMCADData4ScalingFromMotFile(MotFileList{MotFileIndex});
        % [SLScaledMachineData, SLLabTable, refTable] = scaleTable4LabTable(scaleFactor, filteredTable, BuildingData);

        % 결과 구조체 업데이트
        if ~isempty(Data2Scaling4Building.LabModel_Saturation_Date{:})
            scaleList2Build(MotFileIndex).MotFilePath = MotFileList{MotFileIndex};
            scaleList2Build(MotFileIndex).SatDate = Data2Scaling4Building.LabModel_Saturation_Date{:};
            % BuildList(MotFileIndex).SLScaledMachineData = SLScaledMachineData;
            % BuildList(MotFileIndex).SLLabTable = SLLabTable;
            scaleList2Build(MotFileIndex).BuildingData = Data2Scaling4Building;
            scaleList2Build(MotFileIndex).refTable = filteredLabTable4Scaling;
        end
    end
end
