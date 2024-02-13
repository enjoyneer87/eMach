function copyGeomPart(ItemName,geomApp,HowMany) 
%% HowMany가 입력 안되면 복사는 한번만
if nargin<3
        HowMany=2;
end
%%  복사
    for i=1:(HowMany-1)
        ref1 = geomApp.GetDocument().GetAssembly().GetItem(ItemName);
        geomApp.GetDocument().GetSelection().Add(ref1)
        geomApp.GetDocument().GetSelection().Copy()
        geomApp.GetDocument().GetSelection().Clear()
        ref1 = geomApp.GetDocument().CreateReferenceFromIdentifier("plane(TBasicPlane2)");
        geomApp.GetDocument().GetSelection().AddReferenceObject(ref1)
        geomApp.GetDocument().GetSelection().Paste()
    end
end