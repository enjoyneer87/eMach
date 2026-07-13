function plot_dq_two_separate(matFile, resDir, outDir)
% PLOT_DQ_TWO_SEPARATE  Two independent dq-plane figures:
%   Figure 1 : speed-resolved AC loss [kW], one subplot per speed.
%   Figure 2 : efficiency-map optimal operating points (currents only).
%
%   plot_dq_two_separate()                          % default thesis paths
%   plot_dq_two_separate(matFile, resDir, outDir)   % custom paths

%% --- paths ------------------------------------------------------------
if nargin < 1 || isempty(matFile)
    matFile = 'D:\KangDH\Thesis\e10\refModel\e10Turn6V261_SyreMMM_B.mat';
end
if nargin < 2 || isempty(resDir)
    resDir = ['D:\KangDH\Thesis\e10\refModel\e10Turn6V261_SyreMMM_B_results\' ...
              'MMM results\'];
end
if nargin < 3 || isempty(outDir)
    outDir = 'D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\figures';
end
if ~exist(outDir, 'dir'); mkdir(outDir); end

%% --- AC loss on the dq grid -------------------------------------------
m         = load(matFile, 'FluxMap_dq');
F         = m.FluxMap_dq;
Pac3D     = F.Pac_total_kW;     % nIq x nId x nSpeed  [kW]
Id_grid   = F.Id;              % nIq x nId  [A]
Iq_grid   = F.Iq;              % nIq x nId  [A]
speed_vec = F.speed_vec(:)';    % 1 x nSpeed [rpm]
nSpeed    = numel(speed_vec);
Id_vec    = Id_grid(1, :);
Iq_vec    = Iq_grid(:, 1);
xr = [min(Id_vec) max(Id_vec)];
yr = [min(Iq_vec) max(Iq_vec)];
fprintf('FluxMap_dq : Id %d, Iq %d, speeds [%s] rpm\n', ...
        numel(Id_vec), numel(Iq_vec), num2str(speed_vec));

theta  = linspace(pi/2, pi, 100);   % Id<0, Iq>0 quadrant
Tgrid  = F.T;                        % torque on the dq grid [Nm]

%% =====================================================================
%  Figure 1 : AC loss [kW] vs (Id,Iq), 4 speed surfaces overlaid in 3D
%% =====================================================================
spdCols = lines(nSpeed);

f1 = figure('Color', 'w', 'Position', [60 60 980 800]);
ax = axes(f1); hold(ax, 'on');
hS = gobjects(nSpeed, 1);
for k = 1:nSpeed
    Pac_slice = squeeze(Pac3D(:, :, k));
    hS(k) = surf(ax, Id_grid, Iq_grid, Pac_slice, ...
                 'FaceColor', spdCols(k, :), 'FaceAlpha', 0.55, ...
                 'EdgeColor', 'none', 'DisplayName', sprintf('%g rpm', speed_vec(k)));
end
view(ax, 135, 25);
grid(ax, 'on'); box(ax, 'on');
camlight(ax, 'headlight'); lighting(ax, 'gouraud');
xlabel(ax, 'I_d  [A]', 'Interpreter', 'tex');
ylabel(ax, 'I_q  [A]', 'Interpreter', 'tex');
zlabel(ax, 'P_{ac}  [kW]', 'Interpreter', 'tex');
title(ax, 'dq-plane AC loss surfaces by speed');
xlim(ax, xr); ylim(ax, yr);
legend(hS, 'Location', 'northeast', 'Box', 'off', 'FontSize', 10);
set(ax, 'FontSize', 11);
saveFig(f1, fullfile(outDir, 'dq_acloss_byspeed.png'));

%% --- optimal operating points (latest TwMap) -------------------------
d = dir(fullfile(resDir, 'TwMap_*'));
d = d([d.isdir]);
assert(~isempty(d), 'No TwMap_* folder found in %s', resDir);
[~, idx] = max([d.datenum]);
twFile = fullfile(resDir, d(idx).name, 'TwMap.mat');
fprintf('Loading operating points: %s\n', twFile);
S     = load(twFile, 'TwMap');
TwMap = S.TwMap;

Id_op = TwMap.Id(:);
Iq_op = TwMap.Iq(:);
n_op  = TwMap.n(:);
valid = isfinite(Id_op) & isfinite(Iq_op) & ...
        (sqrt(Id_op.^2 + Iq_op.^2) > 1e-6);
Id_op = Id_op(valid);  Iq_op = Iq_op(valid);  n_op = n_op(valid);
fprintf('Feasible operating points: %d / %d\n', nnz(valid), numel(valid));

%% =====================================================================
%  Figure 2 : operating points (currents only), colored by speed
%% =====================================================================
Is_rms2 = [100 200 300 460];
Is_pk2  = Is_rms2 * sqrt(2);

Tlevels = 50:50:500;   % iso-torque curves [Nm], SyRE-style

f2 = figure('Color', 'k', 'Position', [80 80 820 700]);
ax = axes(f2); hold(ax, 'on');
set(ax, 'Color', 'k');   % black plot background

% iso-torque curves from the dq flux map (constant-torque loci)
[cT, hT] = contour(ax, Id_grid, Iq_grid, Tgrid, Tlevels, ...
                   'LineColor', [0.55 0.55 0.55], 'LineWidth', 0.7, ...
                   'ShowText', 'on');
clabel(cT, hT, Tlevels(1:2:end), 'FontSize', 7, 'Color', [0.7 0.7 0.7], ...
       'LabelSpacing', 400);

% isocurrent semicircles (white dashed)
for i = 1:numel(Is_pk2)
    r = Is_pk2(i);
    plot(ax, r*cos(theta), r*sin(theta), '--', ...
         'Color', 'w', 'LineWidth', 0.9);
    text(ax, r*cos(theta(1))-2, r*sin(theta(1)), ...
         sprintf(' %g A_{rms}', Is_rms2(i)), 'Color', 'w', ...
         'FontSize', 8, 'HorizontalAlignment', 'right', 'Interpreter', 'tex');
end
scatter(ax, Id_op, Iq_op, 80, n_op, 'filled', ...
        'MarkerEdgeColor', 'w', 'LineWidth', 0.6);
colormap(ax, turbo);
caxis(ax, [min(n_op) max(n_op)]);
cb = colorbar(ax);
cb.Label.String = 'Speed  [rpm]';
cb.Color = 'w'; cb.Label.Color = 'w';
xlabel(ax, 'I_d  [A]', 'Interpreter', 'tex', 'Color', 'w');
ylabel(ax, 'I_q  [A]', 'Interpreter', 'tex', 'Color', 'w');
title(ax, 'dq-plane: efficiency-map optimal operating points', 'Color', 'w');
xlim(ax, xr); ylim(ax, yr);
grid(ax, 'on');
set(ax, 'Layer', 'top', 'FontSize', 11, 'Box', 'on', ...
        'XColor', 'w', 'YColor', 'w', 'GridColor', [0.6 0.6 0.6]);
saveFig(f2, fullfile(outDir, 'dq_operating_points.png'));

%% --- summary ----------------------------------------------------------
fprintf('\n--- summary ---\n');
fprintf('  AC loss range (all speeds) : %.3f .. %.3f kW\n', ...
        min(Pac3D(:)), max(Pac3D(:)));
fprintf('  operating points           : %d\n', numel(Id_op));
fprintf('  speed range (op pts)       : %.0f .. %.0f rpm\n', min(n_op), max(n_op));
fprintf('\nSaved PNGs to %s\n', outDir);

end % main

%% ====================== helpers =======================================
function saveFig(f, fname)
exportgraphics(f, fname, 'Resolution', 200, 'BackgroundColor', f.Color);
fprintf('  wrote %s\n', fname);
close(f);
end
