function addJmagHeatSourceCondition(ModelObj,Steady2,ConditionName,CellPartIds)

ConditionObj=Steady2.CreateCondition("HeatGeneration", ConditionName);
% Steady2.GetCondition(ConditionName).SetValue("GenerationType", 1);
% Steady2.GetCondition(ConditionName).ClearParts();

% ConditionObj.AddPartByGroup(setName)

% CellPartIds=GroupList.GetParts(GroupIndex-1);

% for PartIndex=1:length(CellPartIds)
% ConditionObj.AddPart(CellPartIds{PartIndex})
% end
% ConditionObj.AddGroup(GroupList.GetPartId())

% Steady2.GetCondition(ConditionName).AddSet(ModelObj.GetSetList().GetSet(setName), 0)

end