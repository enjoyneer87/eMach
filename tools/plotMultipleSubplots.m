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
        elseif isstruct(matList)
        matData1=matList;
        subPlotList=fieldnames(matData1);
        else
        matData1=load(matList.ElecMatFileList{1});
        matData2=load(matList.ElecMatFileList{2});
        subPlotList=fieldnames(matData1);
        end
    end
    %%
    if ischar(matList)
    charCell = getVarNameFromMatfileByType(matList,'char');
    varsStrWithHeight1 = getVariablesHeight1FromMatFile(matList);
    elseif isstruct(matList)
    charCell = getVarNameFromMatData(matList,'char');
    varsStrWithHeight1=getVariablesHeight1FromMatData(matList); 
    else
    charCell = getVarNameFromMatfileByType(matList(1).ElecMatFileList{1},'char');
    varsStrWithHeight1 = getVariablesHeight1FromMatFile(matList(1).ElecMatFileList{1});
    end
    %% deleteCell
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Sleeve_Loss');
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Coefficient');      
    subPlotList = removeCellwithMatchingStr(subPlotList, 'rms');      
    subPlotList = removeCellwithMatchingStr(subPlotList, 'RMS');      
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Unit');      
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Constant');      
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Line');    
    subPlotList = removeCellwithMatchingStr(subPlotList, 'var');    
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Temp');      
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Speed');              
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Frequency');              
    subPlotList = removeCellwithMatchingStr(subPlotList, 'Idc');              
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
    %% TorqueCell
    typeStrt.TorqueCell= getCellwithMatchingStr(subPlotList, 'torque');
    if isempty(typeStrt.TorqueCell)
        typeStrt=rmfield(typeStrt,"TorqueCell");
    end
    %% Other cell

    [otherCell, ~, ~]                               =findUniqueAndNonUniqueStrings(subPlotList,typeStrt.voltageCell);
    [otherCell, ~, ~]                               =findUniqueAndNonUniqueStrings(otherCell,typeStrt.IronLossCell);
    [otherCell, ~, ~]                               =findUniqueAndNonUniqueStrings(otherCell,typeStrt.LossCell);
    [otherCell, ~, ~]                               =findUniqueAndNonUniqueStrings(otherCell,typeStrt.TorqueCell);
    [typeStrt.otherCell, string2Delete, ~]          =findUniqueAndNonUniqueStrings(otherCell,varsStrWithHeight1);
    %% string2Delete
    [typeStrt.voltageCell, ~, ~]              =findUniqueAndNonUniqueStrings(typeStrt.voltageCell, string2Delete);
    [typeStrt.IronLossCell, ~, ~]             =findUniqueAndNonUniqueStrings(typeStrt.IronLossCell,string2Delete);
    [typeStrt.LossCell, ~, ~]                 =findUniqueAndNonUniqueStrings(typeStrt.LossCell,    string2Delete);  
    [typeStrt.TorqueCell, ~, ~]               =findUniqueAndNonUniqueStrings(typeStrt.TorqueCell,    string2Delete);  
    %% 
    % importMatfile(matList.ElecMatFileList{1}, matDataFieldName)
    % matData1=rmfieldByType(matData1,'char');
    % matData2=rmfieldByType(matData2,'char');
    % varNamesCell = getVariablesHeight1FromMatFile(matFileName)
    %% Data입력
    typestrtNames=fieldnames(typeStrt);
    for cellIndex=1:length(typestrtNames)
        cellName=typestrtNames{cellIndex};        
        if ~isempty(typeStrt.(cellName))          
            structbyType.(cellName) = filterFieldwithStrCellFromStruct(matData1,typeStrt.(cellName) );
            structbyType.(cellName) = filterFieldNanorZeros(structbyType.(cellName));
            structbyType.(cellName).Speed=matData1.Speed;
            structbyType.(cellName).Shaft_Torque=matData1.Shaft_Torque;               
            structbyTypeNames=fieldnames(structbyType);     
        end
    end
    %% figure 생성
    for strctIndex=1:length(structbyTypeNames)
        structName=structbyTypeNames{strctIndex};
        % cellName=typestrtNames{strctIndex};
        [~, ~, nonUniqueStrings] = findUniqueAndNonUniqueStrings(fieldnames(structbyType.(structName)), typeStrt.(structName));
        plotSubPlotTNContour(plotFunction,structbyType.(structName),nonUniqueStrings); 
    end

    % plotSubPlotTNContour
    % plotTNContour

    a=findobj('type','figure');
    setSubplotFontProperties(a, 'Times New Roman', 8);


end
