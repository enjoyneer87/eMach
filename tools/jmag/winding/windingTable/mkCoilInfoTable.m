function CoilInfoTable=mkCoilInfoTable(slotArray,PhaseIndex,ParallelNumberIndex,LayerNumber,CoilTableNumber)
    %% nargin
    if nargin<5
    CoilTableNumber= (PhaseIndex+3*(ParallelNumberIndex-1));
    end
    %% 공통 변수와 행 개수 설정
    NumSlots        =length(slotArray);      %numVariables    =NumSlots;
    NumRadPosition  =LayerNumber;     %numRows         =NumRadPosition
    %% 빈 테이블 생성
    emptyCharCell = repmat({' '}, NumRadPosition, NumSlots);
    CoilInfoTable = cell2table(emptyCharCell);
    % 변수 이름 설정 (앞에 'Slot'을 붙임)
    variableNames = cellfun(@(x) sprintf('Slot%d', x), num2cell(1:NumSlots), 'UniformOutput', false);     % 변수 이름 설정 (앞에 'Slot'을 붙임)
    CoilInfoTable.Properties.VariableNames = variableNames;
  
    %% 생성
    CoilInfoTable.Slot1{1}=['Name_',                num2str(CoilTableNumber)];
    CoilInfoTable.Slot1{2}=['PhaseIndex_',          num2str(CoilTableNumber)];
    CoilInfoTable.Slot1{3}=['SerialGroupIndex_',    num2str(CoilTableNumber)];
    CoilInfoTable.Slot1{4}=['Table_',               num2str(CoilTableNumber)];
    % if PhaseIndex==1
    % CoilInfoTable.Slot2{1}=['Coil U',num2str(ParallelNumberIndex)];
    % elseif PhaseIndex==2
    % CoilInfoTable.Slot2{1}=['Coil V',num2str(ParallelNumberIndex)];
    % elseif PhaseIndex==3
    % CoilInfoTable.Slot2{1}=['Coil W',num2str(ParallelNumberIndex)];
    % end
    CoilInfoTable.Slot2{1}= ['Coil',num2str(CoilTableNumber)];
    CoilInfoTable.Slot2{2}= num2str(PhaseIndex-1);
    CoilInfoTable.Slot2{3}= num2str(ParallelNumberIndex-1);
    CoilInfoTable.Slot2{4}= num2str(LayerNumber);
end