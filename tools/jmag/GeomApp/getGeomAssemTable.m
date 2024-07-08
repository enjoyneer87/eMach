function faceRegionTable=getGeomAssemTable(geomApp,AssembleName)
% 
% 
% if nargin>2
% 
% else
% AssemItemObj=AssembleName;
% 
% isGA=isGeomApp(geomApp);
% if isGA
%     AssembleName=PartObj;
%     AssemTable = getGeomAssemItemListTable(geomApp);
%     AssemItemObj=AssemTable.AssemItem(contains(AssemTable.AssemItemName,AssembleName));
% elseif isGA==0
%     isPart=isPartObj(geomApp);
%     if ~isPart
%         isSketch=isSketchObj(geomApp); 
%         if isSketch
%             disp('SketchObj는 안되요')
%         end
%     end
% 
% end

% 3d & 2d Available
AssemTable = getGeomAssemItemListTable(geomApp);
PartGeomTable=AssemTable(contains(AssemTable.Type,'Part'),:);
%% 3D인경우
if ~isempty(PartGeomTable)
    PartObj=PartGeomTable.AssemItem(contains(PartGeomTable.AssemItemName,AssembleName));
    %% PartItem Table
    if iscell(PartObj)
    PartObj=PartObj{:};
    end
    %% get Only Sketch Item
    PartItemTable = getGeomObjItemListTable(PartObj);
    IsSketch=contains(PartItemTable.Type,'Sketch','IgnoreCase',true);
    SketchIndex=find(IsSketch);
    if isscalar(SketchIndex)
        sketchObj=PartItemTable.AssemItem{SketchIndex};
        %% Sketch Item Table
        % SketchGeomItemTable = getGeomObjItemListTable(SketchObj);
        faceRegionTable=getGeomSketchTableWithHierData(geomApp,sketchObj);
    else
    disp('Part 내에 sketch가 여러개입니다')
    end
elseif isempty(PartGeomTable)
%% 2D인 경우
faceRegionTable=getGeomAssembleTableWithHierData(geomApp,AssembleName);
end
end

