function plot_current_acloss_maps(resDir, outDir)
% PLOT_CURRENT_ACLOSS_MAPS  Generate current maps (Id, Iq, Is) and SyRE AC
% copper-loss map from an MMM_MaxTw TwMap result on the speed-torque grid.
%
%   plot_current_acloss_maps()                 % use default thesis paths
%   plot_current_acloss_maps(resDir)           % pick latest TwMap_* in resDir
%   plot_current_acloss_maps(resDir, outDir)   % custom PNG output folder

if nargin < 1 || isempty(resDir)
    resDir = ['D:\KangDH\Thesis\e10\refModel\e10Turn6V261_SyreMMM_B_results\' ...
              'MMM results\'];
end
if nargin < 2 || isempty(outDir)
    outDir = 'D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\figures';
end

%% --- locate latest TwMap folder ---------------------------------------
d = dir(fullfile(resDir, 'TwMap_*'));
d = d([d.isdir]);
assert(~isempty(d), 'No TwMap_* folder found in %s', resDir);
[~, idx] = max([d.datenum]);
twFile = fullfile(resDir, d(idx).name, 'TwMap.mat');
fprintf('Loading: %s\n', twFile);
S = load(twFile);
assert(isfield(S, 'TwMap'), 'TwMap variable missing in %s', twFile);
TwMap = S.TwMap;

fprintf('TwMap fields: %s\n', strjoin(fieldnames(TwMap), ', '));

%% --- grid -------------------------------------------------------------
n = TwMap.n;          % speed [rpm]   (21x17)
T = TwMap.T;          % torque [Nm]

% d/q currents (amplitude). Id is negative (flux-weakening), Iq positive.
Id = TwMap.Id;
Iq = TwMap.Iq;
Is = sqrt(Id.^2 + Iq.^2);   % current magnitude

% AC copper loss directly from SyRE MMM map [W]
PjAC = TwMap.PjAC;
PjDC = TwMap.PjDC;
Pjs  = TwMap.Pjs;           % total stator copper loss = PjDC + PjAC

%% --- feasibility mask -------------------------------------------------
% Outside the torque-speed envelope MMM leaves currents at 0. Mask those
% (and the trivial T=0 row) as NaN so the contour plots stay clean.
feas = (Is > 1e-6) & (T > 1e-6);
mask = @(X) maskNaN(X, feas);

IsM   = mask(Is);
IdM   = mask(Id);
IqM   = mask(Iq);
PjACm = mask(PjAC);

if ~exist(outDir, 'dir'); mkdir(outDir); end

%% --- Figure 1: current magnitude Is -----------------------------------
f1 = figure('Color', 'w', 'Position', [100 100 760 560]);
contourf(n, T, IsM, 24, 'LineColor', 'none');
decorate('Current magnitude  I_s = \surd(I_d^2 + I_q^2)', 'I_s  [A]');
saveFig(f1, fullfile(outDir, 'current_map_Is.png'));

%% --- Figure 2: Id / Iq side by side -----------------------------------
f2 = figure('Color', 'w', 'Position', [100 100 1180 520]);
subplot(1, 2, 1);
contourf(n, T, IdM, 24, 'LineColor', 'none');
decorate('d-axis current  I_d', 'I_d  [A]');
subplot(1, 2, 2);
contourf(n, T, IqM, 24, 'LineColor', 'none');
decorate('q-axis current  I_q', 'I_q  [A]');
saveFig(f2, fullfile(outDir, 'current_map_dq.png'));

%% --- Figure 3: SyRE AC copper loss [kW] -------------------------------
f3 = figure('Color', 'w', 'Position', [100 100 760 560]);
contourf(n, T, PjACm / 1e3, 24, 'LineColor', 'none');
decorate('SyRE AC copper loss  P_{j,AC}', 'P_{j,AC}  [kW]');
saveFig(f3, fullfile(outDir, 'ac_loss_syre_map.png'));

%% --- console summary --------------------------------------------------
fprintf('\n--- summary over feasible points ---\n');
fprintf('  Is   : %.1f .. %.1f A\n',  min(IsM(:)),   max(IsM(:)));
fprintf('  Id   : %.1f .. %.1f A\n',  min(IdM(:)),   max(IdM(:)));
fprintf('  Iq   : %.1f .. %.1f A\n',  min(IqM(:)),   max(IqM(:)));
fprintf('  PjAC : %.0f .. %.0f W (%.2f .. %.2f kW)\n', ...
        min(PjACm(:)), max(PjACm(:)), min(PjACm(:))/1e3, max(PjACm(:))/1e3);
acFrac = 100 * PjAC ./ max(Pjs, eps);
acFrac(~feas) = NaN;
fprintf('  PjAC/Pjs : up to %.1f %% of stator copper loss\n', max(acFrac(:)));
fprintf('\nSaved PNGs to %s\n', outDir);

end % main

%% ====================== helpers =======================================
function Y = maskNaN(X, feas)
Y = X; Y(~feas) = NaN;
end

function decorate(ttl, cbarLabel)
ax = gca;
xlabel('Speed  (rpm)');
ylabel('Torque  (Nm)');
title(ttl, 'Interpreter', 'tex');
colormap(ax, turbo);
cb = colorbar;
cb.Label.String = cbarLabel;
cb.Label.Interpreter = 'tex';
set(ax, 'Layer', 'top', 'FontSize', 11, 'Box', 'on');
axis tight;
end

function saveFig(f, fname)
exportgraphics(f, fname, 'Resolution', 200);
fprintf('  wrote %s\n', fname);
close(f);
end
