function ConductorPartTable=sortingConductorTableBySlot(PartStruct)
    PartTable=struct2table(PartStruct);
    ConductorPartTable=PartTable(contains(PartTable.Name,'Conductor'),:);
    ConductorPartTable=sortrows(ConductorPartTable,'CentroidTheta');
    SlotTheta=uniquetol(ConductorPartTable.CentroidTheta,1e-5);
    
    for i=1:length(SlotTheta)
        SlotIndex=abs(ConductorPartTable.CentroidTheta-SlotTheta(i))<1e-5;
        if ~contains(ConductorPartTable(SlotIndex,:).Name,'Slot','IgnoreCase',true)
        ConductorPartTable(SlotIndex,:).Name=strrep(ConductorPartTable(SlotIndex,:).Name,'/',['/Slot',num2str(i),'/']);
        end
    end
    ConductorPartTable = sortrows(ConductorPartTable,"Name","ascend");
end