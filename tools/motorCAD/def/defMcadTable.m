function McadTable=defMcadTable(category2Out)
    MCADStruct=defMcadTableStruct();
   
    if isfield(MCADStruct,category2Out)
    McadTable=MCADStruct.(category2Out);
    else
        fieldList=fieldnames(MCADStruct);
        matchingIndex=contains(fieldList,category2Out,"IgnoreCase",true);
        matchingIndices=find(matchingIndex);
        %% 2 Table
        if numel(matchingIndices)>1
            disp(['유사한 이름이 여러개입니다  ' ,fieldList((matchingIndex))])

            for TableIndex=1:numel(matchingIndices)
            tempMcadTable=MCADStruct.(fieldList{matchingIndex});
            McadTable=[McadTable;tempMcadTable];
            end
        else
        disp(['유사한 이름이 있습니다  ' ,fieldList((matchingIndex))])
        McadTable=MCADStruct.(fieldList{matchingIndex});
        end
    end
end