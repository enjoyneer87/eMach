function setJMAGFEMConductor(ConductorPartTable,StudyObj)
%% dev
% StudyObj=app.GetCurrentStudy;


%% cellFunction 2 make Unique Conductor Name From Table
splitNames = cellfun(@(x) strsplit(x, '/'), ConductorPartTable{:,"Name"}, 'UniformOutput', false);
collectedStrings = cellfun(@(x) x{3}, splitNames, 'UniformOutput', false);
UniqueConductorPerSlot=unique(collectedStrings);
%% Conductor Set List
ConductorSetNameCellList = cellfun(@(x) strrep(x, '_', ' set '), UniqueConductorPerSlot, 'UniformOutput', false);
NConductorPerSlot=length(ConductorSetNameCellList);
%% Phase List
CircuitPhaseList={'U1','W1','V1'};
NumConditions=StudyObj.NumConditions;

%% 중복 체크
ExistPhaseList = {};
for ConditionIndex = 1:NumConditions
    conditionObj = StudyObj.GetCondition(ConditionIndex-1); 
    if strcmp(conditionObj.GetType, 'FEM Conductor')
        ExistPhaseList{end+1} = conditionObj.GetName;
    end
end
ExistPhaseList=ExistPhaseList(~contains(ExistPhaseList,'mag'));

if isempty(ExistPhaseList)

elseif  ~isempty(ExistPhaseList)
CircuitPhaseList=setxor(CircuitPhaseList,ExistPhaseList);
end

%% Make New Conductor Name Phase - add Slot Matching
for ConditionIndex=1:length(CircuitPhaseList)
    StudyObj.CreateCondition("FEMConductor", CircuitPhaseList{ConditionIndex})
    StudyObj.GetCondition(CircuitPhaseList{ConditionIndex}).SetLink(CircuitPhaseList{ConditionIndex})
    for ConductorIndex=1:NConductorPerSlot
    %% 1st Slot
    curCondition=CircuitPhaseList{ConditionIndex} ; 
    curConditionObj=StudyObj.GetCondition(curCondition);
    subConObj=curConditionObj.CreateSubCondition("FEMConductorData", [ConductorSetNameCellList{ConductorIndex},'_1stSlot']);
    sel = subConObj.GetSelection();
    Slot1stIndex=(ConditionIndex-1)*(NConductorPerSlot)*(2)+ConductorIndex;
    sel.SelectPart(ConductorPartTable.partIndex(Slot1stIndex));
    subConObj.AddSelected(sel)
    if ConditionIndex==2
    subConObj.SetValue("Direction2D", 1)
    end
    sel.Clear
    %% 2nd Slot
    subConObj2=curConditionObj.CreateSubCondition("FEMConductorData", [ConductorSetNameCellList{ConductorIndex},'_2stSlot']);
    sel2 = subConObj2.GetSelection();
    Slot2ndIndex=(ConditionIndex-1)*(NConductorPerSlot)+ConductorIndex+(ConditionIndex)*(NConductorPerSlot);
    sel2.SelectPart(ConductorPartTable.partIndex(Slot2ndIndex))
    subConObj2.AddSelected(sel2)
    if ConditionIndex==2
    subConObj2.SetValue("Direction2D", 1)
    end
    sel2.Clear
    end
    %% Link with Circuit
    StudyObj.GetCondition(CircuitPhaseList{ConditionIndex}).SetLink(CircuitPhaseList{ConditionIndex})
    %% Delete Initial SubCondition
    curConditionObj.RemoveSubCondition(0);    
end

end
