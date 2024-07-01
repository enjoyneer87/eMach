function resultTable = devProcessRegions(RegionTable)
    % Initialize variables to store all found pairs
    regionIdxArray = [];
    line1IdxArray = [];
    line2IdxArray = [];

    % Iterate over each region in RegionTable
    for regionIdx = 1:height(RegionTable)
        sketchList = RegionTable.SketchList{regionIdx};
        LineTable = sketchList{2};

        % Call the function to find quadrilateral pairs in the current region
        foundPairs = findQuadrilateralPairs(LineTable);

        % Store found pairs with region index
        for k = 1:size(foundPairs, 1)
            regionIdxArray = [regionIdxArray; regionIdx, RegionTable.Name(regionIdx)];
            line1IdxArray = [line1IdxArray; foundPairs(k, 1)];
            line2IdxArray = [line2IdxArray; foundPairs(k, 2)];
        end
    end

    % Create a table from the collected data
    resultTable = table(regionIdxArray, line1IdxArray, line2IdxArray, ...
                        'VariableNames', {'RegionIdx', 'Line1Idx', 'Line2Idx'});

    % Display the result table
    disp('Found pairs of quadrilateral lines in each region:');
    disp(resultTable);

    % Optional: Plot the lines to visualize the found pairs
    figure;
    hold on;
    for regionIdx = 1:height(RegionTable)
        sketchList = RegionTable.SketchList{regionIdx};
        LineTable = sketchList{2};

        % Plot all lines
        for i = 1:height(LineTable)
            plot([LineTable.StartVertexTablex(i), LineTable.EndVertexTablex(i)], [LineTable.StartVertexTabley(i), LineTable.EndVertexTabley(i)], 'b');
        end
    end
    
    for k = 1:height(resultTable)
        regionIdx = resultTable.RegionIdx(k);
        sketchList = RegionTable.SketchList{regionIdx{:}};
        LineTable = sketchList{2};
        i = resultTable.Line1Idx(k);
        j = resultTable.Line2Idx(k);
        if i <= height(LineTable) && j <= height(LineTable)
            plot([LineTable.StartVertexTablex(i), LineTable.EndVertexTablex(i)], [LineTable.StartVertexTabley(i), LineTable.EndVertexTabley(i)], 'r', 'LineWidth', 2);
            plot([LineTable.StartVertexTablex(j), LineTable.EndVertexTablex(j)], [LineTable.StartVertexTabley(j), LineTable.EndVertexTabley(j)], 'r', 'LineWidth', 2);
        end
    end
    hold off;

    xlabel('x');
    ylabel('y');
    title('Quadrilateral Line Segments');
end
