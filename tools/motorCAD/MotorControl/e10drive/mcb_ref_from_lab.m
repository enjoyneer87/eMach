function out = mcb_ref_from_lab(workDir)
%MCB_REF_FROM_LAB  Motor-CAD Lab 자속맵을 Motor Control Blockset 에 넣어 기준표를 생성한다.
%
%   mcb.generateMotorLUT(pmsm, inverter, 'idiqLUTs', ...) 는 MTPA + 약자속을 MCB 규약대로 풀어
%   id(T, w), iq(T, w) 를 만든다. pmsm.PMSMLUT.method = 'FluxDQ' 로 두면 우리 Lab 맵
%   (λd, λq, 토크)을 그대로 쓴다 — 손으로 짠 기준표 대신 검증된 구현을 쓰는 길이다.
%
%   검증: 16 krpm 에서 (a) MCB 기준표, (b) PC1 이 만든 기준표, (c) Lab 자체 운전점 궤적을 맞댄다.

if nargin < 1 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
P = load(fullfile(workDir, 'e10_plant_lab.mat'));
S = load(fullfile(workDir, 'e10_stage1_data_16000.mat'));
m = P.machine;

% ---- MCB 규약의 pmsm 구조체
pmsm = struct('model', 'e10', 'sn', '001', 'p', m.p, 'Rs', m.Rs_80C, ...
              'Ld', 0.85e-3, 'Lq', 1.6e-3, 'J', 0.05, 'B', 1e-3, ...
              'FluxPM', P.lambda_m, 'I_rated', m.I_rated_rms*sqrt(2), ...
              'N_max', m.n_rated, 'PositionOffset', 0, 'QEPSlits', 1024);
pmsm.Ke = pmsm.FluxPM*sqrt(3)*2*pi*1000*pmsm.p/60;
pmsm.Kt = 1.5*pmsm.p*pmsm.FluxPM;
pmsm.T_rated = mcb.PMSMRatedTorque(pmsm);

% ---- 자속맵을 MCB 격자로: id 는 음수만, iq 는 대칭으로 펼친다
%      (λd 는 iq 에 대해 우함수, λq·토크는 기함수 — 한 사분면 맵을 그렇게 확장한다)
idV = P.id_pk;                       % -650 ... 0
iqPos = P.iq_pk;                     % 0 ... 650
iqV = [-fliplr(iqPos(2:end)), iqPos];
nId = numel(idV);  nIq = numel(iqV);
Fd = zeros(nId, nIq);  Fq = Fd;  Tq = Fd;
for a = 1:nId
    for b = 1:nIq
        iq = iqV(b);  sgn = sign(iq + eps);
        Fd(a, b) = interp2(P.id_pk, P.iq_pk, P.Fd, idV(a), abs(iq), 'linear');
        Fq(a, b) = sgn*interp2(P.id_pk, P.iq_pk, P.Fq, idV(a), abs(iq), 'linear');
        Tq(a, b) = sgn*interp2(P.id_pk, P.iq_pk, P.T,  idV(a), abs(iq), 'linear');
    end
end

pmsm.PMSMLUT = struct('method', 'FluxDQ', 'idVec', idV, 'iqVec', iqV, ...
                      'FluxDTable', Fd, 'FluxQTable', Fq, 'TorqueTable', Tq, ...
                      'trefVec', linspace(0, 0.9*max(Tq(:)), 25), ...
                      'wrpmVec', [0 2000 4000 8000 12000 16000]);

inv = mcb.getInverterParameters('BoostXL-DRV8305');
inv.V_dc = m.Vdc;  inv.I_max = pmsm.I_rated;  inv.ISenseMax = pmsm.I_rated;  inv.R_board = 0;

fprintf('MCB 기준표 생성: 토크 %d점 x 속도 %d점, 자속맵 %dx%d\n', ...
        numel(pmsm.PMSMLUT.trefVec), numel(pmsm.PMSMLUT.wrpmVec), nId, nIq);
LUT = mcb.generateMotorLUT(pmsm, inv, 'idiqLUTs', drawLUT = 0, useTorquePercent = 0);
out.LUT = LUT;  out.pmsm = pmsm;  out.inverter = inv;
disp('반환 필드:'); disp(fieldnames(LUT)');

% ---- 삼자 대조 (16 krpm)
L = readtable('D:\KangDH\Thesis\e10\work_lab_pc1\existing\lab_points_16k.csv');
idL = LUT.(pickField(LUT, 'id'));  iqL = LUT.(pickField(LUT, 'iq'));
tv = LUT.(pickField(LUT, 'tref'));  wv = LUT.(pickField(LUT, 'wrpm'));
fprintf('\n%8s | %8s %8s %8s | %8s %8s %8s\n', 'T [N·m]', ...
        'γ_MCB', 'γ_PC1', 'γ_Lab', 'I_MCB', 'I_PC1', 'I_Lab');
for T = [5 20 40 60 80]
    [idm, iqm] = lutAt(idL, iqL, tv, wv, T, 16000);
    gm = atan2d(-idm, iqm);  Im = hypot(idm, iqm)/sqrt(2);
    gp = interp1(S.T_ref_vec, S.gamma_ref_current, T);
    Ip = interp1(S.T_ref_vec, S.I_ref_current, T);
    [~, j] = min(abs(L.T - T));
    if abs(L.T(j) - T) < max(0.15*T, 0.5), gl = L.gamma(j); Il = L.Irms(j); else, gl = NaN; Il = NaN; end
    fprintf('%8.1f | %8.2f %8.2f %8.2f | %8.1f %8.1f %8.1f\n', T, gm, gp, gl, Im, Ip, Il);
end
end

function f = pickField(LUT, key)
fn = fieldnames(LUT);
hit = fn(contains(lower(fn), lower(key)));
assert(~isempty(hit), '필드 없음: %s (있는 것: %s)', key, strjoin(fn', ', '));
f = hit{1};
end

function [id, iq] = lutAt(idL, iqL, tv, wv, T, w)
id = interp2(wv, tv, idL, w, T, 'linear');
iq = interp2(wv, tv, iqL, w, T, 'linear');
if ~isfinite(id)      % 표가 (w, T) 순서일 수도 있다
    id = interp2(tv, wv, idL, T, w, 'linear');
    iq = interp2(tv, wv, iqL, T, w, 'linear');
end
end
