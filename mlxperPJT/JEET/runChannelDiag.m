%% runChannelDiag.m — Fig15 Δη 부호 역전의 손실 채널 분해 진단
% Δ(ch) = Hybrid − FullFEA 를 채널별로 맵·통계로 분해하고,
% 각 mot의 전력수지 닫힘(Terminal − Loss − Shaft ≈ 0)을 검사한다.

scriptDir = fileparts(mfilename('fullpath'));
effDir = fullfile(scriptDir, 'map_exports', 'e10', 'effmaps');
figDir = 'E:\KDH\Overleaf\JEET-2024_rev1\fig';

H = load(fullfile(effDir, 'MotorLAB_elecdata_SC_hyb.mat'));
F = load(fullfile(effDir, 'MotorLAB_elecdata_SC_fullfea.mat'));

chList = {'Stator_Copper_Loss_AC', 'Stator_Copper_Loss_DC', ...
          'Iron_Loss', 'Mechanical_Loss', 'Magnet_Loss', 'Total_Loss'};
lbl    = {'\DeltaP_{Cu,AC}', '\DeltaP_{Cu,DC}', '\DeltaP_{Fe}', ...
          '\DeltaP_{mech}', '\DeltaP_{mag}', '\DeltaP_{total}'};

spd = F.Speed; trq = F.Shaft_Torque;
dEta = H.Efficiency - F.Efficiency;

% 관심 영역: 부호 역전 대역 (speed > 5k, torque < 500 Nm, 유효 OP)
valid = isfinite(dEta) & isfinite(F.Total_Loss) & isfinite(H.Total_Loss);
roi = valid & spd > 5000 & trq < 500 & trq > 0;

fprintf('=== 채널별 Δ(Hybrid − FullFEA) [W] ===\n');
fprintf('%-24s %10s %10s | %12s\n', 'channel', 'mean(all)', 'mean(ROI)', 'max|ROI|');
fig = figure('Units','centimeters','Position',[1 1 26 14], 'Color','w');
tiledlayout(fig, 2, 3, 'Padding','compact', 'TileSpacing','compact');
for k = 1:numel(chList)
    ch = chList{k};
    dP = H.(ch) - F.(ch);
    fprintf('%-24s %10.1f %10.1f | %12.1f\n', ch, ...
        mean(dP(valid),'omitnan'), mean(dP(roi),'omitnan'), ...
        max(abs(dP(roi)),[],'omitnan'));
    ax = nexttile;
    contourf(ax, spd, trq, dP/1e3, 40, 'EdgeColor','none');
    colormap(ax, parula(256));
    cb = colorbar(ax); cb.Label.String = [lbl{k} ' [kW]'];
    xlabel(ax,'Speed [RPM]'); ylabel(ax,'Torque [Nm]');
    title(ax, strrep(ch,'_','\_'), 'FontWeight','normal');
end
exportgraphics(fig, fullfile(figDir, 'effmap_channel_diag.png'), 'Resolution', 200);
fprintf('saved: %s\n', fullfile(figDir, 'effmap_channel_diag.png'));

%% Δη 기여 선형화: dEta_ch ≈ -ΔP_ch * η_F^2 / P_out  (η in frac)
fprintf('\n=== ROI에서 채널별 Δη 기여 [%%p] (선형화) ===\n');
etaF = F.Efficiency/100;
Pout = F.Shaft_Power;
sumC = zeros(size(dEta));
for k = 1:numel(chList)-1   % Total 제외
    ch = chList{k};
    dP = H.(ch) - F.(ch);
    contrib = -dP .* etaF.^2 ./ Pout * 100;
    sumC = sumC + contrib;
    fprintf('%-24s mean(ROI) %+8.3f %%p\n', ch, mean(contrib(roi),'omitnan'));
end
fprintf('%-24s mean(ROI) %+8.3f %%p (실측 Δη %+8.3f)\n', 'SUM(linearized)', ...
    mean(sumC(roi),'omitnan'), mean(dEta(roi),'omitnan'));

%% 전력수지 닫힘 검사 (각 mot)
fprintf('\n=== 전력수지 닫힘: Terminal − TotalLoss − Shaft [W] ===\n');
for tag = {'Hybrid', 'FullFEA'}
    if strcmp(tag{1}, 'Hybrid'), D = H; else, D = F; end
    res1 = D.Terminal_Power - D.Total_Loss - D.Shaft_Power;
    res2 = D.Terminal_Power_Motor - D.Total_Loss_Motor - D.Shaft_Power;
    res3 = D.Electromagnetic_Power - (D.Iron_Loss_Rotor + D.Magnet_Loss + ...
           D.Mechanical_Loss) - D.Shaft_Power;
    fprintf('%-8s  |res1| mean %8.1f max %10.1f  |res2| mean %8.1f  |res3(EM chain)| mean %8.1f\n', ...
        tag{1}, mean(abs(res1(valid)),'omitnan'), max(abs(res1(valid)),[],'omitnan'), ...
        mean(abs(res2(valid)),'omitnan'), mean(abs(res3(valid)),'omitnan'));
end

%% AC 손실 자체의 절대 비교 (기대 방향 확인: FullFEA AC ≫ Hybrid AC 여야 함)
fprintf('\n=== AC 동손 절대값 (ROI 평균) ===\n');
fprintf('Hybrid  Cu_AC: %8.1f W | FullFEA Cu_AC: %8.1f W | ratio H/F: %.3f\n', ...
    mean(H.Stator_Copper_Loss_AC(roi),'omitnan'), ...
    mean(F.Stator_Copper_Loss_AC(roi),'omitnan'), ...
    mean(H.Stator_Copper_Loss_AC(roi),'omitnan')/mean(F.Stator_Copper_Loss_AC(roi),'omitnan'));
fprintf('16k 부근(>14k, T>100) — Hybrid: %8.1f W | FullFEA: %8.1f W\n', ...
    mean(H.Stator_Copper_Loss_AC(valid & spd>14000 & trq>100),'omitnan'), ...
    mean(F.Stator_Copper_Loss_AC(valid & spd>14000 & trq>100),'omitnan'));
