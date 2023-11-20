function NewArcTable=getArcDataTable(RegionDataTable,app)
%% Init
StartVertexTable    =table();
CenterVertexTable   =table();         
EndVertexTable      =table();         
% Get ArcTable
ArcTable=getArcTable(RegionDataTable);
%% Get Vertex Table and Arc Radius
    for IndexofArc=1:height(ArcTable)
        CurItem=convertRefObj2Item(ArcTable.ReferenceObj(IndexofArc),app);
        if CurItem.IsValid
        %% VertexTable
        StartVertex                                     =CurItem.GetStartVertex   ;   
        CenterVertex                                    =CurItem.GetCenterVertex  ;     
        EndVertex                                       =CurItem.GetEndVertex     ; 
        % temporary Table
        tempStartVertexTable        =getVertexTable(StartVertex,app);
        tempCenterVertexTable       =getVertexTable(CenterVertex,app);
        tempEndVertexTable          =getVertexTable(EndVertex,app);
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
end

