function [formula, info] = buildAfCustomLossFormula(jsonPath, method)
%BUILDAFCUSTOMLOSSFORMULA AF JSON → Motor-CAD Lab Internal Custom Loss 수식 생성
%
%   [formula, info] = mcad.buildAfCustomLossFormula(jsonPath, method)
%
%   입력:
%     jsonPath : AF_RBF_model_*.json 경로 (예: map_exports/e10/SC/AF_RBF_model_SC.json)
%     method   : 'A' (기본) 속도 2차 다항식 | 'B' 3D RBF 전체 수식
%
%   출력:
%     formula  : Motor-CAD Custom Loss 수식 문자열.
%                추가 손실 = (AF-1) × Stator_Copper_Loss_AC 형태
%     info     : .method, .modelType, .nChars, .requiredVars, (.coeffs)
%
%   Method A: separable_model.speed_poly_coeffs = [a b c] 에서
%     Stator_Copper_Loss_AC * (a*(Speed/1000)**2 + b*(Speed/1000) + (c-1))
%     (AF에서 -1 → 추가 손실만. Speed 단위: RPM, s=Speed/1000 → kRPM)
%
%   Method B: mcad_formula_full 그대로 사용 (이미 `... - Stator_Copper_Loss_AC`
%     꼴로 (AF-1)·P_AC 형태). 개행만 공백으로 정리.
%
%   주의: mcad_formula_reduced_30 / top20 필드는 separable 수식 복제본(생성 버그)
%         이므로 사용하지 않음.

if nargin < 2 || isempty(method)
    method = 'A';
end
assert(isfile(jsonPath), 'AF JSON 없음: %s', jsonPath);

raw = jsondecode(fileread(jsonPath));

info = struct();
info.method    = upper(method);
info.modelType = raw.model_type;
info.jsonPath  = jsonPath;

switch upper(method)
    case 'A'
        c = raw.separable_model.speed_poly_coeffs(:);   % [a; b; c]
        assert(numel(c) == 3, 'speed_poly_coeffs는 3개여야 함 (현재 %d개)', numel(c));
        formula = sprintf(['Stator_Copper_Loss_AC * ((%.9g)*(Speed/1000)**2' ...
                           ' + (%.9g)*(Speed/1000) + (%.9g))'], c(1), c(2), c(3) - 1);
        info.coeffs       = c.';
        info.requiredVars = {'Stator_Copper_Loss_AC', 'Speed'};

    case 'B'
        assert(isfield(raw, 'mcad_formula_full'), 'mcad_formula_full 필드 없음');
        formula = regexprep(raw.mcad_formula_full, '\s+', ' ');
        info.requiredVars = {'Stator_Copper_Loss_AC', 'Speed', ...
                             'Stator_Current_Phase_RMS', 'Phase_Advance'};

    otherwise
        error('method는 ''A'' 또는 ''B''만 지원 (입력: %s)', method);
end

info.nChars = numel(formula);
end
