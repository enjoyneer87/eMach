function point1=convertXYZData2Array(pointData)
    if isstruct(pointData)
    point1 = [pointData.x, pointData.y,pointData.z];
    elseif istable(pointData)
    point1=[pointData.x,pointData.y,0];
    else
    point1=pointData;
    end

end