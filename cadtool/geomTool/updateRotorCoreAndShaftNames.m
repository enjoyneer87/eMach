function RotorAssemRegionTable = updateRotorCoreAndShaftNames(RotorAssemRegionTable)
    % Find the region with the minimum distance from the center
    minRegionIndex = find(RotorAssemRegionTable.distanceRFromCenter == min(RotorAssemRegionTable.distanceRFromCenter));
    sketchList = RotorAssemRegionTable.SketchList{minRegionIndex};
    
    % Check if there is a shaft in the regions
    isShaft = isShaftInRegions(RotorAssemRegionTable);

    % Update the names
    if any(isShaft)
        RotorAssemRegionTable.Name(isShaft) = {'Shaft'};
        
        % Find the next closest region to the shaft to assign as RotorCore
        nonShaftIndices = find(~isShaft);
        distancesNonShaft = RotorAssemRegionTable.distanceRFromCenter(nonShaftIndices);
        [~, nextMinIdx] = min(distancesNonShaft);
        rotorCoreIndex = nonShaftIndices(nextMinIdx);
        RotorAssemRegionTable.Name{rotorCoreIndex} = 'RotorCore';
    else
        RotorAssemRegionTable.Name{minRegionIndex} = 'RotorCore';
    end
end