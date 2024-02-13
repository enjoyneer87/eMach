function devCreateGeomFaceExtrudeSolid(List4FaceExtrude,PartName,geomApp)

reverseSideFace  = List4FaceExtrude(contains(List4FaceExtrude,')))'));
PositiveSideFace = List4FaceExtrude(~contains(List4FaceExtrude,reverseSideFace))
%%
PartItemObj=geomApp.GetDocument().GetAssembly().GetItem(PartName)
PartItemObj.OpenPart()
    if PartItemObj.IsValid
        NumItems=PartItemObj.NumItems;
        for ItemIndex=1:NumItems
            ItemObj=PartItemObj.GetItem(int32(ItemIndex-1));
            if ItemObj.IsValid
                if contains(ItemObj.GetName,'Extrude') && ~contains(ItemObj.GetName,'Face')
                    ExtrudeLength=ItemObj.GetHeight;
                    WhatName=ItemObj.GetName;
                end
            end
        end
    end
%%  
% Positive Side
for IndexPositiveSideFace=1:length(PositiveSideFace)
tempFaceExtrudeObj=PartItemObj.CreateFaceExtrudeSolid();
% tempFaceExtrudeObj.SetProperty("SpecifiedRatio", ExtrudeLength)
% refarray[0] = "face(TExtrudeSolid130+face(TRegionItem79))"
tempFaceExtrudeObj.SetProperty("DirectionId", PositiveSideFace{IndexPositiveSideFace})
tempFaceExtrudeObj.SetProperty("FaceList", PositiveSideFace{IndexPositiveSideFace})
tempFaceExtrudeObj.SetProperty("Height",ExtrudeLength)
end


% refarray = "face(TExtrudeSolid130+face(TExtrudeSolid130+face(TRegionItem79)))"

for IndexPositiveSideFace=1:length(reverseSideFace)

% reverse Side
tempFaceExtrudeObj=PartItemObj.CreateFaceExtrudeSolid();
% tempFaceExtrudeObj.SetProperty("SpecifiedRatio",ExtrudeLength)
tempFaceExtrudeObj.SetProperty("DirectionId",reverseSideFace{IndexPositiveSideFace})
tempFaceExtrudeObj.SetProperty("FaceList", reverseSideFace{IndexPositiveSideFace})
tempFaceExtrudeObj.SetProperty("Height",ExtrudeLength)
end

end