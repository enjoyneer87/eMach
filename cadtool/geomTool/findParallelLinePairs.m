function parallelPairs = findParallelLinePairs(lineTable)
    parallelPairs = [];
    numLines = height(lineTable);

    for i = 1:numLines
        for j = i+1:numLines
            line1 = [lineTable.StartVertexTablex(i), lineTable.StartVertexTabley(i); lineTable.EndVertexTablex(i), lineTable.EndVertexTabley(i)];
            line2 = [lineTable.StartVertexTablex(j), lineTable.StartVertexTabley(j); lineTable.EndVertexTablex(j), lineTable.EndVertexTabley(j)];
            if areLinesParallel(line1, line2)
                parallelPairs = [parallelPairs; i, j];
            end
        end
    end
end