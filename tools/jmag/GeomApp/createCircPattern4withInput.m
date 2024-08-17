function createCircPattern4withInput(AssemRegionTable,AreaName,geomApp,checkWithIDname)
%% devTemp
% AssemRegionTable=StatorAssemRegionTable;
% AreaName='';
%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    geomApp.visible
    end
   
    geomDocu=geomApp.GetDocument;
    geomDesignTable=geomDocu.GetDesignTable;

    Poles=geomDesignTable.GetEquation('POLES').GetValue;
    Slot=geomDesignTable.GetEquation('SLOTS').GetValue;
    [~,~,StatorOneSlotAngle]=calcMotorPeriodicity(Poles,Slot);
    q=calcWindingQs(Slot,Poles);
    NSPP=q;
    PhaseNumber=3;

    %% Check with IdenfierName
    otherAreaIndex=contains(AssemRegionTable.IdentifierName,AreaName);
    %% Check With Name
    if nargin<5
    otherAreaIndex=contains(AssemRegionTable.Name,AreaName);
    end
    otherAreaAssemTable=AssemRegionTable(otherAreaIndex,:);
    %% 중복체크
    tempRegionTable=otherAreaAssemTable;
    categoryStructTable=sortAssemItemTableByType(geomApp,'Stator');
    
    if isfield(categoryStructTable,'RegionCircularPattern')
        RegionCircularPatternTable=categoryStructTable.RegionCircularPattern;    
        if ~isempty(RegionCircularPatternTable)
           for ItemIndex=1:height(RegionCircularPatternTable)
                    existpatternName= RegionCircularPatternTable.AssemItemName{ItemIndex};
                    existpatternName=strsplit(existpatternName,'.');
                    existpatternName=existpatternName{1};
                    tempRegionTable=tempRegionTable(~contains(tempRegionTable.sketchItemName, existpatternName),:);            
            end
            otherAreaAssemTable=tempRegionTable;
        elseif height(RegionCircularPatternTable)==0  % 
            otherAreaAssemTable=tempRegionTable;
        end
    end
    %% createPattern
    for IdIndex=1:height(otherAreaAssemTable)
        SketchItem=geomApp.GetDocument().GetAssembly().GetItem("Stator");
        SketchItem.OpenSketch()
        circItemObj=SketchItem.CreateRegionCircularPattern();
        % Item.SetRegionList(otherAreaAssemTable.IdentifierName{IdIndex})
        % Item.SetRegionList((otherAreaAssemTable.Id(:)))
        circItemObj.SetProperty('Region',otherAreaAssemTable.IdentifierName{IdIndex})
        circItemObj.SetProperty('CenterType','DefaultOrigin')
        circItemObj.SetAngle(360/Poles/(NSPP*PhaseNumber))
    
        if NSPP<1
        circItemObj.SetInstance(int32(360/StatorOneSlotAngle))
        else
        circItemObj.SetInstance(int32(NSPP*PhaseNumber));
        end
        AreaName=otherAreaAssemTable.sketchItemName{IdIndex};
        circItemObj.SetName(AreaName);
        circItemObj.SetProperty("Merge", 1)

    end
    
        SketchItem=geomApp.GetDocument().GetAssembly().GetItem("Stator");
        SketchItem.CloseSketch();
end