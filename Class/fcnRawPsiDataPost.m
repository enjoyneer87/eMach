function [PsiDModel_Lab,PsiQModel_Lab] = fcnRawPsiDataPost(inputobj)
%From MotorCAD Lab Calculation extract the SaturationModel of 30 Point
%   
% currentVec from maxCurrent
% 

mcad = actxserver('MotorCAD.AppAutomation');
proj=strcat(inputobj.file_path,'\',inputobj.file_name,'.mot');
mcad.LoadFromFile(proj);

currentVec=5;
phaseVec=6;

inputobj.ModelParameters_MotorLAB.PsiDModel_Lab=[];
inputobj.ModelParameters_MotorLAB.PsiQModel_Lab=[];
motorLABFieldsNames=fieldnames(inputobj.ModelParameters_MotorLAB);

% 1:length(motorLABFieldsNames)
[success,charPsiDModel_Lab]=invoke(mcad,'GetVariable',motorLABFieldsNames{1});
newStr = split(charPsiDModel_Lab,':');
xy=cell2mat(newStr');
[A,n] = sscanf(xy,'%f')
PsiDModel_Lab = reshape(A,[currentVec,phaseVec]);

[success,charPsiQModel_Lab]=invoke(mcad,'GetVariable',motorLABFieldsNames{2});
newStr = split(charPsiQModel_Lab,':');
xy=cell2mat(newStr');
[A,n] = sscanf(xy,'%f');
PsiQModel_Lab = reshape(A,[currentVec,phaseVec]);

end