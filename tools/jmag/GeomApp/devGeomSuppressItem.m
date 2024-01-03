function devGeomSuppressItem(AssemPartStruct,ItemName,geomApp)
    
    for AssemItemIndex=1:length(AssemPartStruct)
    
    geomApp.GetDocument().GetAssembly().GetItem(AssemPartStruct(AssemItemIndex).AssemPartName).OpenPart()
    geomApp.GetDocument().GetAssembly().GetItem(AssemPartStruct(AssemItemIndex).AssemPartName).GetItem("Turn into Full Model from 1 Period Model along Circumferential Direction").SetProperty("Suppress", 1)
    
    end

end