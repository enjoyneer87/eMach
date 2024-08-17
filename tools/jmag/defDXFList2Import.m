function dxfList2Import=defDXFList2Import(dxfFiles, statorIndex,rotorIndex)
testStatorDXFPath=dxfFiles{statorIndex};
testRotorDXFPath =dxfFiles{rotorIndex};
DXFtool(testStatorDXFPath)
DXFtool(testRotorDXFPath)
dxfList2Import=table();
dxfList2Import.dxfPath(1)={testStatorDXFPath};
dxfList2Import.dxfPath(2)={testRotorDXFPath};
ItemList={'Stator','Rotor'};
dxfList2Import.sketchName(1)=ItemList(1);
dxfList2Import.sketchName(2)=ItemList(2);
end