function LayerTable=getCenterPointofAirBarrierVertex(LayerTable)

if any(contains(LayerTable.Properties.VariableNames,'Vertex'))
    for LayerIndex=1:height(LayerTable.Vertex)
        logicalIndices =LayerTable.Vertex{LayerIndex}.IsCenterVertex==1;
        filteredT = LayerTable.Vertex{LayerIndex}(logicalIndices, :);
        point1=[filteredT.x(1),filteredT.y(1),filteredT.z(1)];
        point2=[filteredT.x(2),filteredT.y(2),filteredT.z(2)];
        [~,radius1,~]=cart2pol(point1(1,1),point1(1,2),point1(1,3));
        [~,radius2,~]=cart2pol(point2(1,1),point2(1,2),point2(1,3));
        
        if radius1>radius2
            centerBarrierPoint(LayerIndex).PointOuter=point1;
            centerBarrierPoint(LayerIndex).PointInner=point2;
        elseif radius1<radius2
            centerBarrierPoint(LayerIndex).PointOuter=point2;
            centerBarrierPoint(LayerIndex).PointInner=point1;
        else 
            disp("동일한 포인트입니다")
        end
    
    end
    LayerTable=[LayerTable,struct2table(centerBarrierPoint)];
else
    disp("AirBarrier가 없는 SPMSM 타입같네요")
end


end