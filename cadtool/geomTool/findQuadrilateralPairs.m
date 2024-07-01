function foundPairs = findQuadrilateralPairs(LineTable)
    % Initialize variables to store found pairs
    foundPairs = [];
    centers=[];
    % Iterate over each line in LineTable to find pairs
    for i = 1:height(LineTable)
        for j = i+1:height(LineTable)
            for k = j+1:height(LineTable)
                for l = k+1:height(LineTable)
                    % Get coordinates of the lines
                    line1 = [LineTable.StartVertexTablex(i), LineTable.StartVertexTabley(i); LineTable.EndVertexTablex(i), LineTable.EndVertexTabley(i)];
                    line2 = [LineTable.StartVertexTablex(j), LineTable.StartVertexTabley(j); LineTable.EndVertexTablex(j), LineTable.EndVertexTabley(j)];
                    line3 = [LineTable.StartVertexTablex(k), LineTable.StartVertexTabley(k); LineTable.EndVertexTablex(k), LineTable.EndVertexTabley(k)];
                    line4 = [LineTable.StartVertexTablex(l), LineTable.StartVertexTabley(l); LineTable.EndVertexTablex(l), LineTable.EndVertexTabley(l)];

                    % Check if the lines form a quadrilateral
                    if isQuadrilateral(line1, line2, line3, line4)
                        foundPairs = [foundPairs; i, j, k, l];
                        centers = [centers; mean([line1(:, 1); line2(:, 1); line3(:, 1); line4(:, 1)]), mean([line1(:, 2); line2(:, 2); line3(:, 2); line4(:, 2)])];
                    end
                end
            end
        end
    end

    foundPairs=[foundPairs centers];
end
