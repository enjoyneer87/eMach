function h = plotMESFieldsFromD(D, varargin)
% plotMESFieldsFromD
% Visualize fields from loadMESviaPythonForMATLAB output struct D.
%
% Usage:
%   h = plotMESFieldsFromD(D);                          % default: elem B magnitude scatter
%   h = plotMESFieldsFromD(D, 'Mode', 'meshB');        % mesh patch with |B|
%   h = plotMESFieldsFromD(D, 'Mode', 'scatterA');     % element-center scatter(A)
%   h = plotMESFieldsFromD(D, 'Mode', 'quiverB');      % element-center quiver(Bx,By)
%   h = plotMESFieldsFromD(D, 'Mode', 'meshA_node');   % node-averaged A on mesh
%
% Name-Value:
%   Mode        : 'scatterB' | 'scatterA' | 'meshB' | 'meshA_node' | 'quiverB'
%   Figure      : figure handle (optional)
%   MarkerSize  : scatter marker size (default: 8)
%   QuiverStep  : subsample for quiver (default: 20)
%   QuiverScale : quiver scale factor (default: 0.8)

    p = inputParser;
    addRequired(p, 'D', @(x) isstruct(x));
    addParameter(p, 'Mode', 'scatterB', @(x) ischar(x) || isstring(x));
    addParameter(p, 'Figure', [], @(x) isempty(x) || isgraphics(x, 'figure'));
    addParameter(p, 'MarkerSize', 8, @(x) isnumeric(x) && isscalar(x) && x > 0);
    addParameter(p, 'QuiverStep', 20, @(x) isnumeric(x) && isscalar(x) && x >= 1);
    addParameter(p, 'QuiverScale', 0.8, @(x) isnumeric(x) && isscalar(x) && x > 0);
    parse(p, D, varargin{:});

    mode = lower(string(p.Results.Mode));

    reqFields = {'Elements','Nodes','Bx','By','A','NodeXYmm'};
    for i = 1:numel(reqFields)
        if ~isfield(D, reqFields{i})
            error('D.%s is missing.', reqFields{i});
        end
    end

    X = D.NodeXYmm(:,1);
    Y = D.NodeXYmm(:,2);
    tri = [D.Elements.Node1, D.Elements.Node2, D.Elements.Node3];

    if isempty(p.Results.Figure)
        fig = figure;
    else
        fig = p.Results.Figure;
        figure(fig);
    end
    clf(fig);

    bx = D.Bx;
    by = D.By;
    bmag = sqrt(bx.^2 + by.^2);
    Aval = D.A;

    xc = (X(tri(:,1)) + X(tri(:,2)) + X(tri(:,3))) / 3;
    yc = (Y(tri(:,1)) + Y(tri(:,2)) + Y(tri(:,3))) / 3;

    switch mode
        case "scatterb"
            h = scatter(xc, yc, p.Results.MarkerSize, bmag, 'filled');
            axis equal;
            colorbar;
            title('|B| at element centers');
            xlabel('X [mm]'); ylabel('Y [mm]');

        case "scattera"
            h = scatter(xc, yc, p.Results.MarkerSize, Aval, 'filled');
            axis equal;
            colorbar;
            title('A at element centers');
            xlabel('X [mm]'); ylabel('Y [mm]');

        case "meshb"
            h = patch('Faces', tri, 'Vertices', [X Y], ...
                'FaceVertexCData', bmag, ...
                'FaceColor', 'flat', ...
                'EdgeColor', [0.7 0.7 0.7], ...
                'LineWidth', 0.2);
            axis equal;
            colorbar;
            title('|B| on mesh (element-wise)');
            xlabel('X [mm]'); ylabel('Y [mm]');

        case "mesha_node"
            A_node = localElementToNodeMean(Aval, tri, size(D.NodeXYmm,1));
            h = patch('Faces', tri, 'Vertices', [X Y], ...
                'FaceVertexCData', A_node, ...
                'FaceColor', 'interp', ...
                'EdgeColor', [0.7 0.7 0.7], ...
                'LineWidth', 0.2);
            axis equal;
            colorbar;
            title('A on mesh (node-averaged)');
            xlabel('X [mm]'); ylabel('Y [mm]');

        case "quiverb"
            qstep = max(1, round(p.Results.QuiverStep));
            idx = 1:qstep:numel(xc);
            h = quiver(xc(idx), yc(idx), bx(idx), by(idx), p.Results.QuiverScale, 'k');
            axis equal;
            title('B vector at element centers');
            xlabel('X [mm]'); ylabel('Y [mm]');

        otherwise
            error('Unknown Mode: %s', mode);
    end
end

function nodeVal = localElementToNodeMean(elemVal, tri, nNode)
    sumVal = zeros(nNode,1);
    cntVal = zeros(nNode,1);

    for k = 1:size(tri,1)
        ids = tri(k,:);
        sumVal(ids) = sumVal(ids) + elemVal(k);
        cntVal(ids) = cntVal(ids) + 1;
    end

    nodeVal = sumVal ./ max(cntVal,1);
end
