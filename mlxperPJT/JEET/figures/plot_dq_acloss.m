function plot_dq_acloss(matFile, resDir, outDir)
% PLOT_DQ_ACLOSS  Overlay speed-resolved AC-loss contours and the efficiency-
% map optimal operating points on the dq current plane.
%
%   plot_dq_acloss()                          % use default thesis paths
%   plot_dq_acloss(matFile, resDir, outDir)   % custom paths
%
% Figure 1 : AC-loss contours per speed (colored per speed) + operating
%            points colored by speed.
% Figure 2 : AC-loss contours (mean over speed) + operating points colored
%            by torque.

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
Id_vec    = F.Id(1, :);         % 1 x nId    [A]
Iq_vec    = F.Iq(:, 1);         % nIq x 1    [A]
speed_vec = F.speed_vec(:)';    % 1 x nSpeed [rpm]
nSpeed    = numel(speed_vec);
fprintf('FluxMap_dq : Id %d, Iq %d, speeds [%s] rpm\n', ...
        numel(Id_vec), numel(Iq_vec), num2str(speed_vec));

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
T_op  = TwMap.T(:);

% Drop NaN / infeasible points (MMM leaves Is = 0 outside the envelope).
valid = isfinite(Id_op) & isfinite(Iq_op) & ...
        (sqrt(Id_op.^2 + Iq_op.^2) > 1e-6) & (T_op > 1e-6);
Id_op = Id_op(valid);  Iq_op = Iq_op(valid);
n_op  = n_op(valid);   T_op  = T_op(valid);
fprintf('Feasible operating points: %d / %d\n', nnz(valid), numel(valid));

%% --- shared style -----------------------------------------------------
% Isocurrent semicircles (rms amplitudes -> peak with sqrt(2)).
Is_rms   = [100 200 300 460];
Is_pk    = Is_rms * sqrt(2);
theta    = linspace(pi/2, pi, 100);   % Id<0, Iq>0 quadrant
spdCols  = lines(nSpeed);
nLevels  = 12;

xr = [min(Id_vec) max(Id_vec)];
yr = [min(Iq_vec) max(Iq_vec)];

%% =====================================================================
%  Figure 1 : per-speed AC-loss contours + operating points (speed)
%% =====================================================================
f1 = figure('Color', 'w', 'Position', [80 80 860 680]);
ax = axes(f1); hold(ax, 'on');

hC = gobjects(nSpeed, 1);
for k = 1:nSpeed
    Pac_slice = squeeze(Pac3D(:, :, k));
    [~, hC(k)] = contour(ax, Id_vec, Iq_vec, Pac_slice, nLevels, ...
                         'LineColor', spdCols(k, :), 'LineWidth', 1.1);
end

% isocurrent guides
for r = Is_pk
    plot(ax, r*cos(theta), r*sin(theta), '--', ...
         'Color', [0.55 0.55 0.55], 'LineWidth', 0.8, 'HandleVisibility', 'off');
end
labelIsocurrents(ax, Is_rms, Is_pk, theta);

% operating points colored by speed
scatter(ax, Id_op, Iq_op, 34, n_op, 'filled', ...
        'MarkerEdgeColor', [0.2 0.2 0.2], 'LineWidth', 0.3);

decorateDQ(ax, xr, yr);
colormap(ax, jet);
caxis(ax, [min(n_op) max(n_op)]);
cb = colorbar(ax); cb.Label.String = 'Operating-point speed  [rpm]';
title(ax, 'dq-plane: AC loss contours (speed) & optimal operating points', ...
      'Interpreter', 'tex');
legend(hC, compose('%g rpm', speed_vec), 'Location', 'southwest', ...
       'Box', 'off', 'FontSize', 9);
saveFig(f1, fullfile(outDir, 'dq_acloss_speed.png'));

%% =====================================================================
%  Figure 2 : mean AC-loss contours + operating points (torque)
%% =====================================================================
Pac_mean = mean(Pac3D, 3, 'omitnan');

f2 = figure('Color', 'w', 'Position', [80 80 860 680]);
ax = axes(f2); hold(ax, 'on');

contourf(ax, Id_vec, Iq_vec, Pac_mean, 20, 'LineColor', 'none');
% faint level lines on top for readability
contour(ax, Id_vec, Iq_vec, Pac_mean, 10, 'LineColor', [1 1 1], ...
        'LineWidth', 0.4, 'HandleVisibility', 'off');

for r = Is_pk
    plot(ax, r*cos(theta), r*sin(theta), '--', ...
         'Color', [0.85 0.85 0.85], 'LineWidth', 0.8, 'HandleVisibility', 'off');
end
labelIsocurrents(ax, Is_rms, Is_pk, theta);

scatter(ax, Id_op, Iq_op, 38, T_op, 'filled', ...
        'MarkerEdgeColor', [0.1 0.1 0.1], 'LineWidth', 0.3);

decorateDQ(ax, xr, yr);
colormap(ax, turbo);
cb = colorbar(ax); cb.Label.String = 'Operating-point torque  [Nm]';
caxis(ax, [min(T_op) max(T_op)]);
title(ax, sprintf(['dq-plane: mean AC loss (%g-%g rpm) & operating ' ...
      'points (torque)'], speed_vec(1), speed_vec(end)), 'Interpreter', 'tex');
saveFig(f2, fullfile(outDir, 'dq_acloss_torque.png'));

%% --- console summary --------------------------------------------------
fprintf('\n--- summary ---\n');
fprintf('  operating points (feasible) : %d\n', numel(Id_op));
fprintf('  speed range (op pts)        : %.0f .. %.0f rpm\n', min(n_op), max(n_op));
fprintf('  torque range (op pts)       : %.1f .. %.1f Nm\n', min(T_op), max(T_op));
fprintf('  dq-grid speeds              : [%s] rpm\n', num2str(speed_vec));
fprintf('  AC loss (all speeds)        : %.3f .. %.3f kW\n', ...
        min(Pac3D(:)), max(Pac3D(:)));
fprintf('  Id range                    : %.0f .. %.0f A\n', min(Id_op), max(Id_op));
fprintf('  Iq range                    : %.0f .. %.0f A\n', min(Iq_op), max(Iq_op));
fprintf('\nSaved PNGs to %s\n', outDir);

end % main

%% ====================== helpers =======================================
function decorateDQ(ax, xr, yr)
xlabel(ax, 'I_d  [A]', 'Interpreter', 'tex');
ylabel(ax, 'I_q  [A]', 'Interpreter', 'tex');
xlim(ax, xr); ylim(ax, yr);
grid(ax, 'on');
set(ax, 'Layer', 'top', 'FontSize', 11, 'Box', 'on');
end

function labelIsocurrents(ax, Is_rms, Is_pk, theta)
% Annotate each semicircle near its top (Iq axis, Id ~ 0).
for i = 1:numel(Is_pk)
    r = Is_pk(i);
    text(ax, r*cos(theta(1))-2, r*sin(theta(1)), ...
         sprintf(' %g A_{rms}', Is_rms(i)), ...
         'Color', [0.4 0.4 0.4], 'FontSize', 8, ...
         'HorizontalAlignment', 'right', 'Interpreter', 'tex', ...
         'HandleVisibility', 'off');
end
end

function saveFig(f, fname)
exportgraphics(f, fname, 'Resolution', 200);
fprintf('  wrote %s\n', fname);
close(f);
end
