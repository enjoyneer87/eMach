function connected = areLinesConnected(LineTable, i, j)
    if nargin>2
    % Function to check if two lines are connected
    connected = ...
        isequal([LineTable.EndVertexTablex(i), LineTable.EndVertexTabley(i)], [LineTable.StartVertexTablex(j), LineTable.StartVertexTabley(j)]) || ...
        isequal([LineTable.StartVertexTablex(i), LineTable.StartVertexTabley(i)], [LineTable.EndVertexTablex(j), LineTable.EndVertexTabley(j)]) || ...
        isequal([LineTable.EndVertexTablex(i), LineTable.EndVertexTabley(i)], [LineTable.EndVertexTablex(j), LineTable.EndVertexTabley(j)]) || ...
        isequal([LineTable.StartVertexTablex(i), LineTable.StartVertexTabley(i)], [LineTable.StartVertexTablex(j), LineTable.StartVertexTabley(j)]);



    % function connected = areLinesConnected(line1, line2)
    else
        line1=LineTable;
        line2=i;
        
    % Check if two lines are connected at any end points
    connected = ...
        isequal(line1(2,:), line2(1,:)) || ...
        isequal(line1(1,:), line2(2,:)) || ...
        isequal(line1(2,:), line2(2,:)) || ...
        isequal(line1(1,:), line2(1,:));
    end



end