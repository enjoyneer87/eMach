function setJMAGFEMConductor4Mag(PartStruct,magComponentList,StudyObj)
%% Use With magComponentList=duplicateACMagCircuitFromTemplate(PWMStudyObj,4);
% ex)magComponentList=duplicateACMagCircuitFromTemplate(PWMStudyObj,4);

%% cellFunction 2 make Unique Conductor Name From TableCreate
PartTable=struct2table(PartStruct);
MagnetTable=PartTable(contains(PartTable.Name,'Magnet'),:);


%% Make New Magnet Name
for ConditionIndex=1:height(MagnetTable)
ConditionName=magComponentList{ConditionIndex}   ;
if ~StudyObj.GetCondition(ConditionName).IsValid
StudyObj.CreateCondition("FEMConductor", ConditionName)
StudyObj.GetCondition(ConditionName).SetLink(ConditionName)
StudyObj.GetCondition(ConditionName).GetSubCondition("untitled").SetName("Conductor Set 1")
end
StudyObj.GetCondition(ConditionName).GetSubCondition("Conductor Set 1").ClearParts()
sel = StudyObj.GetCondition(ConditionName).GetSubCondition("Conductor Set 1").GetSelection();
MagPartIndex=MagnetTable.partIndex(ConditionIndex);
sel.SelectPart(MagPartIndex)
StudyObj.GetCondition(ConditionName).GetSubCondition("Conductor Set 1").AddSelected(sel)
sel.Clear
end

end
