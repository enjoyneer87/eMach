function PartStructByType=tempGetMagnetizationEdgeFromPartStructByType(PartStructByType,app)
    Model=app.GetCurrentModel;
    MagnetMagnetizeEdge=[];
    for MagnetIndex=1:height(PartStructByType.MagnetTable)
        for EdgeIdIndex=1:height(PartStructByType.MagnetTable.Edge)
            % Edge Id로부터 VertexPoisition 추출
            EdgeIdTable=PartStructByType.MagnetTable.Edge{MagnetIndex};
            EdgeId=EdgeIdTable.EdgeIds(EdgeIdIndex);
            StartPositionObj=Model.GetEdgeStartPosition(EdgeId);
            EndPositionObj=Model.GetEdgeEndPosition(EdgeId);    % %   cf - geomApp  EndVertexobj=CurItem.GetEndVertex;
            StartPosition=getPositionStructFromPostionObj(StartPositionObj);
            EndPosition=getPositionStructFromPostionObj(EndPositionObj);
        
            StartPositionVertexangle = calculateAngleBetweenThreePoints(CenterBarrierpoint1, CenterBarrierpoint2, StartPosition);
            EndPositionVertexangle = calculateAngleBetweenThreePoints(CenterBarrierpoint1, CenterBarrierpoint2, EndPosition);
        
            if StartPositionVertexangle==EndPositionVertexangle
                EdgeIdTable.MagnetMagnetizeEdge(EdgeIdIndex)=1;
                PartStructByType.MagnetTable.Edge{MagnetIndex}=EdgeIdTable;
            % else
            %     EdgeIdTable.MagnetMagnetizeEdge(EdgeIdIndex)=0;
            end
        end
    end
end