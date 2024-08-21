function firstSlotWirePartsTable=getFirstSlotWirePartTableFromPartStruct(PartStruct)
    IsWire=contains({PartStruct.Name},"Wire");
    if any(IsWire)==0   
        IsSlot=contains({PartStruct.Name},"Conductor");
        SlotGroupParts=PartStruct(IsSlot);
    SlotGroupPartsTable=struct2table(SlotGroupParts);
    SlotGroupPartsTable=sortrows(SlotGroupPartsTable,"CentroidTheta","ascend");
    tolerance=1e-5;
    WireGroupTable=SlotGroupPartsTable;
    else
    WireGroupParts=PartStruct(IsWire);
    WireGroupTable=struct2table(WireGroupParts);
    WireGroupTable=sortrows(WireGroupTable,"CentroidTheta","ascend");
    tolerance=1e-5;
    end
    %% 첫번째 슬롯 Wire확인
    IsFirstSlot=(abs([WireGroupTable.CentroidTheta]-WireGroupTable.CentroidTheta(1))<tolerance);
    firstSlotWirePartsTable=WireGroupTable(IsFirstSlot,:);
    %% CentroidR으로 번호 할당
    firstSlotWirePartsTable=sortrows(firstSlotWirePartsTable,"CentroidR","ascend");
end