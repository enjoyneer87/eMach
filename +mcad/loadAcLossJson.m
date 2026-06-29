function raw = loadAcLossJson(jsonPath, proximity_model)
%MCAD.LOADACLOSS JSON  JEET_ACLoss_*_Map_Summary.json → raw AC loss 구조체
%
%   raw = mcad.loadAcLossJson(jsonPath)
%   raw = mcad.loadAcLossJson(jsonPath, proximity_model)
%
%   proximity_model : 1 = Hybrid FEA (기본값)
%
%   raw 필드
%   --------
%   Is_peak      [N×1]  peak 전류 (A)
%   gamma        [N×1]  위상각 (deg)
%   speed        [N×1]  속도 (rpm)
%   Pac_total_kW [N×1]
%   Pac_prox_kW  [N×1]
%   Pac_skin_kW  [N×1]
%   speed_vec    [1×nS] 고유 속도 벡터

if nargin < 2, proximity_model = 1; end

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
        if isstruct(r) && isfield(r, 'proximity_model') && ...
                r.proximity_model == proximity_model && isfield(r, 'hybrid_total_kW')
            valid_indices(end+1) = i; %#ok<AGROW>
        end
    end
    if isempty(valid_indices)
        error('mcad:loadAcLossJson:noRecords', ...
            'No records with proximity_model=%d found in %s', proximity_model, jsonPath);
    end
    raw.Is_peak      = cellfun(@(r) r.current,         records(valid_indices));
    raw.gamma        = cellfun(@(r) r.phase,            records(valid_indices));
    raw.speed        = cellfun(@(r) r.speed,            records(valid_indices));
    raw.Pac_total_kW = cellfun(@(r) r.hybrid_total_kW, records(valid_indices));
    raw.Pac_prox_kW  = cellfun(@(r) r.hybrid_prox_kW,  records(valid_indices));
    raw.Pac_skin_kW  = cellfun(@(r) r.hybrid_skin_kW,  records(valid_indices));
else
    pmVec     = arrayfun(@(r) r.proximity_model, records);
    has_field = arrayfun(@(r) isfield(r, 'hybrid_total_kW'), records);
    sel       = records(pmVec == proximity_model & has_field);
    if isempty(sel)
        error('mcad:loadAcLossJson:noRecords', ...
            'No records with proximity_model=%d found in %s', proximity_model, jsonPath);
    end
    raw.Is_peak      = arrayfun(@(r) r.current,         sel);
    raw.gamma        = arrayfun(@(r) r.phase,            sel);
    raw.speed        = arrayfun(@(r) r.speed,            sel);
    raw.Pac_total_kW = arrayfun(@(r) r.hybrid_total_kW, sel);
    raw.Pac_prox_kW  = arrayfun(@(r) r.hybrid_prox_kW,  sel);
    raw.Pac_skin_kW  = arrayfun(@(r) r.hybrid_skin_kW,  sel);
end

raw.speed_vec = sort(unique(raw.speed));
end
