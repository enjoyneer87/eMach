function isQuad = isQuadrilateral(line1, line2, line3, line4)
    % Check if there are at least two pairs of parallel lines
    if areLinesParallel(line1, line3) && areLinesParallel(line2, line4)
        % Check if the parallel lines are not connected
        if ~areLinesConnected(line1, line3) && ~areLinesConnected(line2, line4)
            isQuad = true;
            return;
        end
    elseif areLinesParallel(line1, line4) && areLinesParallel(line2, line3)
        if ~areLinesConnected(line1, line4) && ~areLinesConnected(line2, line3)
            isQuad = true;
            return;
        end
    elseif areLinesParallel(line1, line2) && areLinesParallel(line3, line4)
        if ~areLinesConnected(line1, line2) && ~areLinesConnected(line3, line4)
            isQuad = true;
            return;
        end
    end
    isQuad = false;
end
