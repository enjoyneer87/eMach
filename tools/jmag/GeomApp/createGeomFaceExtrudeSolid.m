function FaceExtrudeObj=createGeomFaceExtrudeSolid(FaceExtrudeCells,PartName,geomApp)

geomDocu=geomApp.GetDocument;
%% Face 할당
% reverseSideFace  = List4FaceExtrude(contains(List4FaceExtrude,')))'));
% PositiveSideFace = List4FaceExtrude(~contains(List4FaceExtrude,reverseSideFace));
reverseSideFace  = FaceExtrudeCells.BackfacesCell;
PositiveSideFace = FaceExtrudeCells.FrontfaceCell;
%% OpenPart
PartItemObj=geomApp.GetDocument().GetAssembly().GetItem(PartName);
PartItemObj.OpenPart()
%% Find ExtrudeLength from ExtrudeSolid Obj
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
%% CreateFaceExtrudeSolid 
% Positive Side
upsideFaceExtrudeObj=PartItemObj.CreateFaceExtrudeSolid();
upsideFaceExtrudeObj.SetProperty("DirectionId", PositiveSideFace{1})
upsideFaceExtrudeObj.SetProperty("Height",ExtrudeLength)
upsideFaceExtrudeObj.SetProperty("name",'upside')

for IndexPositiveSideFace=1:length(PositiveSideFace)
    refObj      =geomDocu.CreateReferenceFromIdentifier(PositiveSideFace{IndexPositiveSideFace});
    upsideFaceExtrudeObj.AddPropertyByReference("FaceList",refObj);
end

% reverse Side
downSideExtrudeObj=PartItemObj.CreateFaceExtrudeSolid();
downSideExtrudeObj.SetProperty("DirectionId",reverseSideFace{1})
downSideExtrudeObj.SetProperty("Height",ExtrudeLength)
downSideExtrudeObj.SetProperty("name",'downSide')
for IndexPositiveSideFace=1:length(reverseSideFace)
    refObj=geomDocu.CreateReferenceFromIdentifier(reverseSideFace{IndexPositiveSideFace});
    downSideExtrudeObj.AddPropertyByReference("FaceList",refObj);
end
%% to Struct
FaceExtrudeObj.upside   =upsideFaceExtrudeObj;
FaceExtrudeObj.downside =downSideExtrudeObj;
end