function BuildList = getBuildListFromMotFileList(MotFileList)
    MotFileQuantity = length(MotFileList);
    BuildList = cell(MotFileQuantity, 2);
    index = 1; % BuildList의 색인

    for i = 1:MotFileQuantity
        modifiedData = getDataFromMotFiles(MotFileList{i});
        LabSatuDateIndex=find(contains(modifiedData, 'LabModel_Saturation_Date'));
        BuildList{index, 1} =modifiedData{LabSatuDateIndex} ;   

        CurrentMotPathIndex=find(contains(modifiedData, 'CurrentMotFilePath_MotorLAB'));
        BuildList{index, 2} =modifiedData{CurrentMotPathIndex} ;   
        BuildList{index,3}= MotFileList{i};

        % for cellRowIndex = 1:length(modifiedData)
        %     if contains(modifiedData{cellRowIndex}, 'LabModel_Saturation_Date')
        %         BuildList{index, 1} = modifiedData{cellRowIndex}; % 색인 위치에 값을 할당
        %     end
        %     % if contains(modifiedData{cellRowIndex}, 'CurrentMotFilePath_MotorLAB')
        %     %     BuildList{index, 2} = modifiedData{cellRowIndex}; % 색인 위치에 값을 할당
        %     %     BuildList{index, 2} = MotFileList{cellRowIndex}; % 색인 위치에 값을 할당
        %     % end
        % end
        if any(~cellfun(@isempty, BuildList(index, :))) % 현재 행에 값이 있는 경우에만 인덱스 증가
            index = index + 1 % 색인 업데이트
        end
    end
end

      