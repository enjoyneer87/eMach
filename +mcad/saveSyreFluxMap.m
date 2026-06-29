function saveSyreFluxMap(out, matPath, motorModelPath)
%SAVESYREFLUXMAP  fromMCAD_lab_json 결과를 SyRE MMM 호환 .mat으로 저장
%
%   mcad.saveSyreFluxMap(out, matPath)
%       FluxMap_dq + raw를 새 .mat 파일로 저장
%
%   mcad.saveSyreFluxMap(out, matPath, motorModelPath)
%       기존 SyRE .mat(motorModelPath)에 FluxMap_dq를 append
%       → GUI_Syre_MMM에서 Load 버튼으로 바로 사용 가능

FluxMap_dq = out.FluxMap_dq;

% fromMCAD_lab_json → out.raw.{psi,acloss}
% fromFitResult     → out.FitResultStr
if isfield(out, 'raw')
    raw_psi    = out.raw.psi;     %#ok<NASGU>
    raw_acloss = out.raw.acloss;  %#ok<NASGU>
    extraFields = {'raw_psi','raw_acloss'};
elseif isfield(out, 'FitResultStr')
    FitResultStr = out.FitResultStr; %#ok<NASGU>
    extraFields  = {'FitResultStr'};
else
    extraFields = {};
end

if isfield(out, 'IronPMLossMap_dq')
    IronPMLossMap_dq = out.IronPMLossMap_dq;
    save(matPath, 'FluxMap_dq', 'IronPMLossMap_dq', extraFields{:});
    fprintf('Saved FluxMap_dq + IronPMLossMap_dq → %s\n', matPath);
else
    save(matPath, 'FluxMap_dq', extraFields{:});
    fprintf('Saved FluxMap_dq → %s\n', matPath);
end

if nargin >= 3 && ~isempty(motorModelPath)
    m = load(motorModelPath);
    if isfield(m, 'motorModel')
        motorModel = m.motorModel;
    else
        motorModel = MMM_load(fileparts(motorModelPath), ...
                              [fliplr(strtok(fliplr(motorModelPath), filesep)) '.mat']);
    end
    motorModel.FluxMap_dq = FluxMap_dq;
    if isfield(out, 'IronPMLossMap_dq')
        motorModel.IronPMLossMap_dq = out.IronPMLossMap_dq;
    end
    save(motorModelPath, 'motorModel', '-append');
    fprintf('Appended FluxMap_dq + IronPMLossMap_dq → %s  (motorModel updated)\n', motorModelPath);
end
end
