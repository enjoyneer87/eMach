function setJMAGFEMCoil(studyObj,PartStructByType)
% studyObj=SinNonEddyStudyObj
%% pre calculation
Dtable=studyObj.GetDesignTable();
tempJMAGDTableCSVpath='Z:\Simulation\JEETACLossValid_e10_v24\refModel\sampleJMAGDesignTable.csv';
Dtable.Export(tempJMAGDTableCSVpath)
JMAGDesignTable=readtable(tempJMAGDTableCSVpath);
propertiesName=JMAGDesignTable.Properties.VariableNames;
PoleProp=JMAGDesignTable(:,contains(propertiesName,'Poles','IgnoreCase',true));
PoleNumber=unique(PoleProp.Variables);
SlotNumberProp=JMAGDesignTable(:,contains(propertiesName,'Slot','IgnoreCase',true));
SlotNumber=unique(SlotNumberProp.Variables);
q=calcNSPP(SlotNumber,PoleNumber);  % NSPP

%%
PhaseName={'u','v','w'};
% studyObj.GetCondition
% ConditionObj=studyObj.GetCondition('FemCoil');
for PhaseIndex=1:length(PhaseName)
    % studyObj.CreateCondition('FemCoil',PhaseName{PhaseIndex})
    % ConditionObj.SetName(PhaseName{PhaseIndex})
    ConditionObj=studyObj.CreateCondition("FEMCoil", PhaseName{PhaseIndex});
    ConditionObj.SetLink(['Coil',num2str(PhaseIndex)])
    %% SubCondition
    subCon_CoilSet1Obj=ConditionObj.GetSubCondition(0);
    if subCon_CoilSet1Obj.IsValid
        sel = subCon_CoilSet1Obj.GetSelection();
        if ~isempty(PartStructByType.SlotTable)
        SlotIndex=contains(PartStructByType.SlotTable.Name,['Slot',num2str(PhaseIndex*q-1)]);
        SlotPartIndex=PartStructByType.SlotTable.partIndex(SlotIndex);
        % elseif isempty(PartStructByType.ConductorTable)
        % SlotIndex=contains(PartStructByType.ConductorTable.Name,['Slot',num2str(PhaseIndex*q-1)]);
        % SlotPartIndex=PartStructByType.SlotTable.partIndex(SlotIndex);
        end
        for slotIndex=1:length(SlotPartIndex)
            sel.SelectPart(SlotPartIndex(slotIndex));    
            subCon_CoilSet1Obj.AddSelected(sel);
        end
        if PhaseIndex==2
        subCon_CoilSet1Obj.SetValue('Direction2D',1)
        end
        sel.Clear;
    end
    %% Coil Set 2 (2nd Slot)
    subCon_CoilSet2Obj=ConditionObj.CreateSubCondition("FEMCoilData", "Coil Set 2");
    sel=subCon_CoilSet2Obj.GetSelection();
    SlotIndex=contains(PartStructByType.SlotTable.Name,['Slot',num2str(PhaseIndex*q)]);
    SlotPartIndex=PartStructByType.SlotTable.partIndex(SlotIndex);
    for slotIndex=1:length(SlotPartIndex)
    sel.SelectPart(SlotPartIndex(slotIndex));    
    subCon_CoilSet2Obj.AddSelected(sel)
    end
    if PhaseIndex==2
    subCon_CoilSet2Obj.SetValue('Direction2D',1)
    end
    sel.Clear

    %% Link with Circuit
    % ConditionObj.SetLink(['Coil',num2str(PhaseIndex)])
    %% Delete Initial SubCondition
    % ConditionObj.RemoveSubCondition(0);   
end

end