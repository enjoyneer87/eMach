%DEMO_JEET_PIPELINE  Walkthrough of the MATLAB <-> Python AC-loss pipeline.
%
%   Run section by section (Ctrl+Enter). Every step leaves plain MATLAB
%   variables in the workspace so intermediate data can be inspected.

%% 1. one-time setup (per MATLAB session)
jeetPySetup();                       % pyMotorEnv_310 + jeet_acloss_rbf

%% 2. load a dataset into the workspace
dsSC  = jeetLoadDataset('SC');       % struct of column vectors
dsRef = jeetLoadDataset('Ref');
fprintf('SC: %d pts | AF range [%.2f, %.2f]\n', ...
    numel(dsSC.af), min(dsSC.af), max(dsSC.af));

figure('Name', 'SC AF samples');
scatter3(dsSC.irms_A, dsSC.phase_deg, dsSC.af, 24, ...
    dsSC.speed_rpm/1000, 'filled');
xlabel('I_{rms} [A]'); ylabel('\beta [deg]'); zlabel('AF');
cb = colorbar; cb.Label.String = 'speed [kRPM]'; grid on

%% 3. data quality: neighbor-consistency outlier scan
Tout = jeetScanOutliers('SC');       % empty after adopted exclusion
disp(Tout)

%% 4. adopted model metrics (paper numbers)
mRef = jeetMetrics('Ref')            %#ok<NOPTS>  wMAE 0.56 %
mSC  = jeetMetrics('SC')             %#ok<NOPTS>  wMAE ~5.1 %

%% 5. AF prediction from the workspace (e.g., beta sweep)
beta = 0:2:90;
afHi = jeetPredictAF('SC', 16000, 920, beta);
afLo = jeetPredictAF('SC',  4000, 460, beta);

figure('Name', 'AF vs beta');
plot(beta, afHi, '-o', beta, afLo, '-s'); grid on
xlabel('\beta [deg]'); ylabel('AF');
legend('16 kRPM, 920 A', '4 kRPM, 460 A', 'Location', 'best');

%% 6. SCL-M similarity check (SC low band vs mapped Ref)
Tsim = jeetSimilarityPairs('SC');
fprintf('similarity: %d pairs, mean|dev| = %.2f %%\n', ...
    height(Tsim), mean(abs(Tsim.dev_pct)));

figure('Name', 'similarity parity');
plot(Tsim.af_ref_mapped, Tsim.af_variant, 'o'); hold on
lim = [0 max(Tsim.af_ref_mapped)*1.1];
plot(lim, lim, 'k--'); grid on; axis equal
xlabel('AF_{Ref}(k_r^2\omega, I/k_r, \beta)'); ylabel('AF_{SC}');

%% 7. transfer-plan ablation grid (takes ~1 min)
G = jeetTransferAblation('SC');
figure('Name', 'transfer ablation');
heatmap(G.n_spd8, G.n_base, round(G.wmae_pct, 1));
xlabel('own 8-kRPM cal points'); ylabel('own 16-kRPM base points');
title('SC transfer plan, wMAE [%]');

%% 8. per-speed kW surfaces on the map plane
% source: 'tsfea' | 'hybrid' | 'calibrated'  (calibrated = Hybrid x AF)
jeetPlotLossSurface('SC', 'iphase', 'tsfea');       % measured, I-beta plane
jeetPlotLossSurface('SC', 'dq',     'calibrated');  % model, dq plane

% side-by-side check: hybrid underestimation vs calibrated at one speed
dsSC = jeetLoadDataset('SC');
m16k = abs(dsSC.speed_rpm - 16000) < 1;
af16 = jeetPredictAF('SC', dsSC.speed_rpm(m16k), ...
    dsSC.irms_A(m16k), dsSC.phase_deg(m16k));
figure('Name', '16 kRPM: hybrid vs calibrated vs TS-FEA');
plot3(dsSC.irms_A(m16k), dsSC.phase_deg(m16k), dsSC.tsfea_kW(m16k), ...
    'ko', 'DisplayName', 'TS-FEA'); hold on
plot3(dsSC.irms_A(m16k), dsSC.phase_deg(m16k), dsSC.hybrid_kW(m16k), ...
    'bs', 'DisplayName', 'Hybrid');
plot3(dsSC.irms_A(m16k), dsSC.phase_deg(m16k), ...
    dsSC.hybrid_kW(m16k) .* af16(:), 'r^', 'DisplayName', 'Calibrated');
grid on; view(-35, 25); legend('Location', 'best');
xlabel('I_{rms} [A]'); ylabel('\beta [deg]'); zlabel('P_{AC} [kW]');

%% 9. regenerate the journal PNGs (then copy to Overleaf fig\)
files = jeetMakeFigures();
disp(files.')
