function createGeometryFromShapes(entities)
    % Create a PDE model
    model = createpde;

    % Initialize geometry description matrix and name array
    gd = [];
    ns = [];
    sf = '';

    for i = 1:length(entities)
        if ~isempty(entities(i).line)
            % Extract line information
            x1 = entities(i).line(1);
            y1 = entities(i).line(2);
            x2 = entities(i).line(3);
            y2 = entities(i).line(4);
            
            % Add line to geometry description matrix
            gd = [gd, 2, 2, x1, y1, x2, y2, 0, 0, 0, 0];
            ns = [ns, ['L', num2str(i)]];
            if isempty(sf)
                sf = ['L', num2str(i)];
            else
                sf = [sf, '+L', num2str(i)];
            end
        end
        
        if ~isempty(entities(i).arc)
            % Extract arc information
            cx = entities(i).arc(1);
            cy = entities(i).arc(2);
            r = entities(i).arc(3);
            startAngle = entities(i).arc(4);
            endAngle = entities(i).arc(5);
            
            % Add arc to geometry description matrix
            gd = [gd, 1, cx, cy, r, deg2rad(startAngle), deg2rad(endAngle), 0, 0];
            ns = [ns, ['A', num2str(i)]];
            if isempty(sf)
                sf = ['A', num2str(i)];
            else
                sf = [sf, '+A', num2str(i)];
            end
        end
    end

    % Create geometry description matrix
    gd = reshape(gd, [], length(ns));
    ns = char(ns);
    ns = reshape(ns', 1, [])';

    % Create a decomposed geometry object
    g = decsg(gd, sf, ns);

    % Assign the geometry to the PDE model
    geometryFromEdges(model, g);

    % Plot the geometry
    figure;
    pdegplot(model, 'EdgeLabels', 'on');
    axis equal;
    title('PDE Model Geometry with Lines and Arcs');
end
