function inputobj = rawPsiDataPost(inputobj)
%From MotorCAD Lab Calculation extract the SaturationModel of 30 Point
%   
% currentVec from maxCurrent
% 
% define struct instead of properties change to class
inputobj.ModelParameters_MotorLAB.PsiDModel_Lab=[];
inputobj.ModelParameters_MotorLAB.PsiQModel_Lab=[];


mcad = actxserver('MotorCAD.AppAutomation');
proj=strcat(inputobj.file_path,'\',inputobj.file_name,'.mot');
refProj=strcat(inputobj.file_path,'\',inputobj.refFile,'.mot');

if exist(proj, 'file') ~= 2
    mcad.LoadFromFile(refProj);
    [success,inputobj.ArmatureConductor_Temperature]=invoke(mcad,'GetVariable','ArmatureConductor_Temperature');
    [success,inputobj.Magnet_Temperature]=invoke(mcad,'GetVariable','Magnet_Temperature');
    [success,inputobj.Shaft_Temperature]=invoke(mcad,'GetVariable','Shaft_Temperature');
    [success,inputobj.Bearing_Temperature_R]=invoke(mcad,'GetVariable','Bearing_Temperature_R');
    [success,inputobj.Bearing_Temperature_F]=invoke(mcad,'GetVariable','Bearing_Temperature_F');
    [success,inputobj.Airgap_Temperature]=invoke(mcad,'GetVariable','Airgap_Temperature');
    mcad.SaveToFile(proj); % 파일 생성

    inputobj.ArmatureConductor_Temperature=    inputobj.ArmatureConductor_Temperature+20;
    inputobj.Magnet_Temperature=    inputobj.Magnet_Temperature+20;
    inputobj.Shaft_Temperature=    inputobj.Shaft_Temperature+20;
    inputobj.Bearing_Temperature_R=    inputobj.Bearing_Temperature_R+20;
    inputobj.Bearing_Temperature_F=    inputobj.Bearing_Temperature_F+20;
    inputobj.Airgap_Temperature=inputobj.Airgap_Temperature+20;
    % 파일이 없는 경우
    mcad.SaveToFile(proj); % 파일 생성
    mcad.LoadFromFile(proj);
%     mcad.ClearModelBuild_Lab();
   
    mcad.SetVariable('ArmatureConductor_Temperature', inputobj.ArmatureConductor_Temperature);
    mcad.SetVariable('Magnet_Temperature', inputobj.Magnet_Temperature);
    mcad.SetVariable('Shaft_Temperature', inputobj.Shaft_Temperature);
    mcad.SetVariable('Bearing_Temperature_R', inputobj.Bearing_Temperature_R);
    mcad.SetVariable('Bearing_Temperature_F', inputobj.Bearing_Temperature_F);
    mcad.SetVariable('Airgap_Temperature', inputobj.Airgap_Temperature);
    mcad.BuildModel_Lab();
    mcad.SaveToFile(); % 파일 생성

%     mcad.Quit()
end
mcad.LoadFromFile(proj);

NcurrentVec=6;
NphaseVec=5;
inputobj.ModelParameters_MotorLAB.PsiDModel_Lab=[];
inputobj.ModelParameters_MotorLAB.PsiQModel_Lab=[];
motorLABFieldsNames=fieldnames(inputobj.ModelParameters_MotorLAB);
%% Lab Calc Temperature Import
[success,inputobj.ArmatureConductor_Temperature]=invoke(mcad,'GetVariable','ArmatureConductor_Temperature');
[success,inputobj.Magnet_Temperature]=invoke(mcad,'GetVariable','Magnet_Temperature');
[success,inputobj.Shaft_Temperature]=invoke(mcad,'GetVariable','Shaft_Temperature');
[success,inputobj.Bearing_Temperature_R]=invoke(mcad,'GetVariable','Bearing_Temperature_R');
[success,inputobj.Bearing_Temperature_F]=invoke(mcad,'GetVariable','Bearing_Temperature_F');
[success,inputobj.Airgap_Temperature]=invoke(mcad,'GetVariable','Airgap_Temperature');




% 1:length(motorLABFieldsNames)
[success,charPsiDModel_Lab]=invoke(mcad,'GetVariable',motorLABFieldsNames{1});
newStr = split(charPsiDModel_Lab,':');
xy=cell2mat(newStr');
[A,n] = sscanf(xy,'%f');
PsiDModel_Lab = reshape(A,[NphaseVec,NcurrentVec]);
PsiDModel_Lab=PsiDModel_Lab';
size(PsiDModel_Lab)
[success,charPsiQModel_Lab]=invoke(mcad,'GetVariable',motorLABFieldsNames{2});
newStr = split(charPsiQModel_Lab,':');
xy=cell2mat(newStr');
[A,n] = sscanf(xy,'%f');
PsiQModel_Lab = reshape(A,[NphaseVec,NcurrentVec]);
PsiQModel_Lab=PsiQModel_Lab';
size(PsiQModel_Lab)
inputobj.ModelParameters_MotorLAB.PsiDModel_Lab=PsiDModel_Lab;
inputobj.ModelParameters_MotorLAB.PsiQModel_Lab=PsiQModel_Lab;

end