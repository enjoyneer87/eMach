function CSVTab =parsMCADInterface2CoilsTable(TotalCoilTable,wdgTabCellperPhRowNParaCol,slotArray,LayerArray)
% GroupNumber               =RadialPosIndex/qSlotcatIndex
% NumcoilsTablesPerPhPara   =GroupNumber * qSlotcatIndex  
%                           =RadialPosIndex/qSlotcatIndex*qSlotcatIndex
%                           =RadialPosIndex
% NumTotalCoilsTable = PhaseNumber*ParallelPathNumber * RadialPosIndex;
%% From JMAG JFT145 Style 
% PhaseIndex * 
coilTableNumber=0;
cellTableArray = cell(height(wdgTabCellperPhRowNParaCol), width(wdgTabCellperPhRowNParaCol));
CSVTab     = mkCoilsTable(slotArray,{});  % 빈 SlotLayerTable만들기 
PosCatList                                = categories(TotalCoilTable.GoRadialPosition);

    for PhaseIndex=1:height(wdgTabCellperPhRowNParaCol)
        for ParaPathIndex=1:width(wdgTabCellperPhRowNParaCol)
            TableCellperGroups=cell(1, 1);
            curPhaseParaCoils=TotalCoilTable(TotalCoilTable.PhaseNumber==num2str(PhaseIndex)&TotalCoilTable.ParallelPath==num2str(ParaPathIndex),:);
            %% KeyPoint 분류 - 테이블이름때문에 헷갈리지말것/Layer&Group별로(나눔)/
            for RadialPosIndex=1:length(PosCatList)
                CoilGroup       =curPhaseParaCoils(curPhaseParaCoils.GoRadialPosition==PosCatList{RadialPosIndex},:);
                if ~isempty(CoilGroup)
                    TableWithGroups = groupCoilsByConsecutiveNumbers(CoilGroup);
                    TableWithGroups.GroupNumber         = categorical(TableWithGroups.GroupNumber);
                    GroupNumber                         = length(categories(TableWithGroups.GroupNumber));
                        for qSlotcatIndex=1:GroupNumber
                            BoolcurCoilTable=TableWithGroups.GroupNumber==num2str(qSlotcatIndex);
                            curCoilTable    =TableWithGroups(BoolcurCoilTable,:);
                            TableCellperGroups{RadialPosIndex,qSlotcatIndex}=curCoilTable;
                            %% keyPoint 4*2인데 실제 알고리즘때문에 4개만 남음
                            TableCellperGroups = removeEmptyCells(TableCellperGroups);
                            TableCell1Phase1Para=TableCellperGroups;                     
                        end
                end    
                cellTableArray{PhaseIndex, ParaPathIndex}=TableCell1Phase1Para;
            end
            %% 위에는 반복문 (RadialPos/qslot)과 분리 - 통째로 넣기위해 여전히 Phase별/ParaPath별임
            for singleCoilsTableIndex=1:height(TableCell1Phase1Para)  % 여러 table들 하나 고르기
                    coilTableNumber              =coilTableNumber+1;
                    CoilInfoTable                =mkCoilInfoTable(slotArray,PhaseIndex,ParaPathIndex,length(LayerArray),coilTableNumber);
                    CoilsTable                   =mkCoilsTable(slotArray,LayerArray);                               % 빈 SlotLayerTable만들기 
                    SingleCoilTable             =TableCell1Phase1Para{singleCoilsTableIndex}; % 테이블하나
                    for CoilNumberIndex=1:height(SingleCoilTable)      % 테이블행선택
                        GoSlotIndex               =SingleCoilTable.GoSlot{CoilNumberIndex};
                        GoSlotIndex               =str2double(GoSlotIndex);
                        GoRadialPosIndex          =SingleCoilTable.GoRadialPosition(CoilNumberIndex);
                        GoRadialPosIndex          =double(char(GoRadialPosIndex)) - double('a') + 1;
                        ReSlotIndex               =SingleCoilTable.ReturnSlot{CoilNumberIndex};
                        ReSlotIndex               =str2double(ReSlotIndex);
                        ReRadialPosIndex          =SingleCoilTable.ReturnRadialPosition(CoilNumberIndex);
                        %%[TC[ Key - JMAG Coil에서 인식문제..
                        ReRadialPosIndex          =double(char(ReRadialPosIndex)) - double('a') + 1;
                        % ReRadialPosIndex          = GoRadialPosIndex;
                        %% 테이블에 값넣기
                        CoilsTable{GoRadialPosIndex,GoSlotIndex}={num2str(2*CoilNumberIndex-1)};  % Coil번호할당하는거
                        CoilsTable{ReRadialPosIndex,ReSlotIndex}={num2str(2*CoilNumberIndex)};    % Coil번호할당하는거
                    end
                    CSVTab=[CSVTab; CoilInfoTable; CoilsTable];
            end
        end
    end    
end