function out = loadMESAllStepsViaPythonForMATLAB(mesPath, varargin)
% loadMESAllStepsViaPythonForMATLAB
% Wrapper around loadMESviaPythonForMATLAB to collect multi-step results.
%
% Example:
%   Dall = loadMESAllStepsViaPythonForMATLAB(mesPath, ...
%       'MotPath', motPath, 'UseCache', true, 'FirstStep', 1, 'FinalStep', 45);
%   k = find([Dall.ByStep.Step] == 10, 1);
%   bx_step10 = Dall.ByStep(k).Bx;
%
% Name-Value options:
%   PythonExe, MotPath, FirstStep, FinalStep, UseCache, CacheDir, RepoRoot, KeepJson, PreferPostprocTxt
%   StepList : explicit step list to fetch (default: [] -> use available steps in range)
% Note:
%   This function uses one Python bridge call (ReturnAllSteps=true) and
%   filters requested steps in MATLAB to avoid per-step bridge overhead.

    p = inputParser;
    addRequired(p, 'mesPath', @(x) ischar(x) || isstring(x));
    addParameter(p, 'PythonExe', localDefaultPythonExeWrap(), @(x) ischar(x) || isstring(x));
    addParameter(p, 'MotPath', "", @(x) ischar(x) || isstring(x));
    addParameter(p, 'FirstStep', 1, @(x) isnumeric(x) && isscalar(x));
    addParameter(p, 'FinalStep', 45, @(x) isnumeric(x) && isscalar(x));
    addParameter(p, 'UseCache', true, @(x) islogical(x) || isnumeric(x));
    addParameter(p, 'CacheDir', localDefaultCacheDirWrap(), @(x) ischar(x) || isstring(x));
    addParameter(p, 'RepoRoot', localRepoRootWrap(), @(x) ischar(x) || isstring(x));
    addParameter(p, 'KeepJson', false, @(x) islogical(x) || isnumeric(x));
    addParameter(p, 'PreferPostprocTxt', true, @(x) islogical(x) || isnumeric(x));
    addParameter(p, 'StepList', [], @(x) isempty(x) || isnumeric(x));
    parse(p, mesPath, varargin{:});

    firstStep = double(p.Results.FirstStep);
    finalStep = double(p.Results.FinalStep);

    commonArgs = {
        'PythonExe', p.Results.PythonExe, ...
        'MotPath', p.Results.MotPath, ...
        'FirstStep', p.Results.FirstStep, ...
        'FinalStep', p.Results.FinalStep, ...
        'UseCache', p.Results.UseCache, ...
        'CacheDir', p.Results.CacheDir, ...
        'RepoRoot', p.Results.RepoRoot, ...
        'PreferPostprocTxt', p.Results.PreferPostprocTxt, ...
        'KeepJson', p.Results.KeepJson ...
    };

    base = loadMESviaPythonForMATLAB(mesPath, commonArgs{:}, 'StepKey', [], 'ReturnAllSteps', true);
    available = reshape(double(base.StepKeys), 1, []);

    if isempty(p.Results.StepList)
        targetSteps = available(available >= firstStep & available <= finalStep);
        if isempty(targetSteps)
            targetSteps = available;
        end
    else
        requested = unique(reshape(double(p.Results.StepList), 1, []), 'stable');
        targetSteps = requested(ismember(requested, available));
    end

    byStep = base.ByStep;
    if ~isempty(byStep)
        allBySteps = reshape(double([byStep.Step]), 1, []);
        keepMask = ismember(allBySteps, targetSteps);
        byStep = byStep(keepMask);
    end

    out = base;
    out.RequestedSteps = reshape(targetSteps, [], 1);
    out.ByStep = byStep;
end

function repoRoot = localRepoRootWrap()
    thisFile = mfilename('fullpath');
    p = fileparts(thisFile);  % Calc
    p = fileparts(p);         % JEET
    p = fileparts(p);         % mlxperPJT
    p = fileparts(p);         % eMach
    p = fileparts(p);         % EveryMotor
    repoRoot = string(p);
end

function pythonExe = localDefaultPythonExeWrap()
    envPython = "c:/Users/user/.ansys_python_venvs/pyMotorEnv_310/Scripts/python.exe";
    if isfile(envPython)
        pythonExe = envPython;
    else
        pythonExe = "python";
    end
end

function cacheDir = localDefaultCacheDirWrap()
    cacheDir = fullfile(char(localRepoRootWrap()), 'data', 'emach data', 'mes_cache');
end
