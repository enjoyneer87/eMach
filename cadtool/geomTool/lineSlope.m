function slope = lineSlope(line)
    % Calculate the slope of a line
    slope = (line(2,2) - line(1,2)) / (line(2,1) - line(1,1));
end
