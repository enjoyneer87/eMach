function radius = calcArcRadius(ArcTable,centerVertex)
    if nargin>1
    startVertex=ArcTable;
    % Calculate the radius for each arc using the center and start points
    radius = sqrt((startVertex(1) - centerVertex(1)).^2 + ...
                 (startVertex(2) - centerVertex(2)).^2);
    else
    % Calculate the radius for each arc using the center and start points
    radius = sqrt((ArcTable.StartVertexTablex - ArcTable.CenterVertexTablex).^2 + ...
                 (ArcTable.StartVertexTabley - ArcTable.CenterVertexTabley).^2);
    end
end