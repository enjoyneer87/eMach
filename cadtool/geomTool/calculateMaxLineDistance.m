function maxDistance = calculateMaxLineDistance(LineTable)
    if isempty(LineTable)
        maxDistance = 0;
        return;
    end

    % Calculate distances from origin for line start and end points
    distances = sqrt(LineTable.StartVertexTablex.^2 + LineTable.StartVertexTabley.^2);
    distances = [distances; sqrt(LineTable.EndVertexTablex.^2 + LineTable.EndVertexTabley.^2)];

    % Find the maximum distance
    maxDistance = max(distances);
end