% File created on 12/01/2023 ¿ÀÈÄ 5:57:37
% This file is in the format of Matlab script
% Only includes changed user defined variables
mcad = actxserver('MotorCAD.AppAutomation');
ExportResults('Transient', filename)
invoke(mcad,'Quit');
