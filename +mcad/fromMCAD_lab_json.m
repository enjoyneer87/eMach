function out = fromMCAD_lab_json(motFilePath, jsonPath, p)
%FROMMCAD_LAB_JSON  Motor-CAD Lab flux linkage + JSON AC loss → SyRE FluxMap_dq
%
%   out = mcad.fromMCAD_lab_json(motFilePath, jsonPath, p)
%
%   Inputs
%   ------
%   motFilePath : .mot 파일 경로 (Lab 계산 완료 상태)
%   jsonPath    : JEET_ACLoss_*_Map_Summary.json 경로
%   p           : 극쌍수 (예: 8극 → p=4)
%
%   Output fields
%   -------------
%   out.FluxMap_dq   SyRE MMM 호환 구조체
%   out.raw.psi      Lab flux linkage 원본 (보간 전)
%   out.raw.acloss   JSON AC loss 원본 (보간 전)
% motFilePath=motPath
%% ── Step 1: Lab flux linkage 추출 ───────────────────────────────────────────
fprintf('── Step 1: Extract Lab flux linkage\n');
raw_psi = extractLabPsi(motFilePath);

fprintf('  Lab grid : %d currents × %d angles\n', ...
    length(raw_psi.Is_peak), length(raw_psi.gamma));
fprintf('  PsiD range: %.4f – %.4f Wb\n', min(raw_psi.PsiD(:)), max(raw_psi.PsiD(:)));

%% ── Step 2: JSON AC loss 로드 ────────────────────────────────────────────────
fprintf('\n── Step 2: Load JSON AC loss\n');
raw_ac = loadAcLossJson(jsonPath);

fprintf('  AC loss records: %d  (%d speeds)\n', ...
    length(raw_ac.Is_peak), length(raw_ac.speed_vec));

%% ── Step 3: 공통 (Id,Iq) RMS 격자 정의 ──────────────────────────────────────
fprintf('\n── Step 3: Build common grid & interpolate\n');
Id_rms_psi = raw_psi.Id_peak(:) / sqrt(2);
Iq_rms_psi = raw_psi.Iq_peak(:) / sqrt(2);

% unique() 방식은 nI*nG개의 고유한 Id/Iq 값을 만들어
% meshgrid가 (nI*nG) × (nI*nG) = 36×36처럼 과대한 격자를 생성한다.
% 소스 해상도(nI, nG)에 맞춰 linspace로 직접 정의한다.
nI = numel(raw_psi.Is_peak);                        % 전류 포인트 수 (6)
nG = numel(raw_psi.gamma);                           % 위상각 포인트 수 (8)
Is_max_rms = max(raw_psi.Is_peak(:)) / sqrt(2);     % RMS 최대 전류
id_vec = linspace(-Is_max_rms, 0,         nI);      % [nI]  음의 d축
iq_vec = linspace(0,           Is_max_rms, nG);     % [nG]  양의 q축
[Id, Iq] = meshgrid(id_vec, iq_vec);                % [nG × nI]
fprintf('  Grid: %d Id × %d Iq  (was unique→%d×%d)\n', nI, nG, ...
    numel(unique(round(Id_rms_psi,4))), numel(unique(round(Iq_rms_psi,4))));

%% ── Step 4: flux linkage → meshgrid ─────────────────────────────────────────
% 현전류 한계원 바깥 격자 모서리(최대 Id + 최대 Iq)는 convex hull 외부 → NaN.
% 자속쇄교수는 0이 아닌 물리 값이므로 nearest-neighbor로 채운다.
Fd = griddata(Id_rms_psi, Iq_rms_psi, raw_psi.PsiD(:), Id, Iq, 'cubic');
Fq = griddata(Id_rms_psi, Iq_rms_psi, raw_psi.PsiQ(:), Id, Iq, 'cubic');
Fd = fillmissing(Fd, 'nearest');
Fq = fillmissing(Fq, 'nearest');

T    = 1.5 * p * (Fd .* Iq - Fq .* Id);
dTpp = nan(size(Id));

%% ── Step 5: AC loss → meshgrid × speed ──────────────────────────────────────
% AC loss도 peak → RMS 변환 후 보간
rad_ac    = deg2rad(raw_ac.gamma + 90);
Id_rms_ac = raw_ac.Is_peak .* cos(rad_ac) / sqrt(2);
Iq_rms_ac = raw_ac.Is_peak .* sin(rad_ac) / sqrt(2);

speed_vec = raw_ac.speed_vec;
nS        = numel(speed_vec);
sz        = [size(Id), nS];

Pac_total = nan(sz);
Pac_prox  = nan(sz);
Pac_skin  = nan(sz);

for k = 1:nS
    mask = raw_ac.speed == speed_vec(k);
    Pac_total(:,:,k) = griddata(Id_rms_ac(mask), Iq_rms_ac(mask), ...
                                raw_ac.Pac_total_kW(mask), Id, Iq, 'cubic');
    Pac_prox(:,:,k)  = griddata(Id_rms_ac(mask), Iq_rms_ac(mask), ...
                                raw_ac.Pac_prox_kW(mask),  Id, Iq, 'cubic');
    Pac_skin(:,:,k)  = griddata(Id_rms_ac(mask), Iq_rms_ac(mask), ...
                                raw_ac.Pac_skin_kW(mask),  Id, Iq, 'cubic');
end

%% ── Step 6: 출력 조립 ────────────────────────────────────────────────────────
FluxMap_dq.Id           = Id;
FluxMap_dq.Iq           = Iq;
FluxMap_dq.Fd           = Fd;
FluxMap_dq.Fq           = Fq;
FluxMap_dq.T            = T;
FluxMap_dq.dT           = nan(size(Id));
FluxMap_dq.dTpp         = nan(size(Id));
FluxMap_dq.Pac_total_kW = Pac_total;
FluxMap_dq.Pac_prox_kW  = Pac_prox;
FluxMap_dq.Pac_skin_kW  = Pac_skin;
FluxMap_dq.speed_vec    = speed_vec(:)';

out.FluxMap_dq = FluxMap_dq;
out.raw.psi    = raw_psi;
out.raw.acloss = raw_ac;
out.p          = p;

if isfield(raw_psi, 'has_losses') && raw_psi.has_losses
    % griddata 'cubic'은 convex hull 바깥에 NaN을 줌.
    % 철손은 운전 영역 바깥에서 0으로 처리해도 물리적으로 타당함.
    fillNaN = @(M) fillmissing(M, 'constant', 0);

    Pfes_h = fillNaN(griddata(Id_rms_psi, Iq_rms_psi, raw_psi.Pfes_h(:), Id, Iq, 'cubic'));
    Pfes_c = fillNaN(griddata(Id_rms_psi, Iq_rms_psi, raw_psi.Pfes_c(:), Id, Iq, 'cubic'));
    Pfer_h = fillNaN(griddata(Id_rms_psi, Iq_rms_psi, raw_psi.Pfer_h(:), Id, Iq, 'cubic'));
    Pfer_c = fillNaN(griddata(Id_rms_psi, Iq_rms_psi, raw_psi.Pfer_c(:), Id, Iq, 'cubic'));
    Ppm    = fillNaN(griddata(Id_rms_psi, Iq_rms_psi, raw_psi.Ppm(:),    Id, Iq, 'cubic'));

    IronPMLossMap_dq.type   = 'map';
    IronPMLossMap_dq.Id     = Id;
    IronPMLossMap_dq.Iq     = Iq;
    IronPMLossMap_dq.Pfes_h = Pfes_h;
    IronPMLossMap_dq.Pfes_c = Pfes_c;
    IronPMLossMap_dq.Pfer_h = Pfer_h;
    IronPMLossMap_dq.Pfer_c = Pfer_c;
    IronPMLossMap_dq.Ppm    = Ppm;
    IronPMLossMap_dq.n0     = raw_psi.FEALossMap_RefSpeed_Lab;
    IronPMLossMap_dq.f0     = raw_psi.FEALossMap_RefSpeed_Lab * p / 60;
    IronPMLossMap_dq.expH = raw_psi.expH;
    IronPMLossMap_dq.expC = raw_psi.expH; % apply the same iron loss scaling
    IronPMLossMap_dq.expPM = raw_psi.expPM;
    IronPMLossMap_dq.segPM = 1.0;

    out.IronPMLossMap_dq = IronPMLossMap_dq;
    fprintf('  IronPMLossMap_dq: Pfes_h max=%.2fW, Pfer_h max=%.2fW, Ppm max=%.2fW  @ n0=%.0f rpm\n', ...
        max(Pfes_h(:)), max(Pfer_h(:)), max(Ppm(:)), IronPMLossMap_dq.n0);
end

fprintf('  Grid : %d Id × %d Iq  (RMS A)\n', length(id_vec), length(iq_vec));
fprintf('  T range: %.1f – %.1f Nm\n', min(T(:)), max(T(:)));
fprintf('Done.\n');
end


% ═════════════════════════════════════════════════════════════════════════════
% 내부 함수: Lab flux linkage 추출
% ═════════════════════════════════════════════════════════════════════════════
function raw = extractLabPsi(motFilePath)
%EXTRACTLABPSI  .mot 파일로부터 Lab 포화모델 flux linkage 추출

% ── Motor-CAD Version Detection ───────────────────────────────────────────
mcadVersion = 'Unknown';
try
    if isfile(motFilePath)
        lines = getDataFromMotFiles(motFilePath);
        for idx = 1:numel(lines)
            if contains(lines{idx}, 'Version', 'IgnoreCase', true)
                parts = strsplit(lines{idx}, '=');
                if numel(parts) == 2
                    mcadVersion = strtrim(parts{2});
                    break;
                end
            end
        end
    end
catch
    % ignore
end
fprintf('  Detected Motor-CAD Version in file: %s\n', mcadVersion);

try
    filteredTable = getMCADLabDataFromMotFile(motFilePath);
    colNames = filteredTable.Properties.VariableNames;
catch ME
    fprintf('[WARN] Direct parsing failed with error: %s\n', ME.message);
    filteredTable = table();
    colNames = {};
end

% Psi 컬럼 자동 탐색 (Vs 단위 → PsiD, PsiQ)
psiD_col = colNames(contains(colNames, 'PsiD', 'IgnoreCase', true) | ...
                    contains(colNames, 'Psi_D','IgnoreCase', true));
psiQ_col = colNames(contains(colNames, 'PsiQ', 'IgnoreCase', true) | ...
                    contains(colNames, 'Psi_Q','IgnoreCase', true));
Is_col   = colNames(contains(colNames, 'SatModel_Is', 'IgnoreCase', true));
gam_col  = colNames(contains(colNames, 'SatModel_Gamma', 'IgnoreCase', true) | ...
                    contains(colNames, 'Gamma_Lab',      'IgnoreCase', true));

% 유효성 체크 (필수 컬럼 누락 시 Fallback 적용)
missing_cols = {};
if isempty(psiD_col), missing_cols{end+1} = 'PsiD'; end
if isempty(psiQ_col), missing_cols{end+1} = 'PsiQ'; end
if isempty(Is_col),   missing_cols{end+1} = 'SatModel_Is_Lab'; end
if isempty(gam_col),  missing_cols{end+1} = 'SatModel_Gamma_Lab'; end
if ~any(strcmp(colNames, 'Id_Peak')), missing_cols{end+1} = 'Id_Peak'; end
if ~any(strcmp(colNames, 'Iq_Peak')), missing_cols{end+1} = 'Iq_Peak'; end

if ~isempty(missing_cols)
    fprintf('[WARN] Missing fields for direct parsing: %s\n', strjoin(missing_cols, ', '));
    if ispc
        fprintf('  Attempting Fallback via ActiveX/COM...\n');
        try
            raw = extractLabPsiViaActiveX(motFilePath);
            return;
        catch ME
            error('COM Fallback also failed: %s\nDetails: %s', ME.identifier, ME.message);
        end
    else
        error('Direct parsing failed due to missing columns, and COM Fallback is not supported on this OS.');
    end
end

PsiD_flat = filteredTable.(psiD_col{1});
PsiQ_flat = filteredTable.(psiQ_col{1});
Is_flat   = filteredTable.(Is_col{1});
gam_flat  = filteredTable.(gam_col{1});

% Id_Peak, Iq_Peak은 getMCADLabDataFromMotFile 내부에서 pkgamma2dq로 계산됨
Id_flat   = filteredTable.Id_Peak;
Iq_flat   = filteredTable.Iq_Peak;

% 격자 추출
Is_vec  = sort(unique(round(Is_flat,  4)));
gam_vec = sort(unique(round(gam_flat, 4)));
nI = numel(Is_vec);
nG = numel(gam_vec);

% flat table → [nI × nG] 행렬로 reshape
PsiD = reshape(PsiD_flat, [nI, nG]);
PsiQ = reshape(PsiQ_flat, [nI, nG]);
[GAMMA, IS] = meshgrid(gam_vec, Is_vec);
Id_peak = reshape(Id_flat, [nI, nG]);
Iq_peak = reshape(Iq_flat, [nI, nG]);

raw.Is_peak = Is_vec;
raw.gamma   = gam_vec;
raw.PsiD    = PsiD;
raw.PsiQ    = PsiQ;
raw.Id_peak = Id_peak;
raw.Iq_peak = Iq_peak;

% Extract Iron/PM losses if available in the parsed table
try
    n0 = 0;
    expH = 1.5;
    expPM = 2.0;
    fid = fopen(motFilePath, 'r');
    if fid ~= -1
        while ~feof(fid)
            line = fgets(fid);
            if contains(line, 'FEALossMap_RefSpeed_Lab')
                parts = split(line, '=');
                if length(parts) > 1
                    val_str = regexprep(strtrim(parts{2}), '[;\]\)]', '');
                    val = str2double(val_str);
                    if ~isnan(val), n0 = val; end
                end
            elseif contains(line, 'Speed_Coeff_-_Stator_Iron_Loss_[Back_Iron]')
                parts = split(line, '=');
                if length(parts) > 1
                    val_str = regexprep(strtrim(parts{2}), '[;\]\)]', '');
                    val = str2double(val_str);
                    if ~isnan(val), expH = val; end
                end
            elseif contains(line, 'Speed_Coeff_-_Magnet_Iron_Loss')
                parts = split(line, '=');
                if length(parts) > 1
                    val_str = regexprep(strtrim(parts{2}), '[;\]\)]', '');
                    val = str2double(val_str);
                    if ~isnan(val), expPM = val; end
                end
            end
        end
        fclose(fid);
    end
    raw.FEALossMap_RefSpeed_Lab = n0;
    raw.expH = expH;
    raw.expPM = expPM;
catch
    raw.FEALossMap_RefSpeed_Lab = 0;
    raw.expH = 1.5;
    raw.expPM = 2.0;
end

try
    % getMCADLabDataFromMotFile drops all-zero columns via removevars.
    % If Lab FEA map model was not run, these columns will be absent.
    % Fall back to direct .mot text parse via getMcadActiveXTableFromMotFile.
    colNames_ft = filteredTable.Properties.VariableNames;
    ironCols = {'FeLossBackIronHy_MotorLAB','FeLossToothHy_MotorLAB', ...
                'FeLossBackIronEd_MotorLAB','FeLossToothEd_MotorLAB', ...
                'FeLossRotorHy_MotorLAB','FeLossRotorPoleHy_MotorLAB', ...
                'FeLossRotorEd_MotorLAB','FeLossRotorPoleEd_MotorLAB', ...
                'MagLossArray_MotorLAB'};
    missingIron = ironCols(~ismember(ironCols, colNames_ft));

    if ~isempty(missingIron)
        % Re-read raw axStruct to recover zero-valued (dropped) columns
        fprintf('  [IronLoss] %d columns missing from filteredTable (dropped as zero?), re-reading from .mot\n', numel(missingIron));
        axStruct = mcad.getMcadActiveXTableFromMotFile(motFilePath);
        filteredTable = supplementIronLossFromAxStruct(filteredTable, axStruct, missingIron, nI, nG);
    end

    Pfes_h_flat = filteredTable.FeLossBackIronHy_MotorLAB + filteredTable.FeLossToothHy_MotorLAB;
    Pfes_c_flat = filteredTable.FeLossBackIronEd_MotorLAB + filteredTable.FeLossToothEd_MotorLAB;
    Pfer_h_flat = filteredTable.FeLossRotorHy_MotorLAB    + filteredTable.FeLossRotorPoleHy_MotorLAB;
    Pfer_c_flat = filteredTable.FeLossRotorEd_MotorLAB    + filteredTable.FeLossRotorPoleEd_MotorLAB;
    Ppm_flat    = filteredTable.MagLossArray_MotorLAB;

    % Validate: if all components are zero, Lab FEA map was not computed
    totalLoss = sum(abs(Pfes_h_flat)) + sum(abs(Pfes_c_flat)) + ...
                sum(abs(Pfer_h_flat)) + sum(abs(Pfer_c_flat));
    if totalLoss < 1e-9
        fprintf('  [IronLoss] All iron loss values are zero — Lab FEA map model not computed. Skipping.\n');
        raw.has_losses = false;
    else
        raw.Pfes_h = reshape(Pfes_h_flat, [nI, nG]);
        raw.Pfes_c = reshape(Pfes_c_flat, [nI, nG]);
        raw.Pfer_h = reshape(Pfer_h_flat, [nI, nG]);
        raw.Pfer_c = reshape(Pfer_c_flat, [nI, nG]);
        raw.Ppm    = reshape(Ppm_flat,    [nI, nG]);
        raw.has_losses = true;
        fprintf('  [IronLoss] Extracted: Pfes_h max=%.2fW, Pfer_h max=%.2fW, Ppm max=%.2fW\n', ...
            max(abs(raw.Pfes_h(:))), max(abs(raw.Pfer_h(:))), max(abs(raw.Ppm(:))));
    end
catch ME
    fprintf('  [IronLoss] Extraction failed: %s\n', ME.message);
    raw.has_losses = false;
end
end


% ═════════════════════════════════════════════════════════════════════════════
% 내부 함수: JSON AC loss 로드
% ═════════════════════════════════════════════════════════════════════════════
function raw = loadAcLossJson(jsonPath, proximity_model)
if nargin < 2, proximity_model = 1; end   % 1 = Hybrid FEA

txt  = fileread(jsonPath);
data = jsondecode(txt);

if isstruct(data) && isfield(data, 'records')
    records = data.records;
else
    records = data;
end

if iscell(records)
    valid_indices = [];
    for i = 1:numel(records)
        r = records{i};
        if isstruct(r) && isfield(r, 'proximity_model') && r.proximity_model == proximity_model && isfield(r, 'hybrid_total_kW')
            valid_indices(end+1) = i;
        end
    end
    
    if isempty(valid_indices)
        error('No records with proximity_model=%d found in %s', proximity_model, jsonPath);
    end
    
    raw.Is_peak      = cellfun(@(r) r.current,          records(valid_indices));
    raw.gamma        = cellfun(@(r) r.phase,             records(valid_indices));
    raw.speed        = cellfun(@(r) r.speed,             records(valid_indices));
    raw.Pac_total_kW = cellfun(@(r) r.hybrid_total_kW,  records(valid_indices));
    raw.Pac_prox_kW  = cellfun(@(r) r.hybrid_prox_kW,   records(valid_indices));
    raw.Pac_skin_kW  = cellfun(@(r) r.hybrid_skin_kW,   records(valid_indices));
else
    pmVec = arrayfun(@(r) r.proximity_model, records);
    has_field = arrayfun(@(r) isfield(r, 'hybrid_total_kW'), records);
    sel   = records(pmVec == proximity_model & has_field);
    
    if isempty(sel)
        error('No records with proximity_model=%d found in %s', proximity_model, jsonPath);
    end
    
    raw.Is_peak      = arrayfun(@(r) r.current,          sel);
    raw.gamma        = arrayfun(@(r) r.phase,             sel);
    raw.speed        = arrayfun(@(r) r.speed,             sel);
    raw.Pac_total_kW = arrayfun(@(r) r.hybrid_total_kW,  sel);
    raw.Pac_prox_kW  = arrayfun(@(r) r.hybrid_prox_kW,   sel);
    raw.Pac_skin_kW  = arrayfun(@(r) r.hybrid_skin_kW,   sel);
end

raw.speed_vec    = sort(unique(raw.speed));
end


% ═════════════════════════════════════════════════════════════════════════════
% 내부 함수: ActiveX/COM Fallback 추출
% ═════════════════════════════════════════════════════════════════════════════
function raw = extractLabPsiViaActiveX(motFilePath)
fprintf('  Initializing Motor-CAD COM Server...\n');
mcad = actxserver('MotorCAD.AppAutomation');
try
    invoke(mcad, 'LoadFromFile', motFilePath);
    
    [~, nI_val] = invoke(mcad, 'GetVariable', 'ModelBuildPoints_Current_Lab');
    [~, nG_val] = invoke(mcad, 'GetVariable', 'ModelBuildPoints_Gamma_Lab');
    [~, I_max_val] = invoke(mcad, 'GetVariable', 'PeakCurrentAmplitude');
    
    nI = nI_val; if ischar(nI) || isstring(nI), nI = str2double(nI); end
    nG = nG_val; if ischar(nG) || isstring(nG), nG = str2double(nG); end
    I_max = I_max_val; if ischar(I_max) || isstring(I_max), I_max = str2double(I_max); end
    
    Is_vec = linspace(0, I_max, nI);
    gam_vec = linspace(0, 90, nG);
    
    [~, psiD_str] = invoke(mcad, 'GetVariable', 'PsiDModel_Lab');
    [~, psiQ_str] = invoke(mcad, 'GetVariable', 'PsiQModel_Lab');
    
    psiD_nums = parseNumericString(psiD_str);
    psiQ_nums = parseNumericString(psiQ_str);
    
    PsiD = reshape(psiD_nums, [nI, nG]);
    PsiQ = reshape(psiQ_nums, [nI, nG]);
    
    [GAMMA, IS] = meshgrid(gam_vec, Is_vec);
    rad = (GAMMA + 90) * pi / 180;
    Id_peak = IS .* cos(rad);
    Iq_peak = IS .* sin(rad);
    
    raw.Is_peak = Is_vec;
    raw.gamma   = gam_vec;
    raw.PsiD    = PsiD;
    raw.PsiQ    = PsiQ;
    raw.Id_peak = Id_peak;
    raw.Iq_peak = Iq_peak;
    
    % Try to extract losses via COM if available
    try
        [~, speed_val] = invoke(mcad, 'GetVariable', 'FEALossMap_RefSpeed_Lab');
        [~, expH_val] = invoke(mcad, 'GetVariable', 'Speed_Coeff_-_Stator_Iron_Loss_[Back_Iron]');
        [~, expPM_val] = invoke(mcad, 'GetVariable', 'Speed_Coeff_-_Magnet_Iron_Loss');
        [~, backIronHy] = invoke(mcad, 'GetVariable', 'FeLossBackIronHy_MotorLAB');
        [~, toothHy] = invoke(mcad, 'GetVariable', 'FeLossToothHy_MotorLAB');
        [~, backIronEd] = invoke(mcad, 'GetVariable', 'FeLossBackIronEd_MotorLAB');
        [~, toothEd] = invoke(mcad, 'GetVariable', 'FeLossToothEd_MotorLAB');
        [~, rotorHy] = invoke(mcad, 'GetVariable', 'FeLossRotorHy_MotorLAB');
        [~, rotorPoleHy] = invoke(mcad, 'GetVariable', 'FeLossRotorPoleHy_MotorLAB');
        [~, rotorEd] = invoke(mcad, 'GetVariable', 'FeLossRotorEd_MotorLAB');
        [~, rotorPoleEd] = invoke(mcad, 'GetVariable', 'FeLossRotorPoleEd_MotorLAB');
        [~, magLoss] = invoke(mcad, 'GetVariable', 'MagLossArray_MotorLAB');
        
        n0 = speed_val; if ischar(n0) || isstring(n0), n0 = str2double(n0); end
        raw.FEALossMap_RefSpeed_Lab = n0;
        
        expH = expH_val; if ischar(expH) || isstring(expH), expH = str2double(expH); end
        if isnan(expH), expH = 1.5; end
        raw.expH = expH;
        
        expPM = expPM_val; if ischar(expPM) || isstring(expPM), expPM = str2double(expPM); end
        if isnan(expPM), expPM = 2.0; end
        raw.expPM = expPM;
        
        Pfes_h_flat = parseNumericString(backIronHy) + parseNumericString(toothHy);
        Pfes_c_flat = parseNumericString(backIronEd) + parseNumericString(toothEd);
        Pfer_h_flat = parseNumericString(rotorHy) + parseNumericString(rotorPoleHy);
        Pfer_c_flat = parseNumericString(rotorEd) + parseNumericString(rotorPoleEd);
        Ppm_flat = parseNumericString(magLoss);
        
        raw.Pfes_h = reshape(Pfes_h_flat, [nI, nG]);
        raw.Pfes_c = reshape(Pfes_c_flat, [nI, nG]);
        raw.Pfer_h = reshape(Pfer_h_flat, [nI, nG]);
        raw.Pfer_c = reshape(Pfer_c_flat, [nI, nG]);
        raw.Ppm = reshape(Ppm_flat, [nI, nG]);
        raw.has_losses = true;
    catch
        raw.FEALossMap_RefSpeed_Lab = 0;
        raw.expH = 1.5;
        raw.expPM = 2.0;
        raw.has_losses = false;
    end
    
    invoke(mcad, 'Quit');
catch ME
    try invoke(mcad, 'Quit'); catch, end
    rethrow(ME);
end
end

function nums = parseNumericString(s)
s = strrep(s, ':', ' ');
s = strrep(s, ';', ' ');
nums = sscanf(s, '%f');
end


% ─────────────────────────────────────────────────────────────────────────────
% supplementIronLossFromAxStruct
%   getMCADLabDataFromMotFile drops all-zero columns via removevars.
%   This helper re-reads those columns directly from the raw axStruct
%   and adds them back to the table so downstream code can find them.
% ─────────────────────────────────────────────────────────────────────────────
function tbl = supplementIronLossFromAxStruct(tbl, axStruct, missingCols, nI, nG)
tableNames = fieldnames(axStruct);
for c = 1:numel(missingCols)
    varName = missingCols{c};
    val = [];
    for t = 1:numel(tableNames)
        subTbl = axStruct.(tableNames{t});
        if istable(subTbl) && any(strcmp(subTbl.AutomationName, varName))
            idx = find(strcmp(subTbl.AutomationName, varName), 1);
            valStr = subTbl.CurrentValue{idx};
            if iscell(valStr), valStr = valStr{1}; end
            val = parseNumericString(valStr);
            break;
        end
    end
    if isempty(val)
        val = zeros(nI * nG, 1);
    end
    % exportRawLossMap reshape convention: (reshape to [nG,nI])' = [nI,nG] flat
    val = val(:);
    if numel(val) == nI * nG
        tbl.(varName) = val;
    else
        tbl.(varName) = zeros(nI * nG, 1);
    end
end
end
