%% runLabIdentityScan.m — Lab elecdata 전력수지 항등식 스캔 + Emag 대조
% (1) 어떤 전력 항등식이 닫히는지 후보 조합을 전수 검사해 Lab 북키핑 규명
% (2) 16k 최대토크 부근 OP에서 Lab Cu_AC를 Emag JSON(hybrid/TS)과 직접 대조

scriptDir = fileparts(mfilename('fullpath'));
effDir = fullfile(scriptDir, 'map_exports', 'e10', 'effmaps');
H = load(fullfile(effDir, 'MotorLAB_elecdata_SC_hyb.mat'));
F = load(fullfile(effDir, 'MotorLAB_elecdata_SC_fullfea.mat'));

valid = isfinite(F.Efficiency) & F.Shaft_Torque > 0;

%% (1) 항등식 후보 스캔 (FullFEA mot 기준)
D = F;
cand = { ...
 'Term - Total - Shaft',            D.Terminal_Power - D.Total_Loss - D.Shaft_Power; ...
 'Term - Total_Motor - Shaft',      D.Terminal_Power - D.Total_Loss_Motor - D.Shaft_Power; ...
 'Term - (Total-ExtLine) - Shaft',  D.Terminal_Power - (D.Total_Loss - D.External_Line_Loss) - D.Shaft_Power; ...
 'Term - Total - EMpower',          D.Terminal_Power - D.Total_Loss - D.Electromagnetic_Power; ...
 'EM - Mech - Shaft',               D.Electromagnetic_Power - D.Mechanical_Loss - D.Shaft_Power; ...
 'EM - Mech - RotorFe - Mag - Shaft', D.Electromagnetic_Power - D.Mechanical_Loss - D.Iron_Loss_Rotor - D.Magnet_Loss - D.Shaft_Power; ...
 'Term - CuTot - FeTot - Mag - Mech - Shaft', D.Terminal_Power - D.Stator_Copper_Loss - D.Iron_Loss - D.Magnet_Loss - D.Mechanical_Loss - D.Shaft_Power; ...
 'Term - Cu(AC+DC) - FeTot - Mag - Mech - Shaft', D.Terminal_Power - (D.Stator_Copper_Loss_AC + D.Stator_Copper_Loss_DC) - D.Iron_Loss - D.Magnet_Loss - D.Mechanical_Loss - D.Shaft_Power; ...
 'EMtorque*w - Shaft - Mech',       D.Electromagnetic_Torque .* (D.Speed*2*pi/60) - D.Shaft_Power - D.Mechanical_Loss; ...
 'Cu_Tot - (AC+DC)',                D.Stator_Copper_Loss - (D.Stator_Copper_Loss_AC + D.Stator_Copper_Loss_DC); ...
 'Total - (CuTot+Fe+Mag+Mech+Ext)', D.Total_Loss - (D.Stator_Copper_Loss + D.Iron_Loss + D.Magnet_Loss + D.Mechanical_Loss + D.External_Line_Loss); ...
};
fprintf('=== 항등식 잔차 (FullFEA mot, 유효 OP) [W] ===\n');
for k = 1:size(cand,1)
    r = cand{k,2};
    fprintf('%-46s mean|r| %10.1f   max|r| %12.1f\n', cand{k,1}, ...
        mean(abs(r(valid)),'omitnan'), max(abs(r(valid)),[],'omitnan'));
end

%% (2) Emag 정답 대조: 16k, 최대토크 열 부근 OP
% Lab 맵에서 speed=16000 열의 최대 토크 OP → (Irms, phase) 읽기
[~, col16] = min(abs(F.Speed(1,:) - 16000));
tcol = F.Shaft_Torque(:, col16);
[tmax, rmax] = max(tcol);
irms16 = F.Stator_Current_Phase_RMS(rmax, col16);
phase16 = F.Phase_Advance(rmax, col16);
fprintf('\n=== 16k 최대토크 OP: T=%.0f Nm, Irms=%.1f A, beta=%.1f deg ===\n', tmax, irms16, phase16);
fprintf('Lab Cu_AC  @16k-maxT: Hybrid %8.1f W | FullFEA %8.1f W\n', ...
    H.Stator_Copper_Loss_AC(rmax, col16), F.Stator_Copper_Loss_AC(rmax, col16));
fprintf('Lab Cu_DC  @16k-maxT: Hybrid %8.1f W | FullFEA %8.1f W\n', ...
    H.Stator_Copper_Loss_DC(rmax, col16), F.Stator_Copper_Loss_DC(rmax, col16));

% Emag JSON (우리 스윕 데이터) 최근접 조건
jsonPath = fullfile(scriptDir, 'map_exports', 'e10', 'SC', 'JEET_ACLoss_SC_Map_Summary.json');
raw = jsondecode(fileread(jsonPath));
recs = raw.records; if ~iscell(recs), recs = num2cell(recs); end
best = struct('dh', inf, 'dt', inf, 'hyb', NaN, 'ts', NaN, 'chyb', '', 'cts', '');
for i = 1:numel(recs)
    p = recs{i};
    if abs(p.speed - 16000) > 1, continue, end
    d = abs(p.current - irms16) + 2*abs(p.phase - phase16);
    if isfield(p,'proximity_model') && p.proximity_model == 1 && isfield(p,'hybrid_total_kW') && d < best.dh
        best.dh = d; best.hyb = p.hybrid_total_kW*1e3;
        best.chyb = sprintf('%.0fA/%.0fdeg', p.current, p.phase);
    elseif isfield(p,'proximity_model') && p.proximity_model == 3 && d < best.dt
        if isfield(p,'ts_ac_active_only_kW') && ~isempty(p.ts_ac_active_only_kW)
            best.dt = d; best.ts = p.ts_ac_active_only_kW*1e3;
            best.cts = sprintf('%.0fA/%.0fdeg', p.current, p.phase);
        end
    end
end
fprintf('Emag 최근접 — Hybrid(액티브 AC) %8.1f W @%s | TS(액티브 AC) %8.1f W @%s\n', ...
    best.hyb, best.chyb, best.ts, best.cts);
fprintf('비율: Lab_hyb/Emag_hyb = %.3f | Lab_full/Emag_TS = %.3f | Emag TS/hyb = %.2f\n', ...
    H.Stator_Copper_Loss_AC(rmax,col16)/best.hyb, ...
    F.Stator_Copper_Loss_AC(rmax,col16)/best.ts, best.ts/best.hyb);
