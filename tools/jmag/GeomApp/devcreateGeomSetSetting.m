function PartGeomTable=devcreateGeomSetSetting(PartGeomTable)


%% LumpTable (RefObj)
LumpTable=table();
for PartIndex=1:height(PartGeomTable)
    PartName=PartGeomTable.AssemItemName{PartIndex};
    PartItemObj=geomApp.GetDocument().GetAssembly().GetItem(PartName);
    PartItemObj.OpenPart();
    clear AssemTable
    AssemTable=getRegObjListTableFromCurrentSelection(geomApp);
    BoolNonLump=~contains(AssemTable.IdentifierName,'lump');
    LumpTable.PartName(PartIndex)={PartName};
    LumpTable.AssemTable(PartIndex)={AssemTable(~BoolNonLump,:)};
    PartItemObj.ClosePart();
end

%% add GeomSetListTable - mkGeomSetListTable
for PartIndex=1:height(PartGeomTable)
        PartName                                    =PartGeomTable.AssemItemName{PartIndex};
        GeomSetListTable                            =mkGeomSetListTable(PartName,'Inner');
        PartGeomTable.GeomSetListTable{PartIndex}   =GeomSetListTable;     
end

%% mkGeomSetListTable
    %% GeomSetSetting    -> GeomSetListTable
    %% SetGeomSet(<mkGeomGeomSet)
    %% GeomSetListTable  -> PartGeomTable 
    
%% add RefObj
% for PartIndex=1:height(PartGeomTable)
%     PartName=PartGeomTable.AssemItemName{PartIndex};
%     PartItemObj=geomApp.GetDocument().GetAssembly().GetItem(PartName);
%     PartItemObj.OpenPart();
%     clear AssemTable
%     AssemTable                       =getRegObjListTableFromCurrentSelection(geomApp);
%     BoolNonLump                      =~contains(AssemTable.IdentifierName,'lump');
%     PartGeomTable.PartName(PartIndex)={PartName};
%     PartGeomTable.AssemRefObTable(PartIndex)={AssemTable(~BoolNonLump,:)};
%     PartItemObj.ClosePart();
% end

end