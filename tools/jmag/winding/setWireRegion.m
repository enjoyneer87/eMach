function setWireRegion(studyObj,firstSlotWirePartsTable,ConductorNumber)
if contains(class(studyObj),'designer')
    app=studyObj;
    NumModels=app.NumModels;
    NumStudies=app.NumStudies;
    if NumStudies==1 && NumModels==1
    % Model=app.GetModel(0);
    % Model.GetName;
    studyObj=app.GetModel(0).GetStudy(0);
    % if Study.IsValid==1
    studyObj.GetName;
    else 
    studyObj=app.GetCurrentStudy;
    % disp('study와 모델이 여러개입니다.')
    end
else
    app  = callJmag;
    studyObj=studyObj;
end

if nargin<3
    WireTemplateObj=getWireTemplateObject(app);
    if WireTemplateObj.IsValid
        WireTemplateName=WireTemplateObj.GetName;
        ConductorNumber=WireTemplateObj.GetProperty("WireCount");
    end
end
   
% studyObj.GetWindingRegion(0).IsValid
NumWindingRegions=studyObj.NumWindingRegions();
WindingRegionObj=studyObj.GetWindingRegion(NumWindingRegions-1);
% if WindingRegionObj.IsValid
%         WindingRegionObj.SetPoles("POLES");
%         WindingRegionObj.SetSlots("SLOTS");
% % else
% %         WindingRegionObj    =devmkWindingRegion(app);
% end


WindingRegionObj.SetIsWireTemplateRegion(true)
deleteCoilRegion()
WindingRegionObj=studyObj.GetWindingRegion(NumWindingRegions-1);



    %% GetWindingRegion WindingRegion object는 매번 호출해야됨 아직 matlab으로 객체인식이 잘안됨
    % WindingRegionObj.SetOriginXYZ(0, 0, 0);
    % Study.GetWindingRegion("HairPinWave").SetIsWireTemplateRegion(1);   
    sel1=cell(ConductorNumber,1);
    for RegionIndex=1:double(ConductorNumber)
        CoilRegionName=['Coil Region ',num2str(RegionIndex)];
        sel1{RegionIndex,1} = WindingRegionObj.GetSelection(1-RegionIndex);
        partIndex{RegionIndex}=WindingRegionObj.GetParts(RegionIndex-1);
        if isempty(partIndex{RegionIndex})
        WindingRegionObj.AddCoilRegion(CoilRegionName);
        end
        partIndex{RegionIndex}=firstSlotWirePartsTable.partIndex((RegionIndex));
        sel1{RegionIndex,1}.SelectPart(partIndex{RegionIndex})
        WindingRegionObj.AddSelected(RegionIndex-1, sel1{RegionIndex,1})
        clear sel1;
    end
end