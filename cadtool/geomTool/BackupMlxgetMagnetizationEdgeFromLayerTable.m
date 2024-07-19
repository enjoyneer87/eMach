function NewLayerTable=getMagnetizationEdgeFromLayerTable(LayerTable,app)
% Model=app.GetCurrentModel;
% if any(contains(LayerTable.Properties.VariableNames,'Vertex'))
% 
% for LayerIndex=1:height(LayerTable)
%     clear oneLayer
%     clear MagnetTable
%     oneLayer=LayerTable(LayerIndex,:);
%     MagnetTable=oneLayer.MagnetTable(1,:);
%     for MagnetIndex=1:height(LayerTable.MagnetTable(LayerIndex,:))
%         clear EdgeIdTable
%         EdgeIdTable=MagnetTable.Edge{MagnetIndex};
%         for EdgeIdIndex=1:height(LayerTable.MagnetTable(LayerIndex,:).Edge{:})
%             EdgeId=EdgeIdTable.EdgeIds(EdgeIdIndex);
%             EdgeIdTable.MagnetMagnetizeEdge(EdgeIdIndex)=0;
%             StartPositionObj=Model.GetEdgeStartPosition(EdgeId);
%             EndPositionObj=Model.GetEdgeEndPosition(EdgeId);    % %   cf - geomApp  EndVertexobj=CurItem.GetEndVertex;
% 
%             % StartPosition=getPositionStructFromPostionObj(StartPositionObj);
%             StartPosition=getPositionStructFromDesignerPostionObj(StartPositionObj);
%             EndPosition=getPositionStructFromDesignerPostionObj(EndPositionObj);
%             % CenterBarrier
%             CenterBarrierpoint1=oneLayer.PointOuter;
%             CenterBarrierpoint2=oneLayer.PointInner;
%             StartPositionVertexangle = calculateAngleBetweenThreePoints(CenterBarrierpoint1, CenterBarrierpoint2, StartPosition);
%             EndPositionVertexangle = calculateAngleBetweenThreePoints(CenterBarrierpoint1, CenterBarrierpoint2, EndPosition);    
%             tolerance = 1e-5; % 허용 가능한 오차 범위 설정 (원하는 값으로 조정)
%              isSimilar = abs(StartPositionVertexangle-EndPositionVertexangle) < tolerance;
%            if  isSimilar
%                EdgeIdTable.MagnetMagnetizeEdge(EdgeIdIndex)=1;
%             % else
%             %     EdgeIdTable.MagnetMagnetizeEdge(EdgeIdIndex)=0;
%            end
%         end
%         MagnetTable.Edge{MagnetIndex}=EdgeIdTable;
%         % MagnetTable.Edge{MagnetIndex}=EdgeIdTable;
%         LayerTable.MagnetTable{LayerIndex}=MagnetTable;
%     end
% end
% 
% 
% 
% NewLayerTable=LayerTable;
% else
%     disp("AirBarrier가 없는 SPMSM 타입같네요")
% 
% 
% end

end