function S = apply_mcb_reference(speed_rpm, workDir)
%APPLY_MCB_REFERENCE  MCB 기준표 + 맵 대칭확장 = 단계 1 이 실제로 추종하는 조합.
%
%   두 가지를 고친다 (2026-09-18 확인).
%     1) 기준표를 Motor Control Blockset 이 만든 것으로 바꾼다.
%        mcb.generateMotorLUT(pmsm, inverter, 'idiqLUTs') 에 Lab 자속맵(method='FluxDQ')을 넣으면
%        MTPA + 약자속을 MCB 규약(FWCMethod 'vclmt')대로 풀어 id(T, w), iq(T, w) 를 준다.
%        Lab 자체 궤적과 진각 0.4도 / 전류 1~9 % 이내로 일치한다.
%        PC1 이 손으로 만든 표는 저토크에서 전류가 34 % 과했다(180.9 대 134.6 A @5 N·m).
%     2) 맵을 iq < 0 으로 대칭 확장한다(λd 우함수, λq·토크 기함수).
%        Lab export 는 한 사분면(iq >= 0)뿐이라, 과도 중 iq 가 0 을 스치면 경계에 붙어
%        빠져나오지 못한다 — 폐루프가 늘 감마 90.00 도에서 멈추던 원인이 이것이었다.
%
%   결과(16 krpm, pi_dec, Ts=50 us): 전류가 기준표를 0.1~0.5 %, 진각 0.4 도 이내로 따라간다.
%   토크가 11~16 % 낮게 보고되는 것은 정의 차이다 — MCB 표는 전자기 토크로 만들었고
%   플랜트는 축 토크를 보고한다(차이 = 철손·자석손의 토크 환산). 필요하면 TorqueTable 에
%   P.Tshaft 를 넣어 다시 생성하면 된다.

if nargin < 1 || isempty(speed_rpm), speed_rpm = 16000; end
if nargin < 2 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
S = load(fullfile(workDir, sprintf('e10_stage1_data_%d.mat', speed_rpm)));
M = load(fullfile(workDir, 'mcb_lut.mat'));
L = M.LUT;  k = find(L.wrpmVec == speed_rpm, 1);
assert(~isempty(k), 'MCB 표에 %g rpm 이 없다', speed_rpm);

S.T_ref_vec = L.trefVec;
S.id_ref_current = L.idTable(:, k).';
S.iq_ref_current = L.iqTable(:, k).';
S.gamma_ref_current = atan2d(-S.id_ref_current, S.iq_ref_current);
S.I_ref_current = hypot(S.id_ref_current, S.iq_ref_current)/sqrt(2);

% --- iq < 0 으로 대칭 확장
S.Fd      = [flipud(S.Fd(2:end, :));      S.Fd];
S.Fq      = [-flipud(S.Fq(2:end, :));     S.Fq];
S.T_shaft = [-flipud(S.T_shaft(2:end, :)); S.T_shaft];
S.iq_pk   = [-fliplr(S.iq_pk(2:end)), S.iq_pk];

S.fd_ref_current = interp2(S.id_pk, S.iq_pk, S.Fd, S.id_ref_current, S.iq_ref_current, 'linear');
S.fq_ref_current = interp2(S.id_pk, S.iq_pk, S.Fq, S.id_ref_current, S.iq_ref_current, 'linear');

% --- 역맵 재생성 (확장된 영역에서)
idF = linspace(S.id_pk(1), S.id_pk(end), 4*numel(S.id_pk));
iqF = linspace(S.iq_pk(1), S.iq_pk(end), 4*numel(S.iq_pk));
[IDf, IQf] = meshgrid(idF, iqF);
FD = interp2(S.id_pk, S.iq_pk, S.Fd, IDf, IQf, 'spline');
FQ = interp2(S.id_pk, S.iq_pk, S.Fq, IDf, IQf, 'spline');
nF = 281;
S.fd_vec = linspace(min(FD(:)), max(FD(:)), nF);
S.fq_vec = linspace(min(FQ(:)), max(FQ(:)), nF);
[FDq, FQq] = meshgrid(S.fd_vec, S.fq_vec);
Fi = scatteredInterpolant(FD(:), FQ(:), IDf(:), 'linear', 'linear');  S.id_of_flux = Fi(FDq, FQq);
Fj = scatteredInterpolant(FD(:), FQ(:), IQf(:), 'linear', 'linear');  S.iq_of_flux = Fj(FDq, FQq);

idB = interp2(S.fd_vec, S.fq_vec, S.id_of_flux, FD, FQ, 'linear');
iqB = interp2(S.fd_vec, S.fq_vec, S.iq_of_flux, FD, FQ, 'linear');
ok = isfinite(idB) & isfinite(iqB);
fprintf('역맵 왕복 99분위: id %.2f, iq %.2f Apk (맵 %d x %d)\n', ...
        prctile(abs(idB(ok)-IDf(ok)), 99), prctile(abs(iqB(ok)-IQf(ok)), 99), ...
        numel(S.id_pk), numel(S.iq_pk));
f = fullfile(workDir, sprintf('e10_stage1_data_%d_mcb.mat', speed_rpm));
save(f, '-struct', 'S');
fprintf('-> %s\n', f);
end
