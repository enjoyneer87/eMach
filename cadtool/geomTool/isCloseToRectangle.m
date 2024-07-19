function isRect = isCloseToRectangle(line1, line2, line3, line4)
    % Check if the given four lines form a shape close to a rectangle or parallelogram
    lengths = [lineLength(line1); lineLength(line2); lineLength(line3); lineLength(line4)];
    slopes = [lineSlope(line1); lineSlope(line2); lineSlope(line3); lineSlope(line4)];

    % Check if opposite sides are parallel and of similar length
    isParallel = @(a, b) abs(a - b) < 1e-6;
    isSimilarLength = @(a, b) abs(a - b) / max(a, b) < 0.1; % Allow 10% difference

    if isParallel(slopes(1), slopes(3)) && isParallel(slopes(2), slopes(4)) && ...
       isSimilarLength(lengths(1), lengths(3)) && isSimilarLength(lengths(2), lengths(4))
        isRect = true;
    else
        isRect = false;
    end
end