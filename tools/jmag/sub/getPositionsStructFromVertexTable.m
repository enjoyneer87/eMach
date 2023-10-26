function VertexPosition=getPositionsStructFromVertexTable(vertexTable,jmagApp)

Model=jmagApp.GetCurrentModel;
% tolerance = 1e-5; % 허용 가능한 오차 범위 설정 (원하는 값으로 조정)

for VertexIndex=1:height(vertexTable)
    PositionObj=Model.GetVertexPosition(vertexTable.VertexIds(VertexIndex));
    x=PositionObj.GetX;
    y=PositionObj.GetY;
    z=PositionObj.GetZ;
    [theta,Radius]=cart2pol(x,y,z);
    VertexPosition(VertexIndex).x=x;
    VertexPosition(VertexIndex).y=y;
    VertexPosition(VertexIndex).z=z;
    VertexPosition(VertexIndex).theta=rad2deg(theta);
    VertexPosition(VertexIndex).Radius=Radius ;
    % VertexPosition(VertexIndex).VertexIds=vertexTable.VertexIds(VertexIndex);
    % isSimilar = abs(VertexPosition.theta(VertexIndex) - CenterAngle) < tolerance;
    % if isSimilar
    VertexPosition(VertexIndex).IsCenterVertex=NaN;

end

end