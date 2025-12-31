mcad=callMCAD();
% 220kW Mtr EM & Thermal
KJMMOTFilePath="E:\KDH\KJS\251114_C67_test_Moa.mot";
mcad.LoadFromFile(KJMMOTFilePath);
ActiveXParametersStruct=getMcadActiveXTableFromMotFile(KJMMOTFilePath);


checkDependencyInSubfolders('getMCADLabDataFromMotFile')'



%[appendix]{"version":"1.0"}
%---
%[metadata:view]
%   data: {"layout":"inline"}
%---
