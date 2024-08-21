function MoveProperty=getWireTemplateMoveProperty(StatorGeomLineTable,OutMostConductorEdgeDesignerTable,app)
%% DesignerTable로부터 GeomTable Line 찾기
% OutMostConductorEdgeDesignerTable
% StatorGeomLineTable
    [~,MatchedStartVertexofLineIndex,~]=intersect([StatorGeomLineTable.StartVertexTablex, StatorGeomLineTable.StartVertexTabley],OutMostConductorEdgeDesignerTable.startPosition(1:2));
    [~,MatchedEndVertexofLineIndex,~]=intersect([StatorGeomLineTable.EndVertexTablex, StatorGeomLineTable.EndVertexTabley],OutMostConductorEdgeDesignerTable.endPosition(1:2));
    [Matchrows4StartVEdge,~]=ind2sub([height(StatorGeomLineTable),2],MatchedStartVertexofLineIndex);
    [Matchrow4EndVEdge,~]=ind2sub([height(StatorGeomLineTable),2],MatchedEndVertexofLineIndex);
    Matchrows4StartVEdge=unique(Matchrows4StartVEdge);
    Matchrow4EndVEdge=unique(Matchrow4EndVEdge);
    if Matchrows4StartVEdge==Matchrow4EndVEdge
    referenceEdge=StatorGeomLineTable.Name{Matchrows4StartVEdge};
    MoveProperty.Reference     =      referenceEdge;   % Conductor Edge
    end
    % OutMostConductorIndex=OutMostConductorEdgeDesignerTable.ConductorID
    ReferenceDirectionVector=[StatorGeomLineTable.vecX(Matchrows4StartVEdge),StatorGeomLineTable.vexY(Matchrows4StartVEdge)];

    perpendicularVector = getPerpendicularVector(ReferenceDirectionVector);
    DirectionVecX =perpendicularVector(1);
    DirectionVecY =perpendicularVector(2);

%% 4 MoveString 으로 만들기 Measurement ??
    HairPinRefObj=getWireTemplateRefObject(app);
    WireTemplateName=HairPinRefObj.GetIdentifier;
    MeasurementEdgeName=['edgeregion(',WireTemplateName,'+edgeregion(',WireTemplateName,')_2)'];
    MoveProperty.Measurement   =   MeasurementEdgeName;
    % SetPropertyStruct.DirectionVecX = -0.997858923238604 ;
    % SetPropertyStruct.DirectionVecY = -0.0654031292301435;
    MoveProperty.DirectionVecX=DirectionVecX;
    MoveProperty.DirectionVecY=DirectionVecY;