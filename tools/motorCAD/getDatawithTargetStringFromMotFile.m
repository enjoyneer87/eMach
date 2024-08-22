function dataCell = getDatawithTargetStringFromMotFile(MotFile,targetString)
    dataCell = {};
    modifiedData = getDataFromMotFiles(MotFile);
    for cellRowIndex = 1:length(modifiedData)
        if contains(modifiedData{cellRowIndex}, targetString)
            dataCell{end+1} = modifiedData{cellRowIndex}; % 색인 위치에 값을 할당
        end
    end
end
