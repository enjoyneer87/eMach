%% runLabIdentityScan2.m — 후속: Terminal 정의·η 정의·EM토크 스케일 확정 + OP 대조 재시도
scriptDir = fileparts(mfilename('fullpath'));
effDir = fullfile(scriptDir, 'map_exports', 'e10', 'effmaps');
H = load(fullfile(effDir, 'MotorLAB_elecdata_SC_hyb.mat'));
F = load(fullfile(effDir, 'MotorLAB_elecdata_SC_fullfea.mat'));
D = F;
valid = isfinite(D.Efficiency) & D.Shaft_Torque > 0;

fprintf('=== Terminal 정의 후보 ===\n');
r_a = D.Terminal_Power - (D.Total_Loss - D.Stator_Copper_Loss) - D.Shaft_Power;
r_b = D.Terminal_Power - D.Electromagnetic_Power;
r_c = D.Terminal_Power - (D.Electromagnetic_Power + D.Iron_Loss_Stator);
fprintf('Term - (Total-CuTot) - Shaft : mean|r| %10.1f\n', mean(abs(r_a(valid)),'omitnan'));
fprintf('Term - EMpower               : mean|r| %10.1f\n', mean(abs(r_b(valid)),'omitnan'));
fprintf('Term - (EMpower+FeStator)    : mean|r| %10.1f\n', mean(abs(r_c(valid)),'omitnan'));

fprintf('\n=== 3상 스케일 가설: Terminal*3 ===\n');
r_d = 3*D.Terminal_Power - D.Total_Loss - D.Shaft_Power;
fprintf('3*Term - Total - Shaft       : mean|r| %10.1f\n', mean(abs(r_d(valid)),'omitnan'));

fprintf('\n=== 효율 정의 확인 ===\n');
eta1 = 100 * D.Shaft_Power ./ (D.Shaft_Power + D.Total_Loss);
eta2 = 100 * D.Shaft_Power ./ D.Terminal_Power;
eta3 = 100 * D.Shaft_Power ./ (3*D.Terminal_Power);
fprintf('|Eff - Shaft/(Shaft+Total)|  : mean %8.3f  max %8.3f\n', ...
    mean(abs(D.Efficiency(valid)-eta1(valid)),'omitnan'), max(abs(D.Efficiency(valid)-eta1(valid)),[],'omitnan'));
fprintf('|Eff - Shaft/Term|           : mean %8.3f\n', mean(abs(D.Efficiency(valid)-eta2(valid)),'omitnan'));
fprintf('|Eff - Shaft/(3Term)|        : mean %8.3f\n', mean(abs(D.Efficiency(valid)-eta3(valid)),'omitnan'));

fprintf('\n=== EM 토크 스케일 ===\n');
ratio = (D.Electromagnetic_Torque .* (D.Speed*2*pi/60)) ./ D.Electromagnetic_Power;
fprintf('EMtorque*w_mech / EMpower    : mean %8.3f (1=정합, 8=섹터?)\n', mean(ratio(valid),'omitnan'));

%% 고속 최대토크 OP 대조 (speed >= 14k, T > 100)
mask = valid & D.Speed >= 14000 & D.Shaft_Torque > 100;
if ~any(mask(:)), mask = valid & D.Speed >= 12000 & D.Shaft_Torque > 100; end
tv = D.Shaft_Torque; tv(~mask) = -inf;
[~, idx] = max(tv(:)); [rr, cc] = ind2sub(size(tv), idx);
spdOP = D.Speed(rr,cc); trqOP = D.Shaft_Torque(rr,cc);
irmsOP = D.Stator_Current_Phase_RMS(rr,cc); phOP = D.Phase_Advance(rr,cc);
fprintf('\n=== 고속 OP: %d rpm, T=%.0f Nm, Irms=%.1f A, beta=%.1f deg ===\n', spdOP, trqOP, irmsOP, phOP);
fprintf('Lab Cu_AC: Hybrid %8.1f W | FullFEA %8.1f W  (H/F %.3f)\n', ...
    H.Stator_Copper_Loss_AC(rr,cc), F.Stator_Copper_Loss_AC(rr,cc), ...
    H.Stator_Copper_Loss_AC(rr,cc)/F.Stator_Copper_Loss_AC(rr,cc));

jsonPath = fullfile(scriptDir, 'map_exports', 'e10', 'SC', 'JEET_ACLoss_SC_Map_Summary.json');
raw = jsondecode(fileread(jsonPath));
recs = raw.records; if ~iscell(recs), recs = num2cell(recs); end
bh = NaN; bt = NaN; ch = ''; ct = ''; dh = inf; dt = inf;
for i = 1:numel(recs)
    p = recs{i};
    if abs(p.speed - spdOP) > 1, continue, end
    d = abs(p.current - irmsOP)/50 + abs(p.phase - phOP)/10;
    if isfield(p,'proximity_model') && p.proximity_model==1 && isfield(p,'hybrid_total_kW') && d<dh
        dh=d; bh=p.hybrid_total_kW*1e3; ch=sprintf('%.0fA/%.0fdeg',p.current,p.phase);
    elseif isfield(p,'proximity_model') && p.proximity_model==3 && d<dt
        v = NaN;
        if isfield(p,'ts_ac_active_only_kW') && ~isempty(p.ts_ac_active_only_kW), v=p.ts_ac_active_only_kW*1e3; end
        if ~isnan(v), dt=d; bt=v; ct=sprintf('%.0fA/%.0fdeg',p.current,p.phase); end
    end
end
fprintf('Emag 최근접: Hybrid %8.1f W @%s | TS %8.1f W @%s | TS/hyb %.2f\n', bh, ch, bt, ct, bt/bh);
fprintf('Lab/Emag: hyb %.3f | full/TS %.3f\n', H.Stator_Copper_Loss_AC(rr,cc)/bh, F.Stator_Copper_Loss_AC(rr,cc)/bt);
