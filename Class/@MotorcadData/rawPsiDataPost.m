function inputobj = fcnRawPsiDataPost(inputobj)
%From MotorCAD Lab Calculation extract the SaturationModel of 30 Point
%   
% currentVec from maxCurrent
% 
% define struct instead of properties change to class
inputobj.ModelParameters_MotorLAB.PsiDModel_Lab=[];
inputobj.ModelParameters_MotorLAB.PsiQModel_Lab=[];


mcad = actxserver('MotorCAD.AppAutomation');
proj=strcat(inputobj.file_path,'\',inputobj.file_name,'.mot');
mcad.LoadFromFile(proj);

NcurrentVec=6;
NphaseVec=5;
inputobj.ModelParameters_MotorLAB.PsiDModel_Lab=[];
inputobj.ModelParameters_MotorLAB.PsiQModel_Lab=[];
motorLABFieldsNames=fieldnames(inputobj.ModelParameters_MotorLAB);

% 1:length(motorLABFieldsNames)
[success,charPsiDModel_Lab]=invoke(mcad,'GetVariable',motorLABFieldsNames{1});
newStr = split(charPsiDModel_Lab,':');
xy=cell2mat(newStr');
[A,n] = sscanf(xy,'%f');
PsiDModel_Lab = reshape(A,[NphaseVec,NcurrentVec]);
PsiDModel_Lab=PsiDModel_Lab'
size(PsiDModel_Lab)
[success,charPsiQModel_Lab]=invoke(mcad,'GetVariable',motorLABFieldsNames{2});
newStr = split(charPsiQModel_Lab,':');
xy=cell2mat(newStr');
[A,n] = sscanf(xy,'%f');
PsiQModel_Lab = reshape(A,[NphaseVec,NcurrentVec]);
PsiQModel_Lab=PsiQModel_Lab'
size(PsiQModel_Lab)
inputobj.ModelParameters_MotorLAB.PsiDModel_Lab=PsiDModel_Lab;
inputobj.ModelParameters_MotorLAB.PsiQModel_Lab=PsiQModel_Lab;

end