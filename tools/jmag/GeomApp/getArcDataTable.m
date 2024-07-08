function NewArcTable=getArcDataTable(RegionDataTable,geomApp)
%% Init
% RegionDataTable=AssembleTable; %dev
StartVertexTable    =table();
CenterVertexTable   =table();         
EndVertexTable      =table();       

%% check App or Geometry Editor
if nargin>1
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    % geomApp.visible
    end
geomApp.Hide;
end
%% Get ArcTable
if isvarofTable(RegionDataTable,'Type')
ArcTable            =getArcTable(RegionDataTable);
elseif isvarofTable(RegionDataTable,'IdentifierName')
ArcTable=RegionDataTable(contains(RegionDataTable.IdentifierName,'Arc'),:);
ArcTable=ArcTable(~contains(ArcTable.IdentifierName,'vertex'),:);
ArcTable=ArcTable(~contains(ArcTable.IdentifierName,'Item'),:);
ArcTable=ArcTable(~contains(ArcTable.IdentifierName,'Boolean'),:);
end
%% Get Vertex Table and Arc Radius

    for IndexofArc=1:height(ArcTable)
        if isvarofTable(RegionDataTable,'IdentifierName')
        CurItem=convertRefObj2Item(ArcTable.ReferenceObj(IndexofArc),geomApp);
        else
        CurItem=ArcTable.sketchItemObj{IndexofArc};
        end
        if CurItem.IsValid
        %% VertexTable
        StartVertex                                     =CurItem.GetStartVertex   ;   
        CenterVertex                                    =CurItem.GetCenterVertex  ;     
        EndVertex                                       =CurItem.GetEndVertex     ; 
        % temporary Table
        if nargin>1
        tempStartVertexTable        =getVertexTable(StartVertex,geomApp);
        tempCenterVertexTable       =getVertexTable(CenterVertex,geomApp);
        tempEndVertexTable          =getVertexTable(EndVertex,geomApp);
        else
        tempStartVertexTable        =getVertexTable(StartVertex);
        tempCenterVertexTable       =getVertexTable(CenterVertex);
        tempEndVertexTable          =getVertexTable(EndVertex);
        end
        % VertexTable Row
        StartVertexTable    =[StartVertexTable;tempStartVertexTable];
        CenterVertexTable   =[CenterVertexTable;tempCenterVertexTable];
        EndVertexTable      =[EndVertexTable;tempEndVertexTable];
        %% ArcTable Data
        ArcTable.lengthinRadius(IndexofArc)                     =CurItem.GetRadius; % Radius from each CenterVertex
        % ArcTable.Angle(IndexofArc)     

        ArcTable.Angle(IndexofArc)=calculateAngleBetweenThreePoints(tempStartVertexTable,tempCenterVertexTable,tempEndVertexTable);
        % geomDocuMeasureManager=geomDocu.GetMeasureManager();
        % refObj1=geomDocu.CreateReferenceFromIdentifier()
        % refObj2=geomDocu.CreateReferenceFromIdentifier()
        % ArcTable.Angle(IndexofArc)=geomDocuMeasureManager.MeasurePointAngle(0,0,0,refObj1,refObj2);
        end
    end
%% Assemble ArcTable with VertexTable
addTableName2VarNameInFunction('StartVertexTable');
addTableName2VarNameInFunction('CenterVertexTable');
addTableName2VarNameInFunction('EndVertexTable');
NewArcTable=[ArcTable StartVertexTable CenterVertexTable EndVertexTable ];
% geomApp.Show


end

