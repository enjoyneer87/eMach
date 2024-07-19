function parallel = areLinesParallel(line1, line2)
    % Calculate slopes
    slope1 = (line1(2,2) - line1(1,2)) / (line1(2,1) - line1(1,1));
    slope2 = (line2(2,2) - line2(1,2)) / (line2(2,1) - line2(1,1));
    
    % Check if slopes are equal
    parallel = abs(slope1 - slope2) < 1e-6;
end
