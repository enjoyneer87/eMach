function regions = findRegionsWithNoOuterArcs(regionTable)
    regions = [];

    % Iterate over each region in RegionTable
    for regionIdx = 1:height(regionTable)
        

        sketchList = regionTable.SketchList{regionIdx};
        arcTable = sketchList{1};
        lineTable = sketchList{2};

        % If there are no arcs, include the region
        if isempty(arcTable)
            regions = [regions; regionIdx];
            continue;
        end

        % Find parallel line pairs
        parallelPairs = findParallelLinePairs(lineTable);

        if isempty(parallelPairs)
            continue;
        end

        % Calculate the maximum distance from origin for arcs
        if ~isempty(arcTable)
            maxArcDistance = calculateMaxArcDistance(arcTable);
            
            % Check if any parallel line pair is not closer to the origin than any arc
            allPairsCloser = true;
            for k = 1:size(parallelPairs, 1)
                line1Idx = parallelPairs(k, 1);
                line2Idx = parallelPairs(k, 2);
    
                % Calculate the maximum distance from origin for the parallel line pair
                maxLineDistance1 = calculateMaxLineDistance(lineTable(line1Idx, :));
                maxLineDistance2 = calculateMaxLineDistance(lineTable(line2Idx, :));
    
                % If the maximum line distance is not less than the maximum arc distance
                if maxLineDistance1 >= maxArcDistance || maxLineDistance2 >= maxArcDistance
                    allPairsCloser = false;
                    break;
                end
            end
        end
    
         MaxLineDistanceIncldNonParallelLine=calculateMaxLineDistance(lineTable);
         isLineMax=MaxLineDistanceIncldNonParallelLine>maxArcDistance;
        % If no arc is outside of any line pair, include the region
        if allPairsCloser && isLineMax
            regions = [regions; regionIdx];
        end
    end

    % Display the result
    if isempty(regions)
        disp('No regions found where no arc is outside of any line pair.');
    else
        fprintf('Regions where no arc is outside of any line pair: %s\n', num2str(regions'));
    end
end
