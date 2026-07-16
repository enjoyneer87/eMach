function figH = jeetPlotLossSurface(scale, plane, source)
%JEETPLOTLOSSSURFACE  Per-speed AC-loss [kW] surfaces on the map plane.
%
%   figH = jeetPlotLossSurface(scale, plane, source)
%
%   plane  : 'iphase' (default)  x = I_rms [A],  y = beta [deg]
%            'dq'                x = i_d [A],    y = i_q [A]   (peak)
%   source : 'tsfea' (default)   measured TS-FEA loss
%            'hybrid'            uncorrected Hybrid loss
%            'calibrated'        Hybrid x AF (adopted Separable RBF)
%
%   One subplot per speed; the interpolated surface (griddata, linear)
%   is overlaid with the actual sample points. Returns the figure handle.
%
%   Examples:
%       jeetPlotLossSurface('SC');                        % TS-FEA, I-beta
%       jeetPlotLossSurface('SC', 'dq', 'calibrated');
%       jeetPlotLossSurface('Ref', 'iphase', 'hybrid');

if nargin < 2 || isempty(plane),  plane = 'iphase'; end
if nargin < 3 || isempty(source), source = 'tsfea'; end

ds = jeetLoadDataset(scale);

switch lower(source)
    case 'tsfea'
        z = ds.tsfea_kW;   srcName = 'TS-FEA';
    case 'hybrid'
        z = ds.hybrid_kW;  srcName = 'Hybrid (uncorrected)';
    case 'calibrated'
        af = jeetPredictAF(scale, ds.speed_rpm, ds.irms_A, ds.phase_deg);
        z = ds.hybrid_kW .* af(:);
        srcName = 'Calibrated (Hybrid x AF)';
    otherwise
        error('jeetPlotLossSurface:source', ...
            'source must be tsfea | hybrid | calibrated');
end

switch lower(plane)
    case 'iphase'
        x = ds.irms_A;  y = ds.phase_deg;
        xLab = 'I_{rms} [A]';  yLab = '\beta [deg]';
    case 'dq'
        amp = ds.irms_A * sqrt(2);
        phr = (ds.phase_deg + 90) * pi / 180;
        x = amp .* cos(phr);  y = amp .* sin(phr);
        xLab = 'i_d [A]';  yLab = 'i_q [A]';
    otherwise
        error('jeetPlotLossSurface:plane', 'plane must be iphase | dq');
end

speeds = unique(ds.speed_rpm);
nSpd = numel(speeds);
nCol = ceil(sqrt(nSpd));
nRow = ceil(nSpd / nCol);

figH = figure('Name', sprintf('%s | %s | %s plane', ...
    scale, srcName, upper(plane)), 'Color', 'w');
tl = tiledlayout(figH, nRow, nCol, 'TileSpacing', 'compact', ...
    'Padding', 'compact');

for k = 1:nSpd
    m = abs(ds.speed_rpm - speeds(k)) < 1;
    xk = x(m); yk = y(m); zk = z(m);

    ax = nexttile(tl);
    if nnz(m) >= 4
        xi = linspace(min(xk), max(xk), 60);
        yi = linspace(min(yk), max(yk), 60);
        [XI, YI] = meshgrid(xi, yi);
        ZI = griddata(xk, yk, zk, XI, YI, 'linear');   % NaN outside hull
        surf(ax, XI, YI, ZI, 'EdgeColor', 'none', 'FaceAlpha', 0.9);
        hold(ax, 'on');
    end
    scatter3(ax, xk, yk, zk, 26, 'k', 'filled', ...
        'MarkerEdgeColor', 'w', 'LineWidth', 0.4);
    hold(ax, 'off');

    title(ax, sprintf('%.0f RPM  (max %.1f kW)', speeds(k), max(zk)));
    xlabel(ax, xLab); ylabel(ax, yLab); zlabel(ax, 'P_{AC} [kW]');
    view(ax, -35, 30); grid(ax, 'on');
    cb = colorbar(ax); cb.Label.String = 'kW';
end

title(tl, sprintf('%s — %s AC loss on the %s plane', ...
    scale, srcName, upper(plane)));
end
