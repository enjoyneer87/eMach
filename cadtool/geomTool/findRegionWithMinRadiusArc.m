function [minRadiusRegionIdx, minRadius] = findRegionWithMinRadiusArc(RegionTable)
    minRadius = inf;
    minRadiusRegionIdx = -1;

    % Iterate over each region in RegionTable
    for regionIdx = 1:height(RegionTable)
        sketchList = RegionTable.SketchList{regionIdx};
        ArcTable = sketchList{1}; % Assume ArcTable is the first element in sketchList

        % Check if ArcTable is empty
        if isempty(ArcTable)
            continue;
        end

        % Filter arcs with CenterVertexTable at (0, 0)
        validArcs = ArcTable(ArcTable.CenterVertexTablex == 0 & ArcTable.CenterVertexTabley == 0, :);
        
        % Check if there are any valid arcs
        if isempty(validArcs)
            continue;
        end

        % Calculate the radius for each valid arc
        radii = calcArcRadius(validArcs);

        % Find the minimum radius in the current valid ArcTable
        [currentMinRadius, ~] = min(radii);

        % Update the overall minimum radius and region index if necessary
        if currentMinRadius < minRadius
            minRadius = currentMinRadius;
            minRadiusRegionIdx = regionIdx;
        end
    end
