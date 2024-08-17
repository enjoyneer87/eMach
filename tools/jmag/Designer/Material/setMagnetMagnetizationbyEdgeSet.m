function setMagnetMagnetizationbyEdgeSet(app,MagNetMaterial,MagnetTable)
% MagNetMaterial='N42EH'
    Model=app.GetCurrentModel;
    SetListObj=Model.GetSetList();
    NumSet=SetListObj.NumSet;
    CurrentStudy=app.GetCurrentStudy;

%% Set Magnetizae
    setList={};
for SetIndex=1:NumSet
    setObj=SetListObj.GetSet(int32(SetIndex-1));
    setName = setObj.GetName;
    if contains(setName,'magnet','IgnoreCase',true)
        setList{SetIndex}=setObj.GetName;
        selMagnetInner=Model.CreateSelection();
        UniqueMagnetName=strsplit(setList{SetIndex},'.');
        UniqueMagnetName=UniqueMagnetName{1};
        MagnetNameIndex=find(contains(MagnetTable.Name,UniqueMagnetName));
        if isempty(UniqueMagnetName)
        MagnetNameIndex=find(contains(MagnetTable.Name, ['Rotor/',UniqueMagnetName]));
        end

        for MagnetIndex=1:height(MagnetNameIndex) 
            MagnetName=MagnetTable.Name{MagnetNameIndex(MagnetIndex)};    
            CurrentStudy.SetMaterialByName(MagnetName, MagNetMaterial);
            MaterialObj=CurrentStudy.GetMaterial(MagnetName);
            MaterialObj.SetPattern('ParallelCircularAnyDirection')
            MaterialObj.SetValue('Poles','POLES')
            MaterialObj.SetValue('StartAngle','360/POLES/2')
            MaterialObj.SetValue("UseMirrorCopy", 1)
            % MaterialObj.GetReverseEdgeDirection()
            MaterialObj.SetEdgeOrientation(0)  % 0 Perpendicular 1 Parallel
            CurrentStudy.GetMaterial(MagnetName).SetDirectionFromReferenceTarget(setObj);

     
            %% [NF]Direction이 외측인지 내측인지 확인 알고리즘
            DirectionObj=MaterialObj.GetDirection;
            DirX=DirectionObj.GetX;
            DirY=DirectionObj.GetY;
            % DirZ=DirectionObj.GetZ;
            direction = checkVectorDirection(DirX, DirY);  
            if contains(direction,'Inwards')
                MaterialObj.SetReverseEdgeDirection(1);
            end
       end
    end
end
 
end