function regions = findRegionsWith2LinePairN2ArcPair(regionTable)

    regions = [];

    % Iterate over each region in RegionTable
    for regionIdx =1:height(regionTable)
        sketchList = regionTable.SketchList{regionIdx};
        arcTable = sketchList{1};
        lineTable = sketchList{2}; 
        parallelPairs = findParallelLinePairs(lineTable);
        is2LinePairs=length(parallelPairs);
        
        %%
        filletAngle=uniquetol(arcTable.Angle,0.001);
        if height(arcTable)==4 &&isscalar(filletAngle)
            is2ArcPairs=1;
        elseif height(arcTable)==2 &&isscalar(filletAngle)
            is2ArcPairs=1;
        else
            is2ArcPairs=0;
        end

        if is2LinePairs&&is2ArcPairs
        regions = [regions; regionIdx];
        end
    end

end