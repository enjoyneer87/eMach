function NewLineTable=getLineDataTable(RegionDataTable,geomApp)
%% Init
StartVertexTable    =table();
% CenterVertexTable   =table();         
EndVertexTable      =table();     
LineDirectionalTable=table();
%% check App or Geometry Editor
    AppDir=geomApp.GetAppDir;
    AppDirStr=split(AppDir,'/');
    if ~strcmp(AppDirStr{end},'Modeller')
    geomApp=geomApp.CreateGeometryEditor(0);
    geomApp.visible
    end
geomApp.Hide;

% Get ArcTable
sketchLineTable=getLineTable(RegionDataTable);

%% Get Vertex Table and Arc Radius
    for IndexofArc=1:height(sketchLineTable)
        CurItem=convertRefObj2Item(sketchLineTable.ReferenceObj(IndexofArc),geomApp);
        if CurItem.IsValid
        %% VertexTable
        StartVertex                                     =CurItem.GetStartVertex   ;   
        % CenterVertex                                    =CurItem.GetCenterVertex  ;     
        EndVertex                                       =CurItem.GetEndVertex     ; 
        % temporary Table
        tempStartVertexTable        =getVertexTable(StartVertex,geomApp);
        % tempCenterVertexTable       =getVertexTable(CenterVertex,app);
        tempEndVertexTable          =getVertexTable(EndVertex,geomApp);
                % VertexTable Row
        StartVertexTable    =[StartVertexTable;  tempStartVertexTable];
        % CenterVertexTable =[CenterVertexTable; tempCenterVertexTable];
        EndVertexTable      =[EndVertexTable;    tempEndVertexTable];

        tempLineDirectionalTable                            =array2table(getDirectionalVector(tempStartVertexTable, tempEndVertexTable));
        tempLineDirectionalTable.Properties.VariableNames   ={'vecX','vexY','VecZ'};
        LineDirectionalTable                                =[LineDirectionalTable;tempLineDirectionalTable];
        %% Line Data
        % sketchLineTable.Radius(IndexofArc)                     =CurItem.GetRadius;
        % ArcTable.Angle(IndexofArc)     
        % sketchLineTable.Angle(IndexofArc)=calculateAngleBetweenThreePoints(tempStartVertexTable,tempEndVertexTable);
        sketchLineTable.length(IndexofArc)                      =calcLengthBetweenTwoPoints(tempStartVertexTable,tempEndVertexTable);
        % geomDocuMeasureManager=geomDocu.GetMeasureManager();
        % refObj1=geomDocu.CreateReferenceFromIdentifier()
        % refObj2=geomDocu.CreateReferenceFromIdentifier()
        % ArcTable.Angle(IndexofArc)=geomDocuMeasureManager.MeasurePointAngle(0,0,0,refObj1,refObj2);
        end
    end
%% Assemble ArcTable with VertexTable
addTableName2VarNameInFunction('StartVertexTable');
% addTableName2VarNameInFunction('CenterVertexTable');
addTableName2VarNameInFunction('EndVertexTable');
NewLineTable=[sketchLineTable LineDirectionalTable StartVertexTable EndVertexTable ];
geomApp.Show

end

