function [RegionLineTable]=getVertexofLineArcJmagRegionData(RegionData,app)

geomApp=app.CreateGeometryEditor(0);
geomDocu=geomApp.GetDocument;
xstart=0;
ystart=0;
zstart=0;
xMax=400;
yMax=400;
zMax=400;
geomApp.View().SelectByCircleWorldPos(xstart, ystart,zstart, xMax, yMax, zMax, 0);
sel=geomDocu.GetSelection;
sel.Clear;
RegionTable=struct2table(RegionData);
for ItemIndex=1:length(RegionData)
    if strcmp(RegionTable.Type{ItemIndex},'SketchLine')|strcmp(RegionTable.Type{ItemIndex},'SketchArc') 
    sel.AddReferenceObject(RegionTable.ReferenceObj(ItemIndex));
    returnItem=sel.Item(0);
        if returnItem.IsValid
        % 모든 Arc 와 line
        % StartVertex와 EndVertex 따기
        startVertex=returnItem.GetStartVertex;
        startVertexPositionTable=struct2table(cart2polJmagVertexObj(startVertex));
        EndVertex=returnItem.GetEndVertex;
        EndVertexPositionTable=struct2table(cart2polJmagVertexObj(EndVertex));
        sel.Clear
        tempTable=addvars(RegionTable(ItemIndex,:),startVertexPositionTable);
        tempTable=addvars(tempTable,               EndVertexPositionTable);
        if ~exist('RegionLineTable','var')
        RegionLineTable=RegionTable(ItemIndex,:);
        RegionLineTable=addvars(RegionLineTable,startVertexPositionTable);
        RegionLineTable=addvars(RegionLineTable,EndVertexPositionTable);
        else
        RegionLineTable(end+1,:)=tempTable;
        end
    end
end

end