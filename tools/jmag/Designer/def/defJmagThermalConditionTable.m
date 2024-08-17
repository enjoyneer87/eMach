function ThermalConditionTable=defJmagThermalConditionTable(runnerType)

% ThermalStudyConditionTypes=Steady2.GetConditionTypes()
load('JmagThermalStudyConditionType.mat');


% 선택 가능한 카테고리를 ThermalStudyConditionTypes로 가정합니다.

%% ThermalConditionTable 초기화
ThermalConditionTable = table('Size', [100, 7], ...
    'VariableTypes', {'categorical', 'cell', 'cell','cell', 'cell', 'cell', 'cell'}, ...
    'VariableNames', {'ConditionType', 'ConditionName', 'ConditionValueTable','GeomSetName', 'FaceTable', 'CircuitComponent', 'CircuitValueTable'});

%% 선택 가능한 카테고리만 할당
ThermalConditionTable.ConditionType(1:height(ThermalStudyConditionTypes),:) = categorical(ThermalStudyConditionTypes);
PartNameList={'Rotor','Stator','Coil','Magnet'};

%% mk ConditionNameSetList
ConditionNameSetList={};
for partNameIndex=1:length(PartNameList)
    ConditionNameSetListTable = mkConditionNameListTable(PartNameList{partNameIndex},runnerType);
    % 결과 확인
    ConditionNameSetList=[ConditionNameSetList;ConditionNameSetListTable.GeomSetList];
end

%% FaceName
GeomSetFaceNameList=ConditionNameSetList(contains(ConditionNameSetList,'Face','IgnoreCase',true));

%% Condition NameList
% HTBConditionNameSetList=GeomSetFaceNameList(~contains(GeomSetFaceNameList,'Coil End'))

%% Heat Transfer Boundary
HTBConditionNameSetList=strrep(GeomSetFaceNameList,'Core','')                ;       
HTBConditionNameSetList=strrep(HTBConditionNameSetList,'Front','_up')        ;               
HTBConditionNameSetList=strrep(HTBConditionNameSetList,'Back','_low')        ;               
HTBConditionNameSetList=strrep(HTBConditionNameSetList,'Face','')            ;           
HTBConditionNameSetList=strrep(HTBConditionNameSetList,' ','')               ;       
HTBConditionNameSetList=strrep(HTBConditionNameSetList,'Gap','_gap')         ;               
HTBConditionNameSetList=strrep(HTBConditionNameSetList,'Side','_side')       ;               
HTBConditionNameSetList=strrep(HTBConditionNameSetList,'-Shaft','_shaft')    ;                   

CircuitNameList=     HTBConditionNameSetList;     

HTBConditionNameSetList=HTBConditionNameSetList(~contains(HTBConditionNameSetList,'Coil'))
HTBConditionNameSetList=HTBConditionNameSetList(~contains(HTBConditionNameSetList,'Magnet'))


% Set Name[Coil-Core] CustomContactResistanceRotationPattern (No Circuit)
CoilStatorSetNameList=strrep(GeomSetFaceNameList,'Face','')            ; 
CoilStatorSetNameList=strrep(CoilStatorSetNameList,'Stator','')            ;           
CoilStatorSetNameList=strrep(CoilStatorSetNameList,' ','')               ;       
CoilStatorSetNameList=CoilStatorSetNameList(contains(CoilStatorSetNameList,'Coil'));
CoilStatorSetNameList=CoilStatorSetNameList(contains(CoilStatorSetNameList,'Core'));

% Equivalent Temperature Boundary Pattern (CE1, CE2 Circuit)
EquiTempBoundarySetNameList=strrep(GeomSetFaceNameList,'Face','')            ;           
EquiTempBoundarySetNameList=EquiTempBoundarySetNameList(contains(EquiTempBoundarySetNameList,'Coil End'))
EquiTempBoundarySetNameList=strrep(EquiTempBoundarySetNameList,' ','')               ;       
EquiTempBoundarySetNameList=strrep(EquiTempBoundarySetNameList,'Front','_up')        ;               
EquiTempBoundarySetNameList=strrep(EquiTempBoundarySetNameList,'Back','_low')        ;      

% ContactThermalResistancePattern(Rotation) Condition
ContactThermalResistancePatternSetNameList=strrep(GeomSetFaceNameList,'Face','')            ;           
ContactThermalResistancePatternSetNameList=strrep(ContactThermalResistancePatternSetNameList,'Rotor','')            ;           
ContactThermalResistancePatternSetNameList=strrep(ContactThermalResistancePatternSetNameList,' ','')               ;       

ContactThermalResistancePatternSetNameList=ContactThermalResistancePatternSetNameList(contains(ContactThermalResistancePatternSetNameList,'Magnet-Core'));

% Assemble
DefConditionNameList=[HTBConditionNameSetList;CoilStatorSetNameList;EquiTempBoundarySetNameList;ContactThermalResistancePatternSetNameList]

%% Circuit
CircuitComponentList=strrep(CircuitNameList,'Stator','stator')  ;
CircuitComponentList=strrep(CircuitComponentList,'Rotor','rotor')       ;
CircuitComponentList=strrep(CircuitComponentList,'CoilEnd_up','CE1')       ;
CircuitComponentList=strrep(CircuitComponentList,'CoilEnd_low','CE2')       ;


%% Delete Empty GeomSetName
ThermalConditionTable.GeomSetName(1:height(GeomSetFaceNameList))=GeomSetFaceNameList;
emptyGeomSetNameRows = cellfun('isempty', ThermalConditionTable.GeomSetName);
ThermalConditionTable(emptyGeomSetNameRows, :) = [];


%% Allocate 
% Heat Boundary Condtion
ThermalConditionTable.ConditionName=DefConditionNameList;
% Circuit Component List
ThermalConditionTable.CircuitComponent=CircuitComponentList;

% ThermalConditionTable에서 ConditionValueTable 열이 비어있는 행의 인덱스 찾기
emptyConditionValueTableRows = cellfun('isempty', ThermalConditionTable.ConditionValueTable);

% 해당 행의 ConditionType 데이터 삭제
ThermalConditionTable.('ConditionType')(emptyConditionValueTableRows) = '<undefined>';


%% DuplicateSetObj 맞춰서 SetName 변경
    % 'Coil' 또는 'Magnet'을 포함하지않는 행 찾기
indices = ~contains(ThermalConditionTable.GeomSetName, 'Coil') & ~contains(ThermalConditionTable.GeomSetName, 'Magnet');

% 해당 행의 'GeomSetName'에 '_FullModelSet' 추가
ThermalConditionTable.GeomSetName(indices) = strcat(ThermalConditionTable.GeomSetName(indices), '_FullModelSet');

% 결과 확인
disp(ThermalConditionTable);

% 비어있는 행 삭제
end