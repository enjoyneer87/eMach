function NewArcTable=getArcDataTable(RegionDataTable,geomApp)
%% Init
StartVertexTable    =table();
CenterVertexTable   =table();         
EndVertexTable      =table();       

%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    % geomApp.visible
    end
geomApp.Hide;

%% Get ArcTable
ArcTable            =getArcTable(RegionDataTable);
%% Get Vertex Table and Arc Radius

    for IndexofArc=1:height(ArcTable)
        CurItem=convertRefObj2Item(ArcTable.ReferenceObj(IndexofArc),geomApp);
        if CurItem.IsValid
        %% VertexTable
        StartVertex                                     =CurItem.GetStartVertex   ;   
        CenterVertex                                    =CurItem.GetCenterVertex  ;     
        EndVertex                                       =CurItem.GetEndVertex     ; 
        % temporary Table
        tempStartVertexTable        =getVertexTable(StartVertex,geomApp);
        tempCenterVertexTable       =getVertexTable(CenterVertex,geomApp);
        tempEndVertexTable          =getVertexTable(EndVertex,geomApp);
        % VertexTable Row
        StartVertexTable    =[StartVertexTable;tempStartVertexTable];
        CenterVertexTable   =[CenterVertexTable;tempCenterVertexTable];
        EndVertexTable      =[EndVertexTable;tempEndVertexTable];
        %% ArcTable Data
        ArcTable.Radius(IndexofArc)                     =CurItem.GetRadius;
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
geomApp.Show


end

