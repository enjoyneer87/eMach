%% plotFig15Effmaps.m — Fig 15: Lab 효율맵 비교 (SC Hybrid vs FullFEA)
% 패널: (a) Hybrid 기반 효율맵  (b) FullFEA 기반 효율맵  (c) |Δη| 오차맵
% (d) dq 전류쌍 패널은 2026-08-21 저자 지시로 삭제 — 3패널 1행 배치로 전환
% 스타일 참고: tools/effiMap/plotEfficiencyMotorcad.m 의 contourf 스타일
%              (코드 의존은 없다 — 전부 MATLAB 내장 함수)
% 입력: run_lab_effmaps_fig15.py 가 수집한 map_exports/e10/effmaps/*.mat

scriptDir = fileparts(mfilename('fullpath'));

% 데이터 루트는 JEET_DATA_ROOT 로 덮어쓸 수 있다 (배포 레포/CI 용).
dataRoot = getenv('JEET_DATA_ROOT');   % 미설정이면 '' 를 돌려준다
if isempty(dataRoot)
    dataRoot = fullfile(scriptDir, 'map_exports', 'e10');
end
% 출력 폴더는 JEET_FIGDIR 로 덮어쓸 수 있다 (배포 레포/CI 용).
figDir = getenv('JEET_FIGDIR');
if isempty(figDir)
    figDir = 'E:\KDH\Overleaf\JEET-2024_rev1\fig';
end
if ~isfolder(figDir), mkdir(figDir); end

effDir = fullfile(dataRoot, 'effmaps');

hybMat  = fullfile(effDir, 'MotorLAB_elecdata_SC_hyb.mat');
fullMat = fullfile(effDir, 'MotorLAB_elecdata_SC_fullfea.mat');
refMat  = fullfile(effDir, 'MotorLAB_elecdata_Ref.mat');
assert(isfile(hybMat) && isfile(fullMat), 'SC elecdata mat 미생성 — run_lab_effmaps_fig15.py 먼저');

H = load(hybMat);  F = load(fullMat);

%% ── 공통 스타일 함수형 설정 ─────────────────────────────────────────
cntrsEff = [80 84 88 90 92:1:98];
cntrsLbl = [92 94 97];   % 라벨은 성기게 --- 92~98 이 1%p 간격이라 전부 붙이면 좌측 코너에서 뭉친다
effClim  = [80 98];

% 인쇄 크기(2단 전폭 ~17.5 cm)에 맞춰 물리 크기를 잡고 폰트를 명시한다.
% 컬러바는 eastoutside — 전폭에서 하단 바는 세로를 과하게 먹는다.
% 24 cm 도판을 0.30배로 축소하던 종전 설정에서는 축 글자가 ~3 pt로 찍혔다.
FS = 7.7;   % 축/눈금 글자 [pt] — 전폭 캔버스(17.5 cm) = 인쇄 크기 -> 축소 ~1.0, 지면 7.7 pt 그대로
% 등고선 라벨: 전폭에서는 겹치지 않으므로 표시(저자 확인 2026-08-02).
fig = figure('Units','centimeters','Position',[1 1 17.5 5.9], 'Color','w');
set(fig,'DefaultAxesFontSize',FS, 'DefaultTextFontSize',FS, ...
        'DefaultAxesFontName','Times New Roman', ...
        'DefaultTextFontName','Times New Roman');
tl = tiledlayout(fig, 1, 3, 'Padding','compact', 'TileSpacing','compact');

%% (a) Hybrid 효율맵
ax1 = nexttile;
contourf(ax1, H.Speed, H.Shaft_Torque, H.Efficiency, 60, 'EdgeColor','none');
hold(ax1,'on');
[Cc, hc] = contour(ax1, H.Speed, H.Shaft_Torque, H.Efficiency, cntrsEff, ...
    'EdgeColor','k', 'LineWidth', 0.5);
clabel(Cc, hc, cntrsLbl, 'FontSize', FS-1.2, 'LabelSpacing', 400);
clim(ax1, effClim); colormap(ax1, jet(256));
xlabel(ax1,'Speed [RPM]'); ylabel(ax1,'Torque [Nm]');
title(ax1,'(a)', 'FontWeight','normal');
grid(ax1,'on');

%% (b) FullFEA 효율맵
ax2 = nexttile;
contourf(ax2, F.Speed, F.Shaft_Torque, F.Efficiency, 60, 'EdgeColor','none');
hold(ax2,'on');
[Cc, hc] = contour(ax2, F.Speed, F.Shaft_Torque, F.Efficiency, cntrsEff, ...
    'EdgeColor','k', 'LineWidth', 0.5);
clabel(Cc, hc, cntrsLbl, 'FontSize', FS-1.2, 'LabelSpacing', 400);
clim(ax2, effClim); colormap(ax2, jet(256));
cb2 = colorbar(ax2, 'Location','eastoutside'); cb2.Label.String = 'Efficiency [%]';
cb2.FontSize = FS; cb2.Label.FontSize = FS;
xlabel(ax2,'Speed [RPM]'); ylabel(ax2,'Torque [Nm]');
title(ax2,'(b)', 'FontWeight','normal');
grid(ax2,'on');

%% (c) 오차맵 Δη
ax3 = nexttile;
dEff = H.Efficiency - F.Efficiency;      % 부호 유지 (Hybrid − FullFEA)
contourf(ax3, F.Speed, F.Shaft_Torque, dEff, 40, 'EdgeColor','none');
hold(ax3,'on');
contour(ax3, F.Speed, F.Shaft_Torque, dEff, [-2:-0.5:-0.5 0.5:0.5:2 0], ...
    'EdgeColor','k', 'ShowText','on', 'LineWidth', 0.5);
colormap(ax3, parula(256));
cb3 = colorbar(ax3, 'Location','eastoutside');
cb3.Label.String = '\Delta\eta [%p]';
cb3.FontSize = FS; cb3.Label.FontSize = FS;
xlabel(ax3,'Speed [RPM]'); ylabel(ax3,'Torque [Nm]');
title(ax3,'(c)', 'FontWeight','normal');
grid(ax3,'on');
fprintf('CAPTION Δη range: %.2f to %.2f %%p | speed %.0f to %.0f RPM\n', min(dEff(:),[],'omitnan'), max(dEff(:),[],'omitnan'), min(F.Speed(:),[],'omitnan'), max(F.Speed(:),[],'omitnan'));
fprintf('Δη: mean(|.|)=%.3f %%p, max(|.|)=%.3f %%p\n', ...
    mean(abs(dEff(:)),'omitnan'), max(abs(dEff(:)),[],'omitnan'));

% (d) dq 전류쌍 패널은 삭제했다 (저자 지시 2026-08-21). 운전 궤적이 보정
% 학습 영역 안에 있다는 근거는 Fig 4(AF 맵의 전류원)가 그대로 담고 있다.

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
