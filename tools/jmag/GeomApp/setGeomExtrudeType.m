function setGeomExtrudeType(setType,PartName,geomApp)
%setType
% 0 - one 
% 1 - both direction

geomApp.GetDocument().GetAssembly().GetItem(PartName).OpenPart()
geomApp.GetDocument().GetAssembly().GetItem(PartName).GetItem("Extrude").SetProperty("Type", int32(setType))
geomApp.GetDocument().GetAssembly().GetItem(PartName).ClosePart()

end