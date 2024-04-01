function modifiedTable = filterAndSortVarTablebyNameCell(changedOriginalTable, LabLinkFormatNameCell,MachineData)
    % originalTable에서 LabLinkFormat에 있는 변수만 남기고 변수 순서를 LabLinkFormat에 맞게 정렬
    
    % 변수 이름 가져오기
    varNames = changedOriginalTable.Properties.VariableNames;
   
    %% Filter and Make Table with LabLinkFormat
    varToKeep = intersect(varNames, LabLinkFormatNameCell);
    filteredTable = changedOriginalTable(:, varToKeep);
  
    %% Make AC Loss Table
    ACIndex=contains(LabLinkFormatNameCell,'AC Copper');
    ACNameCell=LabLinkFormatNameCell(ACIndex);   

    ACConductorLossProportion_Lab=convertCharTypeData2ArrayData(MachineData.ACConductorLossProportion_Lab);
   
    numACLossVariables = numel(ACNameCell);

    % ACLossTable 초기화
    ACLoss = zeros(size(originalTable, 1), numACLossVariables);
    ACLossTable=array2table(ACLoss,"VariableNames",ACNameCell);

    % 각 AC Copper Loss 변수에 대한 계산 수행
    for i = 1:numACLossVariables
        ACVarName = ACNameCell{i};
        ACLossTable(:, ACVarName) = changedOriginalTable(:,'Stator Copper Loss AC').* ACConductorLossProportion_Lab(i, :);
    end
    
    %% 합치기 
    modifiedTable=mergeTables(filteredTable,ACLossTable);
    % mergedTable = horzcat(filteredTable, ACLossTable);

   
    %%
    % AddVarCell=setdiff(LabLinkFormatNameCell,varNames);
    % AddVarCell=setdiff(AddVarCell,ACNameCell);
    % 
    % AddTable = changedOriginalTable(:, AddVarCell);

   
    % LabLinkFormat의 순서대로 변수 순서 정렬 (originalTable에 존재하는 변수만 고려)
    % 변수 순서 정렬을 위해 무시할 변수를 제외한 LabLinkFormat 변수만 선택
    % LabLinkFormatToMove = NameCell(ismember(NameCell, varNames));
    
    % 변수 순서 정렬
    % modifiedTable = movevars(filteredTable, LabLinkFormatToMove, 'After', varNames{end});
end