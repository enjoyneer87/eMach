function WireInfo=getWireInfo4GeomWireTemplate(SlotUniqueValueStruct,StatorGeomLineTable,PartStruct,CenterVertexDesignerTable,StatorOneSlotAngle)

    ConductorNumber=height(SlotUniqueValueStruct.Indices);
    WireInfo.ConductorNumber          =ConductorNumber;
  

 %% Core나 Insulation 의 중앙 Vertex
    % CenterVertexDesignerTable
    [~,MatchStartIndexinGeomTable,~]=intersect([StatorGeomLineTable.StartVertexTablex, StatorGeomLineTable.StartVertexTabley],CenterVertexDesignerTable.Position(1:2))
    [~,MatchEndIndexinGeomTable,~]  =intersect([StatorGeomLineTable.EndVertexTablex, StatorGeomLineTable.EndVertexTabley],CenterVertexDesignerTable.Position(1:2))

    [Matchrows4Start,~]=ind2sub([height(StatorGeomLineTable),2],MatchStartIndexinGeomTable);
    [Matchrow4End,~]=ind2sub([height(StatorGeomLineTable),2],MatchEndIndexinGeomTable)

    Matchrows4Start=unique(Matchrows4Start);
    Matchrow4End=unique(Matchrow4End);

    StartVertexFromStartVertex  =StatorGeomLineTable.StartVertexTableName{Matchrows4Start};
    StartVertexFromEndVertex    =StatorGeomLineTable.EndVertexTableName{Matchrow4End};

    StatorVertex=StartVertexFromStartVertex;
    WireInfo.StartVertex              =StatorVertex;

%% Conductor Edge 중  Radius 가 가장 큰거   
    % DesignTable 에서 가져오기 
    OutMostConductorEdgeDesignerTable =  findOutMostConductorEdgeTable(PartStruct)
    WireInfo.RectangleHeight          =  OutMostConductorEdgeDesignerTable.conductorDimension(2)   
    WireInfo.RectangleWidth           =  OutMostConductorEdgeDesignerTable.conductorDimension(1)     
    WireInfo.DirectionAngle           =  StatorOneSlotAngle/2;

    %%[TC]
    WireInfo.WireCoatingThickness     =  0.1           
    WireInfo.InsulationThickness      =  0.25       
    WireInfo.WieGapDistance           =  0.1     
    WireInfo.FillFactor               =80;


end