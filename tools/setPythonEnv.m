% pyenv('Version', ... 
%             'C:\Users\KDH2018-PC\anaconda3\envs\py38_pcan151\python.exe', ... 
%             'ExecutionMode','InProcess') 

% pyenv('Version', ... 
%             'C:\Program Files\JMAG-Designer22.2\python3.8\python.exe', ... 
%             'ExecutionMode','InProcess') 

function setPythonEnv(python2call)
pe=pyenv;
if strcmp(python2call,'mcad')
    if pe.Status == 'NotLoaded'
    pyenv(ExecutionMode="OutOfProcess",Version='C:\ANSYS_Motor-CAD\2024_1_3\Python\Python\python.exe');
    end
elseif strcmp(python2call,'jmag')
pyenv('Version', 'C:\ANSYS_Motor-CAD\2023_2_1\Python\Python\python.exe');
elseif strcmp(python2call,'pyleecan')
pyenv('Version', 'C:\ANSYS_Motor-CAD\2023_2_1\Python\Python\python.exe');
end

end
