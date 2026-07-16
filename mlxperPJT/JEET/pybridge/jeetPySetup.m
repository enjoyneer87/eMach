function jeetPySetup(pythonExe)
%JEETPYSETUP  Configure the MATLAB->Python bridge for jeet_acloss_rbf.
%
%   jeetPySetup()            uses the default pyMotorEnv_310 interpreter
%   jeetPySetup(pythonExe)   uses a custom python.exe
%
%   Must be called once per MATLAB session BEFORE any other jeet* call.
%   (pyenv can only be set before Python is first loaded.)

if nargin < 1
    pythonExe = ['c:\Users\user\.ansys_python_venvs\pyMotorEnv_310' ...
                 '\Scripts\python.exe'];
end

pe = pyenv;
if pe.Status == "NotLoaded"
    pyenv('Version', pythonExe);
elseif ~strcmpi(char(pe.Executable), pythonExe)
    warning('jeetPySetup:alreadyLoaded', ...
        ['Python already loaded from %s. Restart MATLAB to switch ' ...
         'interpreters.'], char(pe.Executable));
end

% make the package importable
toolsDir = 'D:\KangDH\EveryMotor\eMach\tools';
sysPath = py.sys.path;
if ~any(cellfun(@(p) strcmpi(char(p), toolsDir), cell(sysPath)))
    insert(sysPath, int32(0), toolsDir);
end

% headless matplotlib inside MATLAB
py.importlib.import_module('matplotlib');
py.matplotlib.use('Agg');

py.importlib.import_module('jeet_acloss_rbf');
fprintf('[jeetPySetup] jeet_acloss_rbf ready (python: %s)\n', ...
    char(pyenv().Executable));
end
