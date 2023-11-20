function newStruct=getRegionDataArea(refObjDataStruct,app,AssembleName)
if nargin<3
AssembleName='Stator';
end
geomApp=app.CreateGeometryEditor(0);
geomApp.GetDocument().GetAssembly().GetItem(AssembleName).OpenSketch();
geomDocu=geomApp.GetDocument();
sel=mkSelectionObj(app,1);
newStruct=struct();
%% Selection Object
sel=geomDocu.GetSelection;
NumSelections=sel.Count;
%% 면적 구하기 
    for SelIndex=1:NumSelections
        % geomApp.View().SelectByCircleWorldPos(xstart, ystart,zstart, xMax, yMax, zMax, 0);
        % sel=geomDocu.GetSelection;
        sel.Clear;
        sel.AddReferenceObject(refObjDataStruct(SelIndex).ReferenceObj);
        geomDocuVolManager=geomDocu.GetVolumeCalculationManager();
        newStruct(SelIndex).Area=geomDocuVolManager.CalculateArea;
        % RegionArray(SelIndex,1)=refObjTable(SelIndex).Area;
    end
sel.Clear
geomApp.GetDocument().GetAssembly().GetItem(AssembleName).CloseSketch();
end
