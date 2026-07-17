%% plotFig15Effmaps.m — Fig 15: Lab 효율맵 비교 (SC Hybrid vs FullFEA)
% 패널: (a) Hybrid 기반 효율맵  (b) FullFEA 기반 효율맵
%       (c) |Δη| 오차맵         (d) 효율맵 운전점의 dq 전류쌍 (DQplane 스타일)
% 재사용: tools/effiMap/plotEfficiencyMotorcad.m 의 contourf 스타일
% 입력: run_lab_effmaps_fig15.py 가 수집한 map_exports/e10/effmaps/*.mat

scriptDir = fileparts(mfilename('fullpath'));
eMachRoot = fullfile(scriptDir, '..', '..');
addpath(genpath(fullfile(eMachRoot, 'tools', 'effiMap')));

effDir = fullfile(scriptDir, 'map_exports', 'e10', 'effmaps');
figDir = 'E:\KDH\Overleaf\JEET-2024_rev1\fig';

hybMat  = fullfile(effDir, 'MotorLAB_elecdata_SC_hyb.mat');
fullMat = fullfile(effDir, 'MotorLAB_elecdata_SC_fullfea.mat');
refMat  = fullfile(effDir, 'MotorLAB_elecdata_Ref.mat');
assert(isfile(hybMat) && isfile(fullMat), 'SC elecdata mat 미생성 — run_lab_effmaps_fig15.py 먼저');

H = load(hybMat);  F = load(fullMat);

%% ── 공통 스타일 함수형 설정 ─────────────────────────────────────────
cntrsEff = [80 84 88 90 92:1:98];
effClim  = [80 98];

fig = figure('Units','centimeters','Position',[1 1 24 18], 'Color','w');
tl = tiledlayout(fig, 2, 2, 'Padding','compact', 'TileSpacing','compact');

%% (a) Hybrid 효율맵
ax1 = nexttile;
contourf(ax1, H.Speed, H.Shaft_Torque, H.Efficiency, 60, 'EdgeColor','none');
hold(ax1,'on');
contour(ax1, H.Speed, H.Shaft_Torque, H.Efficiency, cntrsEff, ...
    'EdgeColor','k', 'ShowText','on', 'LineWidth', 0.5);
clim(ax1, effClim); colormap(ax1, jet(256));
xlabel(ax1,'Speed [RPM]'); ylabel(ax1,'Torque [Nm]');
title(ax1,'(a) Hybrid-based efficiency [%]', 'FontWeight','normal');
grid(ax1,'on');

%% (b) FullFEA 효율맵
ax2 = nexttile;
contourf(ax2, F.Speed, F.Shaft_Torque, F.Efficiency, 60, 'EdgeColor','none');
hold(ax2,'on');
contour(ax2, F.Speed, F.Shaft_Torque, F.Efficiency, cntrsEff, ...
    'EdgeColor','k', 'ShowText','on', 'LineWidth', 0.5);
clim(ax2, effClim); colormap(ax2, jet(256));
cb2 = colorbar(ax2); cb2.Label.String = 'Efficiency [%]';
xlabel(ax2,'Speed [RPM]'); ylabel(ax2,'Torque [Nm]');
title(ax2,'(b) TS-FEA(FullFEA)-based efficiency [%]', 'FontWeight','normal');
grid(ax2,'on');

%% (c) 오차맵 Δη
ax3 = nexttile;
dEff = H.Efficiency - F.Efficiency;      % 부호 유지 (Hybrid − FullFEA)
contourf(ax3, F.Speed, F.Shaft_Torque, dEff, 40, 'EdgeColor','none');
hold(ax3,'on');
contour(ax3, F.Speed, F.Shaft_Torque, dEff, [-2:-0.5:-0.5 0.5:0.5:2 0], ...
    'EdgeColor','k', 'ShowText','on', 'LineWidth', 0.5);
colormap(ax3, parula(256));
cb3 = colorbar(ax3); cb3.Label.String = '\Delta\eta = \eta_{hyb} − \eta_{FEA} [%p]';
xlabel(ax3,'Speed [RPM]'); ylabel(ax3,'Torque [Nm]');
title(ax3,'(c) Efficiency error map', 'FontWeight','normal');
grid(ax3,'on');
fprintf('Δη: mean(|.|)=%.3f %%p, max(|.|)=%.3f %%p\n', ...
    mean(abs(dEff(:)),'omitnan'), max(abs(dEff(:)),[],'omitnan'));

%% (d) dq 전류쌍 (DQplane 스타일)
ax4 = nexttile; hold(ax4,'on');
fn = fieldnames(F);
idName = fn(ismember(lower(fn), {'id_peak','id','current_d','id_a'}));
iqName = fn(ismember(lower(fn), {'iq_peak','iq','current_q','iq_a'}));
if isempty(idName)
    disp('사용 가능 필드:'); disp(fn);
    error('elecdata에서 Id/Iq 필드를 못 찾음 — 필드명 확인 필요');
end
Id = F.(idName{1}); Iq = F.(iqName{1});
spdMat = F.Speed;
scatter(ax4, Id(:), Iq(:), 9, spdMat(:), 'o');
cb4 = colorbar(ax4); cb4.Label.String = 'Speed [RPM]';
% 전류 한계원 (920 A rms → peak 변환 여부는 데이터 스케일에 맞춰 자동)
imaxPk = max(hypot(Id(:), Iq(:)), [], 'omitnan');
th = linspace(90, 180, 90);
plot(ax4, imaxPk*cosd(th), imaxPk*sind(th), 'b-', 'LineWidth', 1.2, ...
    'DisplayName', sprintf('I = %.0f A', imaxPk));
axis(ax4, 'equal'); grid(ax4,'on');
xlabel(ax4,'i_d [A]'); ylabel(ax4,'i_q [A]');
title(ax4,'(d) dq current pairs of the map (FullFEA Lab)', 'FontWeight','normal');

%% 저장
outPng = fullfile(figDir, 'effmap_SC_compare.png');
outPdf = fullfile(figDir, 'effmap_SC_compare.pdf');
exportgraphics(fig, outPng, 'Resolution', 220);
exportgraphics(fig, outPdf, 'ContentType', 'vector');
fprintf('saved: %s\n', outPdf);

%% Ref 단독 효율맵 (참고 그림)
if isfile(refMat)
    R = load(refMat);
    figR = figure('Units','centimeters','Position',[2 2 14 10], 'Color','w');
    contourf(R.Speed, R.Shaft_Torque, R.Efficiency, 60, 'EdgeColor','none');
    hold on
    contour(R.Speed, R.Shaft_Torque, R.Efficiency, cntrsEff, ...
        'EdgeColor','k', 'ShowText','on', 'LineWidth', 0.5);
    clim(effClim); colormap(jet(256));
    cb = colorbar; cb.Label.String = 'Efficiency [%]';
    xlabel('Speed [RPM]'); ylabel('Torque [Nm]'); grid on
    title('Ref (k_r=1) Lab efficiency map', 'FontWeight','normal');
    exportgraphics(figR, fullfile(figDir, 'effmap_Ref.png'), 'Resolution', 220);
    fprintf('saved: %s\n', fullfile(figDir, 'effmap_Ref.png'));
end
