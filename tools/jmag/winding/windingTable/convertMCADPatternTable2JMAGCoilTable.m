function [coilsTablePerCoil,CSVTab,outputPath] = convertMCADPatternTable2JMAGCoilTable(McadWindingPatternTable,outputPath)
    %% nargin
    if ~istable(McadWindingPatternTable)
    refOutputPath             =strrep(McadWindingPatternTable,'.txt','.csv');
    McadWindingPatternTable=readMCADWindingPatterTXT(McadWindingPatternTable);
    end
    %% [Direct Input CoilTable]MCAD2MCADInterface - 어차피 돌리면 되니까 reverse 할필요없음
    % [NewWindingTable4JMAG, ~]               = renumberMCADSlotNumber(reNumberLayerTable, true);
    [TablePerPhasePara,TotalCoilTable]        = convertMCADPatternTable2MCADInterface(McadWindingPatternTable);  % PhasePara로만 변경
    PosCatList                                = categories(TotalCoilTable.GoRadialPosition);
    %% Count Total CoilNumber
    PhaseNumber             = length(unique(McadWindingPatternTable.PhaseNumber));
    ParallelPathNumber      = length(unique(McadWindingPatternTable.ParallelPathNumber));
    %% 2 JMAG JFT145 Style  > convertMCAD2JmagWireTable로 넘어가기  CoilsTable
    cellTableArray = cell(height(TablePerPhasePara), width(TablePerPhasePara));
    for PhaseIndex=1:height(TablePerPhasePara)
        for ParaPathIndex=1:width(TablePerPhasePara)
            TableCellperGroups=cell(1, 1);
            curPhaseParaCoils=TotalCoilTable(TotalCoilTable.PhaseNumber==num2str(PhaseIndex)&TotalCoilTable.ParallelPath==num2str(ParaPathIndex),:);
            for RadialPosIndex=1:length(PosCatList)
            CoilGroup       =curPhaseParaCoils(curPhaseParaCoils.GoRadialPosition==PosCatList{RadialPosIndex},:);
                if ~isempty(CoilGroup)
                TableWithGroups = groupCoilsByConsecutiveNumbers(CoilGroup);
                TableWithGroups.GroupNumber         = categorical(TableWithGroups.GroupNumber);
                GroupNumber                         = length(categories(TableWithGroups.GroupNumber));
                    for qSlotcatIndex=1:GroupNumber
                        curCoilTable=TableWithGroups.GroupNumber==num2str(qSlotcatIndex);
                        TableCellperGroups{RadialPosIndex,qSlotcatIndex}=TableWithGroups(curCoilTable,:);
                        TableCellperGroups = removeEmptyCells(TableCellperGroups);
                        TableCell=TableCellperGroups;
                    end
                end
            end
            cellTableArray{PhaseIndex, ParaPathIndex}=TableCell;
        end
    end

    %% cell2 Table
    coilsTablePerCoil = cell2table(cellTableArray);
    coilsTablePerCoil.Properties.RowNames         =TablePerPhasePara.Properties.RowNames;
    coilsTablePerCoil.Properties.VariableNames    =TablePerPhasePara.Properties.VariableNames;
    %% Count Total CoilNumber
    PhaseNumber             = length(unique(McadWindingPatternTable.PhaseNumber));
    ParallelPathNumber      = length(unique(McadWindingPatternTable.ParallelPathNumber));
    NumcoilsTablesPerPhPara = height(coilsTablePerCoil{1,1}{:});
    NumTotalCoilsTable      = PhaseNumber*ParallelPathNumber*NumcoilsTablesPerPhPara;
    %% [이거 잘못된거같어]From convertMCAD2JmagWireTable
    %% reNumber   +1
    %% SlotArray  +1
    NewWindingTable                 =renumberSlotNumber(McadWindingPatternTable);
    NewWindingTable                 =renumberCoilNumber(NewWindingTable);
    SlotTable                       = NewWindingTable(contains(NewWindingTable.TypeofData,'Slot'),"ValueTable");
    slotArrayCell                   = unique(SlotTable.ValueTable);
    %% RadPoisition +1 Number
    reNumberLayerTable              = renumberRadialPositionNumber(NewWindingTable);
    reNumberLayerTable              = reverseAlphabetRadialPosition(reNumberLayerTable);
    RadialPosition_LayerTable       = reNumberLayerTable(contains(reNumberLayerTable.TypeofData,'RadialPosition'),"ValueTable");
    cellArray                       = cellfun(@(x) num2str(x), RadialPosition_LayerTable.Variables, 'UniformOutput', false);
    LayerArray                      = unique(cellArray);
    LayerArray                      = cellfun(@(x) str2num(x), LayerArray, 'UniformOutput', false);
    %% 4CSV Table
    %% CSV 첫줄
    CoilPropertiesTable                                 =mkCoilPropertiesTable(slotArrayCell,NumTotalCoilsTable);
    %% !!! KeyPoint
    % coilsTablePerCoil{1,1}{:}{1}
    % From [CoilInfoTableStruct,CoilTableStruct]       = parsPhaseParaMCADTable(wdgTabCellperPhRowNParaCol,slotArrayCell,LayerArray);
    wdgTabCellperPhRowNParaCol                         = parsMCADWindingTableByPhaseRNParaCol(reNumberLayerTable);           
    CSVTab                                             = parsMCADInterface2CoilsTable(TotalCoilTable,wdgTabCellperPhRowNParaCol,slotArrayCell,LayerArray);
    %% out 

    if nargin>1
    outputPath = writeJmagWindingPatternCSV(CSVTab, outputPath);
    else
    outputPath = writeJmagWindingPatternCSV(CSVTab, refOutputPath);
    end
end

