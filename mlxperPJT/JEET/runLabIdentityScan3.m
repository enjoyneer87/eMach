%% runLabIdentityScan3.m — 단위(kW/W) 보정 닫힘 + 16k Lab vs Emag 절대 대조
scriptDir = fileparts(mfilename('fullpath'));
effDir = fullfile(scriptDir, 'map_exports', 'e10', 'effmaps');
H = load(fullfile(effDir, 'MotorLAB_elecdata_SC_hyb.mat'));
F = load(fullfile(effDir, 'MotorLAB_elecdata_SC_fullfea.mat'));
D = F;
valid = isfinite(D.Efficiency) & D.Shaft_Torque > 0;

% 가설: Terminal/Shaft/EM Power = kW, 손실 = W
r = 1000*D.Terminal_Power - 1000*D.Shaft_Power - D.Total_Loss;
fprintf('1000*(Term - Shaft) - Total : signed mean %10.1f W, mean|r| %10.1f, max|r| %10.1f\n', ...
    mean(r(valid),'omitnan'), mean(abs(r(valid)),'omitnan'), max(abs(r(valid)),[],'omitnan'));
r2 = 1000*D.Electromagnetic_Power - 1000*D.Shaft_Power - D.Mechanical_Loss;
fprintf('1000*(EM - Shaft) - Mech    : signed mean %10.1f W\n', mean(r2(valid),'omitnan'));

% 스케일 재확인
fprintf('Shaft_Power 범위: %.2f ~ %.2f (kW로 해석 시 %.0f~%.0f kW)\n', ...
    min(D.Shaft_Power(valid)), max(D.Shaft_Power(valid)), min(D.Shaft_Power(valid)), max(D.Shaft_Power(valid)));

%% 16k 열의 최대토크 OP (조건 완화)
[~, c16] = min(abs(D.Speed(1,:) - 16000));
tcol = D.Shaft_Torque(:, c16); tcol(~isfinite(tcol)) = -inf;
[tmax, r16] = max(tcol);
irms = D.Stator_Current_Phase_RMS(r16, c16); ph = D.Phase_Advance(r16, c16);
fprintf('\n=== 16k OP: T=%.1f Nm, Irms=%.1f A, beta=%.1f deg ===\n', tmax, irms, ph);
labH = H.Stator_Copper_Loss_AC(r16, c16); labF = F.Stator_Copper_Loss_AC(r16, c16);
fprintf('Lab Cu_AC: Hybrid %9.1f W | FullFEA %9.1f W (H/F %.3f)\n', labH, labF, labH/labF);

% Emag JSON 16k 최근접
jsonPath = fullfile(scriptDir, 'map_exports', 'e10', 'SC', 'JEET_ACLoss_SC_Map_Summary.json');
raw = jsondecode(fileread(jsonPath));
recs = raw.records; if ~iscell(recs), recs = num2cell(recs); end
bh=NaN; bt=NaN; ch=''; ct=''; dh=inf; dt=inf;
for i = 1:numel(recs)
    p = recs{i};
    if abs(p.speed - 16000) > 1, continue, end
    d = abs(p.current - irms)/50 + abs(p.phase - ph)/10;
    if isfield(p,'proximity_model') && p.proximity_model==1 && isfield(p,'hybrid_total_kW') && d<dh
        dh=d; bh=p.hybrid_total_kW*1e3; ch=sprintf('%.0fA/%.0f°',p.current,p.phase);
    elseif isfield(p,'proximity_model') && p.proximity_model==3 && d<dt
        v=NaN;
        if isfield(p,'ts_ac_active_only_kW') && ~isempty(p.ts_ac_active_only_kW), v=p.ts_ac_active_only_kW*1e3; end
        if ~isnan(v), dt=d; bt=v; ct=sprintf('%.0fA/%.0f°',p.current,p.phase); end
    end
end
fprintf('Emag @16k 최근접: Hybrid %9.1f W @%s | TS %9.1f W @%s | TS/hyb %.2f\n', bh, ch, bt, ct, bt/bh);
fprintf('Lab/Emag 배율: hybLab/hybEmag = %.3f | fullLab/tsEmag = %.3f\n', labH/bh, labF/bt);
