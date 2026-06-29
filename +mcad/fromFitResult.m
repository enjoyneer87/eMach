function out = fromFitResult(FitResultStr, p, jsonPath, n0_rpm)
%MCAD.FROMFITRESULT  plotMultipleInterpSatuMapSubplots 결과 → SyRE FluxMap_dq
%
%   out = mcad.fromFitResult(FitResultStr, p)
%   out = mcad.fromFitResult(FitResultStr, p, jsonPath)
%   out = mcad.fromFitResult(FitResultStr, p, jsonPath, n0_rpm)
%
%   장점
%   ----
%   · 플롯 워크플로우와 보간을 공유 → 추가 보간 없음
%   · scatteredInterpolant(linear, linear) 사용 → 경계 NaN 없음
%   · 100×100 해상도 (6×8 격자 기반 fromMCAD_lab_json 대비 고해상도)
%
%   권장 워크플로우
%   ---------------
%   filteredTable = getMCADLabDataFromMotFile(motPath);
%   MCADLinkTable = reNameLabTable2LabLink(filteredTable);
%   FitResultStr  = plotMultipleInterpSatuMapSubplots(@plotFitResult, MCADLinkTable, 'bilinear');
%   out = mcad.fromFitResult(FitResultStr, 4, jsonPath);
%   mcad.saveSyreFluxMap(out, outMat);
%
%   Inputs
%   ------
%   FitResultStr : plotMultipleInterpSatuMapSubplots 반환 구조체 배열
%   p            : 극쌍수
%   jsonPath     : (옵션) JEET AC loss JSON 경로
%   n0_rpm       : (옵션) 철손 기준 속도 (rpm). FitResultStr 외부 입력.

if nargin < 3, jsonPath = []; end
if nargin < 4, n0_rpm   = 0;  end

varNames = {FitResultStr.varNames};

%% ── Step 1: Fd, Fq 추출 ─────────────────────────────────────────────────────
fprintf('── Step 1: Extract Fd, Fq from FitResultStr\n');

% reNameLabTable2LabLink 결과: 'Flux Linkage D' / 'Flux Linkage Q'
% 또는 rename 안 된 경우: 'SatModel_PsiD_Lab' / 'PsiDModel_Lab' 등
psiD_idx = findFirst(varNames, {'Flux Linkage D','PsiD','Psi D','SatModel_PsiD','PsiDModel'});
psiQ_idx = findFirst(varNames, {'Flux Linkage Q','PsiQ','Psi Q','SatModel_PsiQ','PsiQModel'});

if isempty(psiD_idx) || isempty(psiQ_idx)
    error('mcad:fromFitResult:noPsi', ...
        ['FitResultStr에서 PsiD/PsiQ를 찾지 못했습니다.\n' ...
         '사용 가능한 변수:\n  %s'], strjoin(varNames, '\n  '));
end

% XGrid/YGrid: PEAK 전류(A), ZGrid: Wb
Id_pk = FitResultStr(psiD_idx).singleDataSet.XGrid;
Iq_pk = FitResultStr(psiD_idx).singleDataSet.YGrid;
Fd    = FitResultStr(psiD_idx).singleDataSet.ZGrid;
Fq    = FitResultStr(psiQ_idx).singleDataSet.ZGrid;

% Peak → RMS
Id = Id_pk / sqrt(2);
Iq = Iq_pk / sqrt(2);
T  = 1.5 * p * (Fd .* Iq - Fq .* Id);

fprintf('  Grid : %d Id × %d Iq  (Id_pk %.1f–%.1f A, Iq_pk %.1f–%.1f A)\n', ...
    size(Id,2), size(Id,1), min(Id_pk(:)), max(Id_pk(:)), min(Iq_pk(:)), max(Iq_pk(:)));
fprintf('  Fd range: %.4f – %.4f Wb\n', min(Fd(:)), max(Fd(:)));
fprintf('  T range : %.1f – %.1f Nm\n',  min(T(:)),  max(T(:)));

%% ── Step 2: AC loss (JSON) → 동일 meshgrid ─────────────────────────────────
Pac_total = [];  Pac_prox = [];  Pac_skin = [];  speed_vec = [];

if ~isempty(jsonPath) && isfile(jsonPath)
    fprintf('\n── Step 2: AC loss (JSON)\n');
    raw_ac = mcad.loadAcLossJson(jsonPath);

    rad_ac   = deg2rad(raw_ac.gamma + 90);
    Id_pk_ac = raw_ac.Is_peak .* cos(rad_ac);
    Iq_pk_ac = raw_ac.Is_peak .* sin(rad_ac);

    speed_vec = raw_ac.speed_vec;
    nS        = numel(speed_vec);
    sz        = [size(Id), nS];
    Pac_total = zeros(sz);  Pac_prox = zeros(sz);  Pac_skin = zeros(sz);

    for k = 1:nS
        mask = raw_ac.speed == speed_vec(k);
        Pac_total(:,:,k) = interpScattered(Id_pk_ac(mask), Iq_pk_ac(mask), raw_ac.Pac_total_kW(mask), Id_pk, Iq_pk);
        Pac_prox(:,:,k)  = interpScattered(Id_pk_ac(mask), Iq_pk_ac(mask), raw_ac.Pac_prox_kW(mask),  Id_pk, Iq_pk);
        Pac_skin(:,:,k)  = interpScattered(Id_pk_ac(mask), Iq_pk_ac(mask), raw_ac.Pac_skin_kW(mask),  Id_pk, Iq_pk);
    end
    fprintf('  AC loss: %d speeds interpolated\n', nS);
end

%% ── Step 3: FluxMap_dq 조립 ─────────────────────────────────────────────────
FluxMap_dq.Id   = Id;
FluxMap_dq.Iq   = Iq;
FluxMap_dq.Fd   = Fd;
FluxMap_dq.Fq   = Fq;
FluxMap_dq.T    = T;
FluxMap_dq.dT   = nan(size(Id));
FluxMap_dq.dTpp = nan(size(Id));

if ~isempty(Pac_total)
    FluxMap_dq.Pac_total_kW = Pac_total;
    FluxMap_dq.Pac_prox_kW  = Pac_prox;
    FluxMap_dq.Pac_skin_kW  = Pac_skin;
    FluxMap_dq.speed_vec    = speed_vec(:)';
end

out.FluxMap_dq   = FluxMap_dq;
out.FitResultStr = FitResultStr;
out.p            = p;

%% ── Step 4: 철손 맵 ─────────────────────────────────────────────────────────
%   reNameLabTable2LabLink 변환 결과 이름으로 검색
%   Pfes_h = 스테이터 히스테리시스 (Back Iron + Tooth)
%   Pfes_c = 스테이터 와전류    (Back Iron + Tooth)
%   Pfer_h = 로터   히스테리시스 (Back Iron + Pole)
%   Pfer_c = 로터   와전류    (Back Iron + Pole)
%   Ppm    = 자석 손실
fprintf('\n── Step 4: Iron & PM loss map\n');

Pfes_h = sumZGrids(FitResultStr, Id_pk, Iq_pk, varNames, ...
    {'Hysteresis Iron Loss \(Stator Back Iron\)', 'Hysteresis Iron Loss \(Stator Tooth\)'});
Pfes_c = sumZGrids(FitResultStr, Id_pk, Iq_pk, varNames, ...
    {'Eddy Iron Loss \(Stator Back Iron\)',        'Eddy Iron Loss \(Stator Tooth\)'});
Pfer_h = sumZGrids(FitResultStr, Id_pk, Iq_pk, varNames, ...
    {'Hysteresis Iron Loss \(Rotor Back Iron\)',   'Hysteresis Iron Loss \(Rotor Pole\)'});
Pfer_c = sumZGrids(FitResultStr, Id_pk, Iq_pk, varNames, ...
    {'Eddy Iron Loss \(Rotor Back Iron\)',          'Eddy Iron Loss \(Rotor Pole\)'});
Ppm    = sumZGrids(FitResultStr, Id_pk, Iq_pk, varNames, {'Magnet Loss'});

totalIron = sum(abs(Pfes_h(:))) + sum(abs(Pfes_c(:))) + sum(abs(Pfer_h(:)));
if totalIron < 1e-9
    fprintf('  철손 변수 없음 (Lab FEA map 미계산 또는 모두 0) — IronPMLossMap_dq 생략\n');
else
    IronPMLossMap_dq.type   = 'map';
    IronPMLossMap_dq.Id     = Id;
    IronPMLossMap_dq.Iq     = Iq;
    IronPMLossMap_dq.Pfes_h = Pfes_h;
    IronPMLossMap_dq.Pfes_c = Pfes_c;
    IronPMLossMap_dq.Pfer_h = Pfer_h;
    IronPMLossMap_dq.Pfer_c = Pfer_c;
    IronPMLossMap_dq.Ppm    = Ppm;
    IronPMLossMap_dq.n0     = n0_rpm;
    IronPMLossMap_dq.f0     = n0_rpm * p / 60;
    IronPMLossMap_dq.expH   = 1.0;
    IronPMLossMap_dq.expC   = 2.0;
    IronPMLossMap_dq.expPM  = 2.0;
    IronPMLossMap_dq.segPM  = 1.0;
    out.IronPMLossMap_dq = IronPMLossMap_dq;
    fprintf('  Pfes_h max=%.2fW,  Pfer_h max=%.2fW,  Ppm max=%.2fW\n', ...
        max(Pfes_h(:)), max(Pfer_h(:)), max(Ppm(:)));
end

fprintf('Done.\n');
end


% ─────────────────────────────────────────────────────────────────────────────
% 첫 번째 패턴 매치 인덱스 반환 (대소문자 무시, 부분 문자열 포함)
% ─────────────────────────────────────────────────────────────────────────────
function idx = findFirst(varNames, patterns)
idx = [];
for k = 1:numel(patterns)
    hits = find(~cellfun('isempty', regexpi(varNames, patterns{k})));
    if ~isempty(hits)
        idx = hits(1);
        return;
    end
end
end


% ─────────────────────────────────────────────────────────────────────────────
% 여러 패턴에 매칭되는 FitResultStr 항목의 ZGrid를 합산
% 그리드 불일치 시 fitResult 함수 핸들로 Id_pk/Iq_pk에서 재평가
% ─────────────────────────────────────────────────────────────────────────────
function Z = sumZGrids(FitResultStr, Id_pk, Iq_pk, varNames, patterns)
Z = zeros(size(Id_pk));
for k = 1:numel(patterns)
    idx = findFirst(varNames, patterns(k));
    if isempty(idx), continue; end
    ds = FitResultStr(idx).singleDataSet;
    if isequal(size(ds.XGrid), size(Id_pk)) && ...
       max(abs(ds.XGrid(:) - Id_pk(:))) < 1e-6 * (max(Id_pk(:)) - min(Id_pk(:)) + eps)
        % 격자 동일 → ZGrid 직접 합산
        Z = Z + ds.ZGrid;
    else
        % 격자 다르면 fitResult 함수 핸들로 재보간
        f = FitResultStr(idx).fitResult;
        v = f(Id_pk, Iq_pk);
        v(isnan(v)) = 0;
        Z = Z + v;
    end
end
end


% ─────────────────────────────────────────────────────────────────────────────
% scatteredInterpolant(linear, linear)으로 보간 — 경계 외삽 포함, NaN 없음
% ─────────────────────────────────────────────────────────────────────────────
function Z = interpScattered(x, y, v, Xq, Yq)
F = scatteredInterpolant(x(:), y(:), v(:), 'linear', 'linear');
Z = F(Xq, Yq);
Z(Z < 0) = 0;   % 물리적으로 음수 손실 불가
end
