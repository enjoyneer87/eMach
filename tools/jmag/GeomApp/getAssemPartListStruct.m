function AssemPartStruct=getAssemPartListStruct(geomApp)
    AssemTable=getGeomAssemItemListTable(geomApp);
    geomApp.Hide
    AssemPartStruct=struct();

    %% AssemPart
    for AssemItemIndex=1:height(AssemTable)
        if ~contains(AssemTable.AssemItemName{AssemItemIndex},'Plane')
        AssemPartStruct(AssemItemIndex).AssemPartTable=getSGeomPartData(geomApp,AssemTable.AssemItemName{AssemItemIndex})
        AssemPartStruct(AssemItemIndex).AssemPartName =AssemTable.AssemItemName{AssemItemIndex};
        end
    end


    %% 비어있는 구조체 행 삭제 ('Plane'행)
    AssemPartStruct = rmEmptyRowbyField(AssemPartStruct,'AssemPartTable');
end