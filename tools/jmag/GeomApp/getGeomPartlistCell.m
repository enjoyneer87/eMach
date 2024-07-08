function AssembleItemName=getGeomPartlistCell(geomApp)
%% init
     geomDocu        =geomApp.GetDocument;
    geomAssemble    =geomDocu.GetAssembly;
    NumAssemblyItem =geomAssemble.NumItems;

%% get Current Part List    
% 1~3 Index는 Plane reference라서 제외
    for ItemIndex=4:NumAssemblyItem    
        selAssemblItem=geomAssemble.GetItem(int32(ItemIndex-1));
        if selAssemblItem.IsValid
            AssembleItemName{ItemIndex-3}=selAssemblItem.GetName;
        end
    end
end