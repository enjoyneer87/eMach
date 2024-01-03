function subIdentifierName=mkSubIdName4RegionExtrude(SolidName,RegionItemName)
 % case Origin Solid
% SolidIdentifierName = "lump(TExtrudeSolid306+face(TExtrudeSolid306+face(TRegionItem305)))"

%ex) SolidIdentifierName= "lump(TFaceExtrudeSolid308+lump(TExtrudeSolid306+face(TExtrudeSolid306+face(TRegionItem305))))"
subIdentifierName = ['face(',SolidName,'+face(',RegionItemName,'))'];



end