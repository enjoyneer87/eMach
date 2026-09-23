function out = mbc_ref_from_lab(workDir, vsFactors)
%MBC_REF_FROM_LAB  Model-Based Calibration Toolbox 로 e10 전류 기준표(id*, iq* vs 속도·토크)를 만든다.
%
%   MathWorks 예제 "Generate Current Controller Calibration Tables for Flux-Based Motor Controllers"
%   (calibratepmsm) 의 흐름을 따른다. 다이나모/FEA 데이터 대신 Motor-CAD Lab 자속맵과 속도별 축 토크맵
%   (e10_plant_lab.mat, 2000/4000/8000/16000 rpm)에서 교정 데이터를 만든다.
%     Vs = |R i + j ωe λ| (피크, 단계 1·2 플랜트와 같은 식),  Flux = |λ|,  FluxMax = VsMax/ωe
%   전압 한계 VsMax 를 기준(Lab 상전압 한계 285.1 V rms -> 403.2 V 피크)의 vsFactors 배로 바꿔 가며
%   표를 만든다 — 교정 때 두는 전압 여유가 고속 진각 상한을 정한다는 것을 보이기 위해서다.
%
%   출력: mbc_tables.mat  (tables{k}: 속도·토크 격자의 Id/Iq 표, vsFactor)

if nargin < 1 || isempty(workDir), workDir = 'D:\KangDH\Thesis\e10\work_lab_pc1\drive'; end
if nargin < 2, vsFactors = [1.00 0.95 0.90]; end
P = load(fullfile(workDir, 'e10_plant_lab.mat'));
m = P.machine;  p = m.p;  R = m.Rs_80C;
VsBase = m.Vph_lim*sqrt(2);                 % 403.2 V 피크
IsMax = m.I_rated_rms*sqrt(2);              % 650.5 A 피크

% 맵은 M(iq, id) 로 저장돼 있다 (P.axis_note). 13 A 격자는 16 000 rpm 전압 한계 근처에서
% 한 칸에 70 V 이상 변해 한계 안에 드는 점이 거의 없으므로 2 배로 촘촘하게 선형 보간한다.
iqF = linspace(P.iq_pk(1), P.iq_pk(end), 2*numel(P.iq_pk) - 1);
idF = linspace(P.id_pk(1), P.id_pk(end), 2*numel(P.id_pk) - 1);
[IQ, ID] = ndgrid(iqF, idF);
up = @(A) interpn(P.iq_pk, P.id_pk, A, IQ, ID, 'linear');
Fd = up(P.Fd);  Fq = up(P.Fq);
rows = {};
for k = 1:numel(P.speeds)
    n = P.speeds(k);  we = p*n*2*pi/60;
    vd = R*ID - we*Fq;  vq = R*IQ + we*Fd;
    Vs = hypot(vd, vq);
    Is = hypot(ID, IQ);
    keep = Is <= 1.05*IsMax;
    Trq = up(P.Tshaft(:, :, k));
    rows{end+1} = table(Trq(keep), ID(keep), IQ(keep), repmat(n, nnz(keep), 1), Is(keep), Vs(keep), ...
        hypot(Fd(keep), Fq(keep)), repmat(VsBase/we, nnz(keep), 1), ...
        'VariableNames', {'Trq', 'Id', 'Iq', 'n', 'Is', 'Vs', 'Flux', 'FluxMax'}); %#ok<AGROW>
end
mbcData = vertcat(rows{:});
mbcData = mbcData(mbcData.Trq >= 0, :);
fprintf('MBC 데이터: %d 행, 속도 %s\n', height(mbcData), mat2str(unique(mbcData.n)'));

% 토크 격자: 최고속에서 전압 한계 안에 드는 최대 토크까지 (한계 밖 점까지 넣으면 표가 한 점으로 무너진다)
top = mbcData.n == max(P.speeds) & mbcData.Vs <= min(vsFactors)*VsBase;
Tbp = linspace(0, 0.98*max(mbcData.Trq(top)), 25);
out = struct('vsFactor', {}, 'VsMax', {}, 'IsMax', {}, 'speed', {}, 'torque', {}, 'Id', {}, 'Iq', {}, 'raw', {});
for f = vsFactors
    VsMax = f*VsBase;
    t0 = tic;
    [tab, res] = calibratepmsm(mbcData, IsMax, VsMax, 'TableType', 'SpeedTorque', ...
                               'Breakpoints', {[], Tbp});
    fprintf('VsMax %.0f %% (%.1f V pk): %.0f s\n', 100*f, VsMax, toc(t0));
    [spd, trq, Id, Iq] = unpackTables(tab);
    out(end+1) = struct('vsFactor', f, 'VsMax', VsMax, 'IsMax', IsMax, 'speed', spd, 'torque', trq, ...
                        'Id', Id, 'Iq', Iq, 'raw', struct('tables', tab, 'results', res)); %#ok<AGROW>
end
save(fullfile(workDir, 'mbc_tables.mat'), 'out', 'mbcData');
fprintf('-> %s\n', fullfile(workDir, 'mbc_tables.mat'));
end

function [spd, trq, Id, Iq] = unpackTables(tab)
% calibratepmsm 이 돌려주는 구조를 일반화해서 읽는다 (필드 이름은 릴리스마다 다를 수 있다)
fn = fieldnames(tab);
iId = find(contains(fn, 'Id', 'IgnoreCase', true) & contains(fn, 'Table', 'IgnoreCase', true), 1);
iIq = find(contains(fn, 'Iq', 'IgnoreCase', true) & contains(fn, 'Table', 'IgnoreCase', true), 1);
if isempty(iId), disp(tab); error('Id 표 필드를 찾지 못함'); end
tId = tab.(fn{iId});  tIq = tab.(fn{iIq});
if isstruct(tId)
    f2 = fieldnames(tId);
    Id = tId.(f2{find(contains(f2, 'Value', 'IgnoreCase', true), 1)});
    Iq = tIq.(f2{find(contains(f2, 'Value', 'IgnoreCase', true), 1)});
    bp = f2(contains(f2, 'Breakpoint', 'IgnoreCase', true));
    spd = tId.(bp{1});  trq = tId.(bp{2});
else
    Id = tId;  Iq = tIq;
    spd = tab.(fn{find(contains(fn, 'speed', 'IgnoreCase', true), 1)});
    trq = tab.(fn{find(contains(fn, 'torque', 'IgnoreCase', true) | contains(fn, 'trq', 'IgnoreCase', true), 1)});
end
end
