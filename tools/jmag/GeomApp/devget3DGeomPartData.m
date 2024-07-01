function AssemObjTable=devget3DGeomPartData(geomApp,AssembleName)
    %% dev
    % AssembleName=AssemTable.AssemItemName{AssemItemIndex}
    
    %%
    geomApp.GetDocument().GetAssembly().GetItem(AssembleName).OpenPart()
    AssemObjStruct=getSkecthDataTableFromCurrentSelection(geomApp);   
    geomApp.GetDocument().GetAssembly().GetItem(AssembleName).ClosePart()
    AssemObjTable                =struct2table(AssemObjStruct);

end