function mcad=callMCAD(pyMCAD)
if nargin==1
    strcmp(pyMCAD,'pyMCAD')
    pymotorcad = py.importlib.import_module('ansys.motorcad.core');
    mcad = pymotorcad.MotorCADCompatibility();
else
mcad=actxserver('motorcad.appautomation');
end
end
