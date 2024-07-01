function isShaft=checkcontainsOriginPointinLineArc(sketchList)
    % Extract the sketch list for the specified regio
    % Assume ArcTable is the first element and LineTable is the second element in sketchList
    ArcTable = sketchList{1};
    LineTable = sketchList{2};

    % Check ArcTable for non-zero start or end points
    isArcContain = containsOriginPoint(ArcTable);
    % Check LineTable for non-zero start or end points
    isLineContain = containsOriginPoint(LineTable);

    if (isArcContain||isLineContain)
    isShaft=1;
    else
    isShaft=0;
    end
end
