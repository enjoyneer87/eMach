function WindingRegionObj=devmkWindingRegion(app,ConductorNumber)
    Model=app.GetCurrentModel;
    Study=app.GetCurrentStudy;
   % Study.CreateWindingRegion("HairPinWave",1)  % Coil Template
    WindingRegionObj=Study.CreateWindingRegion("HairPinWave",0);  % Wire (Geometry) Template
    % Study.CreateWinding("HairPinWave")
    % equationStruct=getJmagDesignerEquationStruct(app);
    
    %% GetWindingRegion WindingRegion object는 매번 호출해야됨 아직 matlab으로 객체인식이 잘안됨
    % Study.GetWindingRegion("HairPinWave");
    Study.GetWindingRegion("HairPinWave").SetOriginXYZ(0, 0, 0);
    Study.GetWindingRegion("HairPinWave").SetIsWireTemplateRegion(1);   
    
    % Study.GetWindingRegion("HairPinWave").CoilGroupSize
    % Study.GetWindingRegion("HairPinWave").GetAllSlotSelection
    
    % if nargin<2
    %     WireTemplateObj=getWireTemplateObject(app);
    %     if WireTemplateObj.IsValid
    %         WireTemplateName=WireTemplateObj.GetName;
    %         ConductorNumber=WireTemplateObj.GetProperty("WireCount");
    %     end
    % end
    % for RegionIndex=1:ConductorNumber
    %     CoilRegionName=['Coil Region ',num2str(RegionIndex)];
    %   Study.GetWindingRegion("HairPinWave").AddCoilRegion(CoilRegionName);
    % end

    % a.IsValid
    % % WindingRegionObj.HasCoilEnd
    % WireTemplateName

end
