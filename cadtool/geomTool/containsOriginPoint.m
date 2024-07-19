function iscontain = containsOriginPoint(ArcTable)
    if isempty(ArcTable)
        disp('ArcTable is empty.');
        iscontain = 0;
        return;
    end

    % Check for arcs with zero start or end points
    ZeroStartPoints = ArcTable(ArcTable.StartVertexTablex == 0 & ArcTable.StartVertexTabley == 0, :);
    ZeroEndPoints = ArcTable(ArcTable.EndVertexTablex == 0 & ArcTable.EndVertexTabley == 0, :);

    if ~isempty(ZeroStartPoints) || ~isempty(ZeroEndPoints)
        disp('There is a zero point.');
        iscontain = 1;
    else
        % disp('No zero points.');
        iscontain = 0;
    end
end
