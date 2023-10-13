function plotMultipleSubplots(plotFunction, matList, subPlotList, lastfigure,startfigure)
    % plotFunction: 그래프를 그리는 함수 (함수 핸들)
    % lastfigure: 총 서브플롯의 개수
    if nargin < 5
        startfigure = 1;
    end
    if nargin <3
        if ischar(matList)
            % |length(matList)<2
        matData1=load(matList);
        subPlotList=fieldnames(matData1);
        else
        matData1=load(matList.ElecMatFileList{1});
        matData2=load(matList.ElecMatFileList{2});
        subPlotList=fieldnames(matData1);
        end
    end
    %% deleteCell
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Sleeve_Loss');
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Coefficient');      
        % Voltage Cell
    typeStrt.voltageCell = getCellwithMatchingStr(subPlotList, 'V');
    if isempty(typeStrt.voltageCell)
        typeStrt=rmfield(typeStrt,"voltageCell");
    end
        % Iron Loss Cell
    typeStrt.IronLossCell= getCellwithMatchingStr(subPlotList, 'Iron');     
    if isempty(typeStrt.IronLossCell)
        typeStrt=rmfield(typeStrt,"IronLossCell");
    end
        % Other Loss cell
    LossCell= getCellwithMatchingStr(subPlotList, 'Loss');
    typeStrt.LossCell = removeCellwithMatchingStr(LossCell, 'Iron');
    if isempty(typeStrt.LossCell)
        typeStrt=rmfield(typeStrt,"LossCell");
    end
    % Other cell
    otherCell = removeCellwithMatchingStr(subPlotList, 'Loss');    
    if ischar(matList)
    charCell = getVarNameFromMatfileByType(matList,'char');
    varsStrWithHeight1 = getVariablesHeight1FromMatFile(matList);
    else
    charCell = getVarNameFromMatfileByType(matList(1).ElecMatFileList{1},'char');
    varsStrWithHeight1 = getVariablesHeight1FromMatFile(matList(1).ElecMatFileList{1});
    end
    [uniqueStringsInCell1, uniqueStringsInCell2, nonUniqueStrings] =findUniqueAndNonUniqueStrings(otherCell,charCell);
    [uniqueStringsInCell1,matDataFieldName,c]=findUniqueAndNonUniqueStrings(uniqueStringsInCell1,varsStrWithHeight1);
    otherCell = removeCellwithMatchingStr(uniqueStringsInCell1, 'Temp');      
    otherCell = removeCellwithMatchingStr(otherCell, 'Speed');              
    typeStrt.otherCell = removeCellwithMatchingStr(otherCell, 'V');      
    if isempty(typeStrt.otherCell)
        typeStrt=rmfield(typeStrt,"otherCell");
    end

    %% 
    % importMatfile(matList.ElecMatFileList{1}, matDataFieldName)
    % matData1=rmfieldByType(matData1,'char');
    % matData2=rmfieldByType(matData2,'char');
    % varNamesCell = getVariablesHeight1FromMatFile(matFileName)
    %% figure 생성
    typestrtNames=fieldnames(typeStrt);
    for cellIndex=1:length(typestrtNames)
        cellName=typestrtNames{cellIndex};        
        if ~isempty(typeStrt.(cellName))             
            structbyType.(cellName) = filterFieldwithStrCellFromStruct(matData1,typeStrt.(cellName) );
            structbyType.(cellName).Speed=matData1.Speed;
            structbyType.(cellName).Shaft_Torque=matData1.Shaft_Torque;
            structbyTypeNames=fieldnames(structbyType);     
        end
    end
      
    for strctIndex=1:length(structbyTypeNames)
        structName=structbyTypeNames{strctIndex};
        cellName=typestrtNames{strctIndex};
        plotSubPlotTNContour(plotFunction,structbyType.(cellName),typeStrt.(cellName)); 
    end

    % plotSubPlotTNContour
    % plotTNContour

    a=findobj('type','figure');
    setSubplotFontProperties(a, 'Times New Roman', 8);


end
