function mesData = loadMESviaPythonForMATLAB(mesPath, varargin)
% loadMESviaPythonForMATLAB
% Bridge function for seamless MATLAB workflow:
%   .mes -> Python parser (pyMCAD) -> MATLAB struct/table
%
% Example:
%   mesPath = "F:\KDH\Thesis\JEET\e10\refModel\e10_UserRemesh\FEResultsData\OnLoadTorque_result_1.mes";
%   D = loadMESviaPythonForMATLAB(mesPath, 'PythonExe', 'python', 'StepKey', []);
%   bx = D.Elements.Bx;
%   by = D.Elements.By;
%   A  = D.Elements.A;
%
% Name-Value options:
%   PythonExe : Python executable name/path (default: pyMotorEnv_310 if found, else "python")
%   StepKey   : target step index (default: first step in file)
%   MotPath   : optional .mot path for Motor-CAD export fallback
%   FirstStep : first step for SaveFEAData export range (default: 1)
%   FinalStep : final step for SaveFEAData export range (default: 45)
%   UseCache  : reuse cached txt if exists (default: true)
%   CacheDir  : cache root folder (default: EveryMotor/data/emach data/mes_cache)
%   RepoRoot  : EveryMotor repo root (default: auto-detect)
%   KeepJson  : keep intermediate json file (default: false)

    p = inputParser;
    addRequired(p, 'mesPath', @(x) ischar(x) || isstring(x));
    addParameter(p, 'PythonExe', localDefaultPythonExe(), @(x) ischar(x) || isstring(x));
    addParameter(p, 'StepKey', [], @(x) isempty(x) || isnumeric(x));
    addParameter(p, 'MotPath', "", @(x) ischar(x) || isstring(x));
    addParameter(p, 'FirstStep', 1, @(x) isnumeric(x) && isscalar(x));
    addParameter(p, 'FinalStep', 45, @(x) isnumeric(x) && isscalar(x));
    addParameter(p, 'UseCache', true, @(x) islogical(x) || isnumeric(x));
    addParameter(p, 'CacheDir', localDefaultCacheDir(), @(x) ischar(x) || isstring(x));
    addParameter(p, 'RepoRoot', localRepoRoot(), @(x) ischar(x) || isstring(x));
    addParameter(p, 'KeepJson', false, @(x) islogical(x) || isnumeric(x));
    parse(p, mesPath, varargin{:});

    mesPath = string(p.Results.mesPath);
    if ~isfile(mesPath)
        error('MES file not found: %s', mesPath);
    end

    pythonExe = string(p.Results.PythonExe);
    repoRoot = string(p.Results.RepoRoot);
    keepJson = logical(p.Results.KeepJson);

    if ~isfolder(repoRoot)
        error('RepoRoot does not exist: %s', repoRoot);
    end

    if isempty(p.Results.StepKey)
        stepArg = "None";
    else
        stepArg = string(double(p.Results.StepKey));
    end

    motPath = string(p.Results.MotPath);
    if strlength(strtrim(motPath)) == 0
        motArg = "None";
    else
        motArg = motPath;
    end

    firstStep = double(p.Results.FirstStep);
    finalStep = double(p.Results.FinalStep);
    useCache = logical(p.Results.UseCache);
    cacheDir = string(p.Results.CacheDir);
    if ~isfolder(cacheDir)
        mkdir(cacheDir);
    end

    bridgeInputPath = mesPath;
    cacheTxtPath = "";
    usedCache = false;
    if endsWith(lower(mesPath), ".mes")
        cacheTxtPath = localMakeCacheTxtPath(mesPath, firstStep, finalStep, cacheDir);
        if useCache && isfile(cacheTxtPath)
            bridgeInputPath = cacheTxtPath;
            usedCache = true;
        end
    end

    jsonPath = string(tempname) + ".json";
    cmd = localBuildBridgeCommand(pythonExe, repoRoot, bridgeInputPath, jsonPath, motArg, stepArg, firstStep, finalStep);
    [status, outText] = system(cmd);

    if status ~= 0
        if isfile(jsonPath)
            rawErr = jsondecode(fileread(jsonPath));
            if ~keepJson
                delete(jsonPath);
            end
            if isfield(rawErr, 'error_code') && isfield(rawErr, 'error_message')
                error('Python bridge failed [%s]: %s\n%s', rawErr.error_code, rawErr.error_message, outText);
            end
        end
        error('Python bridge failed. Output:\n%s', outText);
    end

    if ~isfile(jsonPath)
        error('Bridge output json not found: %s', jsonPath);
    end

    raw = jsondecode(fileread(jsonPath));
    if isfield(raw, 'ok') && ~logical(raw.ok)
        errCode = '';
        errMsg = 'unknown bridge error';
        if isfield(raw, 'error_code')
            errCode = string(raw.error_code);
        end
        if isfield(raw, 'error_message')
            errMsg = string(raw.error_message);
        end
        if ~keepJson
            delete(jsonPath);
        end
        error('Python bridge returned failure [%s]: %s', errCode, errMsg);
    end

    if ~keepJson
        delete(jsonPath);
    end

    mesData = struct();
    mesData.SourceMES = char(mesPath);
    mesData.BridgeInputPath = char(bridgeInputPath);
    mesData.UsedCache = usedCache;
    mesData.CacheTxtPath = char(cacheTxtPath);
    mesData.StepKeys = reshape(double(raw.steps), [], 1);
    mesData.UsedStep = double(raw.used_step);
    if isempty(p.Results.StepKey) && numel(mesData.StepKeys) > 1
        warning(['StepKey is empty, so only one step is returned (UsedStep=%d). ', ...
                 'Use loadMESAllStepsViaPythonForMATLAB(...) to collect multiple steps.'], ...
                mesData.UsedStep);
    end
    if isfield(raw, 'source_mode')
        mesData.SourceMode = raw.source_mode;
    else
        mesData.SourceMode = 'unknown';
    end
    if isfield(raw, 'bridge_notes')
        mesData.BridgeNotes = raw.bridge_notes;
    else
        mesData.BridgeNotes = '';
    end

    if isfield(raw, 'meta')
        mesData.Meta = raw.meta;
    else
        mesData.Meta = struct();
    end

    mesData.Elements = localElementsToTable(raw);
    mesData.Nodes = localNodesToTable(raw);

    % Convenience vectors for direct use in existing MATLAB codes.
    mesData.Bx = mesData.Elements.Bx;
    mesData.By = mesData.Elements.By;
    mesData.B = mesData.Elements.B;
    mesData.A = mesData.Elements.A;
    mesData.J = mesData.Elements.J;
    mesData.NodeXYmm = [mesData.Nodes.Xmm, mesData.Nodes.Ymm];
end

function T = localElementsToTable(raw)
    names = {'TriIndex','Node1','Node2','Node3','RegCode','Bx','By','B','A','J'};
    if ~isfield(raw, 'elements') || isempty(raw.elements)
        T = table('Size', [0, numel(names)], ...
            'VariableTypes', {'double','double','double','double','double','double','double','double','double','double'}, ...
            'VariableNames', names);
        return;
    end

    E = raw.elements;
    n = numel(E);

    tri = zeros(n,1); n1 = zeros(n,1); n2 = zeros(n,1); n3 = zeros(n,1);
    rc = zeros(n,1); bx = nan(n,1); by = nan(n,1); b = nan(n,1);
    a = nan(n,1); j = nan(n,1);

    for k = 1:n
        tri(k) = localToDouble(E(k).tri_index);
        n1(k)  = localToDouble(E(k).node_1);
        n2(k)  = localToDouble(E(k).node_2);
        n3(k)  = localToDouble(E(k).node_3);
        rc(k)  = localToDouble(E(k).reg_code);
        bx(k)  = localToDouble(E(k).bx);
        by(k)  = localToDouble(E(k).by);
        b(k)   = localToDouble(E(k).b);
        a(k)   = localToDouble(E(k).a);
        j(k)   = localToDouble(E(k).j);
    end

    T = table(tri, n1, n2, n3, rc, bx, by, b, a, j, ...
        'VariableNames', names);
end

function T = localNodesToTable(raw)
    names = {'NodeIndex','Xmm','Ymm'};
    if ~isfield(raw, 'nodes') || isempty(raw.nodes)
        T = table('Size', [0, 3], ...
            'VariableTypes', {'double','double','double'}, ...
            'VariableNames', names);
        return;
    end

    N = raw.nodes;
    n = numel(N);
    idx = zeros(n,1); x = nan(n,1); y = nan(n,1);

    for k = 1:n
        idx(k) = localToDouble(N(k).node_index);
        x(k) = localToDouble(N(k).x_mm);
        y(k) = localToDouble(N(k).y_mm);
    end

    T = table(idx, x, y, 'VariableNames', names);
end

function v = localToDouble(x)
    if isempty(x)
        v = NaN;
        return;
    end
    if ischar(x) || isstring(x)
        y = str2double(x);
        if isnan(y)
            v = NaN;
        else
            v = y;
        end
        return;
    end
    v = double(x);
end

function repoRoot = localRepoRoot()
    thisFile = mfilename('fullpath');
    p = fileparts(thisFile);  % Calc
    p = fileparts(p);         % JEET
    p = fileparts(p);         % mlxperPJT
    p = fileparts(p);         % eMach
    p = fileparts(p);         % EveryMotor
    repoRoot = string(p);
end

function pythonExe = localDefaultPythonExe()
    envPython = "c:/Users/user/.ansys_python_venvs/pyMotorEnv_310/Scripts/python.exe";
    if isfile(envPython)
        pythonExe = envPython;
    else
        pythonExe = "python";
    end
end

function cacheDir = localDefaultCacheDir()
    cacheDir = fullfile(char(localRepoRoot()), 'data', 'emach data', 'mes_cache');
end

function p = localMakeCacheTxtPath(mesPath, firstStep, finalStep, cacheDir)
    [~, stem, ~] = fileparts(char(mesPath));
    tag = sprintf('%s_fs%d_fe%d', stem, round(firstStep), round(finalStep));
    tag = regexprep(tag, '[^A-Za-z0-9._-]', '_');
    p = string(fullfile(char(cacheDir), [tag, '.txt']));
end

function cmd = localBuildBridgeCommand(pythonExe, repoRoot, inputPath, outJson, motArg, stepArg, firstStep, finalStep)
    bridgePy = fullfile(char(repoRoot), 'eMach', 'tools', 'motorCAD', 'pyMCAD', 'matlab_bridge.py');
    if ~isfile(bridgePy)
        error('Python bridge module file not found: %s', bridgePy);
    end

    cmd = sprintf(['"%s" "%s" magnetic_from_file ' ...
                   '--repo-root "%s" --input "%s" --out-json "%s" --mot-path "%s" --step "%s" --first-step %d --final-step %d'], ...
                  char(pythonExe), bridgePy, char(repoRoot), char(inputPath), char(outJson), char(motArg), char(stepArg), round(firstStep), round(finalStep));
end
