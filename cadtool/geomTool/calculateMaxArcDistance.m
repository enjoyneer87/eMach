function maxDistance = calculateMaxArcDistance(ArcTable)
    if isempty(ArcTable)
        maxDistance = 0;
        return;
    end

    % Calculate distances from origin for arc start, end, and center points
    distances = sqrt(ArcTable.StartVertexTablex.^2 + ArcTable.StartVertexTabley.^2);
    distances = [distances; sqrt(ArcTable.EndVertexTablex.^2 + ArcTable.EndVertexTabley.^2)];
    distances = [distances; sqrt(ArcTable.CenterVertexTablex.^2 + ArcTable.CenterVertexTabley.^2)];

    % Find the maximum distance
    maxDistance = max(distances);
end
