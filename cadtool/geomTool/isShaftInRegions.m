function isShaft = isShaftInRegions(regionTable)
    isShaft = false(height(regionTable), 1);

    for regionIndex = 1:height(regionTable)
        sketchList = regionTable.SketchList{regionIndex};
        isShaft(regionIndex) = checkcontainsOriginPointinLineArc(sketchList);
    end

    if any(isShaft)
    isShaft=find(isShaft);
    else
    isShaft=0;
    end
end
