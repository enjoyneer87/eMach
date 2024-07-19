function foundPairs = findEqualLengthParallelLines(LineTable)
    % Function to calculate length of a line segment
    % lineLength = @(x1, y1, x2, y2) sqrt((x2 - x1).^2 + (y2 - y1).^2);
    
    % if isvarofTable(LineTable,'length')
    % length1 =LineTable.length(i);
    % length2 =LineTable.length(j);
    % else
    % length1 = lineLength(LineTable.StartVertexTablex(i), LineTable.StartVertexTabley(i), LineTable.EndVertexTablex(i), LineTable.EndVertexTabley(i));
    % length2 = lineLength(LineTable.StartVertexTablex(j), LineTable.StartVertexTabley(j), LineTable.EndVertexTabley(j), LineTable.EndVertexTabley(j));
    % end
    % Tolerance for parallelism
    parallelTolerance = 1e-6;

    % Initialize variables to store found pairs
    foundPairs = [];

    % Iterate over each line in LineTable to find pairs
    for i = 1:height(LineTable)
        for j = i+1:height(LineTable)
            % Calculate slopes
            deltax1 = LineTable.EndVertexTablex(i) - LineTable.StartVertexTablex(i);
            deltay1 = LineTable.EndVertexTabley(i) - LineTable.StartVertexTabley(i);
            deltax2 = LineTable.EndVertexTablex(j) - LineTable.StartVertexTablex(j);
            deltay2 = LineTable.EndVertexTabley(j) - LineTable.StartVertexTabley(j);

            if abs(deltax1 * deltay2 - deltay1 * deltax2) < parallelTolerance
                % Check if lines are not connected
                if ~areLinesConnected(LineTable, i, j)
                    foundPairs = [foundPairs; i, j];
                end
            end
        end
    end
end

