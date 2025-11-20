% pyenv('Version', ... 
%             'C:\Users\KDH2018-PC\anaconda3\envs\py38_pcan151\python.exe', ... 
%             'ExecutionMode','InProcess') 

% pyenv('Version', ... 
%             'C:\Program Files\JMAG-Designer22.2\python3.8\python.exe', ... 
%             'ExecutionMode','InProcess') 

function setPythonEnv(python2call)
pe=pyenv;
% MCADVersion='C:\ANSYS_Motor-CAD\2024_1_3\Python\Python\python.exe';
MCADVersion='C:\Ansys_Motor-CAD\2025_1_1\Python\Python\pythonw.exe';

if strcmp(python2call,'mcad')
    if pe.Status == 'NotLoaded'
    pyenv(ExecutionMode="OutOfProcess",Version=MCADVersion);

    end
elseif strcmp(python2call,'jmag')
pyenv('Version', 'C:\Program Files\JMAG-Designer23.1\python3.8\python.exe');

elseif strcmp(python2call,'pyleecan')
pyenv('Version', 'C:\ANSYS_Motor-CAD\2023_2_1\Python\Python\python.exe');
elseif strcmp(python2call,'gmsh')
pyenv('Version', 'Z:\01_Codes_Projects\git_fork_emach\.venv\Scripts\pythonw.exe')
end

end
