%% [0] 경로 설정
fprintf('\n%s\n', repmat('=',1,62));
fprintf(' milestone_check.m — JEET 마일스톤 검증 대시보드\n');
fprintf('%s\n\n', repmat('=',1,62));
fprintf('[0] 경로 설정\n');

SCRIPT_DIR  = fileparts(mfilename('fullpath'));
EMACH_ROOT  = fileparts(fileparts(SCRIPT_DIR));

addpath(genpath(EMACH_ROOT));
fprintf('  eMach 루트  : %s\n', EMACH_ROOT);

% 결과 파일 경로
RES_PHASE   = fullfile(SCRIPT_DIR, 'verify_phase_angle_results.mat');
RES_EFF     = fullfile(SCRIPT_DIR, 'efficiency_map_results.mat');
RES_PAPER   = fullfile(SCRIPT_DIR, 'paper_results.mat');
RES_SYRE_B  = fullfile(SCRIPT_DIR, 'map_exports', 'e10', 'Ref', ...
                       'e10_SyreMMM.mat');

fprintf('  [1] β_opt   : %s\n', RES_PHASE);
fprintf('  [2] 효율맵   : %s\n', RES_EFF);
fprintf('  [3] Scaling  : %s\n', RES_PAPER);
fprintf('  [4] MCAD→SyRE: %s\n', RES_SYRE_B);


%% [1] β_opt 검증 (Task 1)
fprintf('\n%s\n[1] β_opt 검증\n%s\n', repmat('-',1,50), repmat('-',1,50));

if ~isfile(RES_PHASE)
    warning('milestone:noFile', '[1] 파일 없음: %s — 스킵', RES_PHASE);
else
    d1 = load(RES_PHASE, 'beta_ref', 'beta_sc', 'beta_halfsc', ...
              'speed_rpm', 'torque_nm');

    spd_vec = d1.speed_rpm(:)';          % [1 × nS]
    trq_vec = d1.torque_nm(:)';          % [1 × nT]
    nS = numel(spd_vec);
    nT = numel(trq_vec);

    beta_ref = reshape(d1.beta_ref, nT, nS);
    beta_sc  = reshape(d1.beta_sc,  nT, nS);
    delta_b  = beta_sc - beta_ref;

    fprintf('  속도 [rpm]  : %s\n', num2str(spd_vec, '%g '));
    fprintf('  토크 [Nm]   : %s\n', num2str(trq_vec, '%g '));
    fprintf('  Δβ (SC−Ref) 범위: %.2f° ~ %.2f°\n', ...
            min(delta_b(:)), max(delta_b(:)));

    figure('Name','[1] β_opt 검증','NumberTitle','off','Color','w');

    % subplot(1,3,1) — Ref β_opt
    subplot(1,3,1);
    contourf(spd_vec, trq_vec, beta_ref, 12, 'LineColor','none');
    colormap(gca, parula);
    colorbar; clim([min(beta_ref(:)) max(beta_ref(:))]);
    xlabel('Speed [rpm]'); ylabel('Torque [Nm]');
    title('Ref  β_{opt} [°]');
    set(gca,'FontSize',9);

    % subplot(1,3,2) — SC β_opt
    subplot(1,3,2);
    contourf(spd_vec, trq_vec, beta_sc, 12, 'LineColor','none');
    colormap(gca, parula);
    colorbar; clim([min(beta_ref(:)) max(beta_ref(:))]);
    xlabel('Speed [rpm]'); ylabel('Torque [Nm]');
    title('SC  β_{opt} [°]');
    set(gca,'FontSize',9);

    % subplot(1,3,3) — Δβ = SC − Ref
    subplot(1,3,3);
    contourf(spd_vec, trq_vec, delta_b, 12, 'LineColor','none');
    colormap(gca, bwr_colormap_(64));
    cax = max(abs(delta_b(:)));
    if cax < 1e-6, cax = 1; end
    clim([-cax cax]);
    colorbar;
    xlabel('Speed [rpm]'); ylabel('Torque [Nm]');
    title('Δβ = SC − Ref [°]');
    set(gca,'FontSize',9);

    sgtitle('[1] 최적 전류위상각 β_{opt} 비교', 'FontWeight','bold');
    fprintf('  [OK] β_opt 플롯 완료.\n');
end


%% [2] 효율맵 검증 (Task 2 - 파일 없으면 스킵)
fprintf('\n%s\n[2] 효율맵 검증\n%s\n', repmat('-',1,50), repmat('-',1,50));

if ~isfile(RES_EFF)
    warning('milestone:noFile', '[2] 파일 없음: %s — 스킵', RES_EFF);
else
    d2 = load(RES_EFF);

    % 공통 필드 확인
    req_fld = {'eta_pct','speed_rpm','torque_nm'};
    missing = req_fld(~isfield(d2, req_fld));
    if ~isempty(missing)
        warning('milestone:noField', '[2] 누락 필드: %s — 스킵', strjoin(missing,', '));
    else
        spd2 = d2.speed_rpm(:)';
        trq2 = d2.torque_nm(:)';
        eta  = d2.eta_pct;

        figure('Name','[2] 효율맵 검증','NumberTitle','off','Color','w');

        % η 등고선맵
        subplot(2,2,1);
        [C,h] = contourf(spd2, trq2, eta, 20, 'LineColor','none');
        clabel(C, h, 'FontSize',7, 'Color','k');
        colormap(gca, hot);
        colorbar; clim([min(eta(:)) 100]);
        xlabel('Speed [rpm]'); ylabel('Torque [Nm]');
        title('η [%]'); set(gca,'FontSize',9);

        % 손실 분해 (있는 필드만)
        lossNames = {'loss_cu_dc_kW','loss_cu_ac_kW','loss_fe_kW'};
        lossTitles = {'P_{Cu,DC} [kW]','P_{Cu,AC} [kW]','P_{Fe} [kW]'};
        cmaps = {cool, autumn, winter};
        for k = 1:3
            if isfield(d2, lossNames{k})
                subplot(2,2,k+1);
                contourf(spd2, trq2, d2.(lossNames{k}), 12, 'LineColor','none');
                colormap(gca, cmaps{k});
                colorbar;
                xlabel('Speed [rpm]'); ylabel('Torque [Nm]');
                title(lossTitles{k}); set(gca,'FontSize',9);
            end
        end

        sgtitle('[2] 효율맵 및 손실 분해', 'FontWeight','bold');
        fprintf('  [OK] 효율맵 플롯 완료. η_peak = %.2f%%\n', max(eta(:)));
    end
end


%% [3] Scaling 검증 (Task 3 - 파일 없으면 스킵)
fprintf('\n%s\n[3] Scaling 검증\n%s\n', repmat('-',1,50), repmat('-',1,50));

if ~isfile(RES_PAPER)
    warning('milestone:noFile', '[3] 파일 없음: %s — 스킵', RES_PAPER);
else
    d3 = load(RES_PAPER);

    % 기대 필드: cases(k).k_r, k_a, label, eta_pct, speed_rpm, torque_nm
    if ~isfield(d3, 'cases')
        warning('milestone:noField', '[3] ''cases'' 필드 없음 — 스킵');
    else
        nCase = numel(d3.cases);
        fprintf('  케이스 수 : %d\n', nCase);

        figure('Name','[3] Scaling 검증','NumberTitle','off','Color','w');
        cmap_s = lines(nCase);

        for k = 1:nCase
            c = d3.cases(k);
            spd3 = c.speed_rpm(:)';
            trq3 = c.torque_nm(:)';

            subplot(1, nCase, k);
            contourf(spd3, trq3, c.eta_pct, 15, 'LineColor','none');
            colormap(gca, parula); colorbar; %#ok<NASGU>
            xlabel('Speed [rpm]'); ylabel('Torque [Nm]');
            lbl = '';
            if isfield(c,'label'),  lbl = c.label;  end
            if isfield(c,'k_r') && isfield(c,'k_a')
                lbl = sprintf('%s  (k_r=%.2f, k_a=%.2f)', lbl, c.k_r, c.k_a);
            end
            title(sprintf('η [%%] — %s', strtrim(lbl)));
            set(gca,'FontSize',8);
            fprintf('  케이스 %d: %s  η_peak=%.2f%%\n', k, strtrim(lbl), max(c.eta_pct(:)));
        end

        sgtitle('[3] 스케일링 케이스별 효율맵 비교', 'FontWeight','bold');
        fprintf('  [OK] Scaling 플롯 완료.\n');
    end
end


%% [4] MCAD→SyRE 연동 검증
fprintf('\n%s\n[4] MCAD→SyRE 연동 검증\n%s\n', repmat('-',1,50), repmat('-',1,50));

% 후보 경로 순서대로 시도
candidates = {
    RES_SYRE_B, ...
    fullfile(SCRIPT_DIR, 'map_exports', 'e10', 'Ref', 'JEET_SyreMMM.mat'), ...
    fullfile(EMACH_ROOT, 'mlxperPJT', 'JEET', 'test_syre_out.mat'), ...
};

mat4_path = '';
for k = 1:numel(candidates)
    if isfile(candidates{k})
        mat4_path = candidates{k};
        break;
    end
end

if isempty(mat4_path)
    warning('milestone:noFile', '[4] FluxMap_dq .mat 파일을 찾을 수 없음 — 스킵\n  탐색 경로:\n%s', ...
            strjoin(candidates, '\n  '));
else
    fprintf('  로드: %s\n', mat4_path);
    d4 = load(mat4_path);

    % FluxMap_dq 구조 체크
    if ~isfield(d4, 'FluxMap_dq')
        warning('milestone:noField', '[4] FluxMap_dq 필드 없음 — 스킵');
    else
        fm = d4.FluxMap_dq;
        req4 = {'Id','Iq','Fd','Fq','T'};
        miss4 = req4(~isfield(fm, req4));

        if ~isempty(miss4)
            warning('milestone:noField', '[4] FluxMap_dq 누락 필드: %s', strjoin(miss4,', '));
        else
            fprintf('  FluxMap_dq 필드 확인: Id Iq Fd Fq T — OK\n');
            fprintf('  Id 범위  : [%.2f, %.2f] A (RMS)\n', min(fm.Id(:)), max(fm.Id(:)));
            fprintf('  Iq 범위  : [%.2f, %.2f] A (RMS)\n', min(fm.Iq(:)), max(fm.Iq(:)));
            fprintf('  Fd 범위  : [%.4f, %.4f] Wb\n',      min(fm.Fd(:)), max(fm.Fd(:)));
            fprintf('  Fq 범위  : [%.4f, %.4f] Wb\n',      min(fm.Fq(:)), max(fm.Fq(:)));
            fprintf('  T  범위  : [%.1f, %.1f] Nm\n',      min(fm.T(:)),  max(fm.T(:)));

            Id_ax = fm.Id(1,:);   % Id 축 벡터 (행)
            Iq_ax = fm.Iq(:,1)';  % Iq 축 벡터 (열→행)

            figure('Name','[4] MCAD→SyRE FluxMap_dq','NumberTitle','off','Color','w');

            subplot(1,3,1);
            contourf(Id_ax, Iq_ax, fm.Fd, 15, 'LineColor','none');
            colormap(gca, parula); colorbar;
            xlabel('I_d [A_{rms}]'); ylabel('I_q [A_{rms}]');
            title('F_d [Wb]'); set(gca,'FontSize',9);

            subplot(1,3,2);
            contourf(Id_ax, Iq_ax, fm.Fq, 15, 'LineColor','none');
            colormap(gca, parula); colorbar;
            xlabel('I_d [A_{rms}]'); ylabel('I_q [A_{rms}]');
            title('F_q [Wb]'); set(gca,'FontSize',9);

            subplot(1,3,3);
            contourf(Id_ax, Iq_ax, fm.T, 15, 'LineColor','none');
            colormap(gca, cool); colorbar;
            xlabel('I_d [A_{rms}]'); ylabel('I_q [A_{rms}]');
            title('T [Nm]'); set(gca,'FontSize',9);

            sgtitle('[4] MCAD→SyRE FluxMap\_dq 검증', 'FontWeight','bold');

            % IronPMLossMap_dq 체크
            if isfield(d4, 'IronPMLossMap_dq')
                irn = d4.IronPMLossMap_dq;
                fprintf('  IronPMLossMap_dq: n0=%g rpm, f0=%g Hz\n', ...
                    irn.n0, irn.f0);
            else
                fprintf('  IronPMLossMap_dq: 없음 (Lab 철손 FEA 미계산 또는 미저장)\n');
            end
            fprintf('  [OK] FluxMap_dq 시각화 완료.\n');
        end
    end
end

fprintf('\n%s\n milestone_check 완료\n%s\n', repmat('=',1,62), repmat('=',1,62));


% ─────────────────────────────────────────────────────────────────────────────
% Blue-White-Red 컬러맵 (발산형, Δ 플롯용)
% ─────────────────────────────────────────────────────────────────────────────
function cmap = bwr_colormap_(n)
if nargin < 1, n = 64; end
half = floor(n/2);
r    = [linspace(0,1,half); ones(1, n-half)];
g    = [linspace(0,1,half); linspace(1,0, n-half)];
b    = [ones(1,half);       linspace(1,0, n-half)];
cmap = [r', g', b'];
end
