function inputobj = exportRawLossMap(inputobj)
%From MotorCAD Lab Calculation extract the SaturationModel of 30 Point
% inputobj = MotorcadData  obj
% currentVec from maxCurrent
% 
% define struct instead of properties change to class
inputobj.LossParameters_MotorLAB=[]
inputobj.ModelParameters_MotorLAB=[]

inputobj.LossParameters_MotorLAB.RawLossMap.LossModel_Is_Lab=[];
inputobj.LossParameters_MotorLAB.RawLossMap.LossModel_Gamma_Lab=[];
inputobj.LossParameters_MotorLAB.RawLossMap.FeHysLossArray_MotorLAB=[];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossBackIronHy_MotorLAB=[];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossToothHy_MotorLAB=[];

inputobj.LossParameters_MotorLAB.RawLossMap.FeLossRotorPoleHy_MotorLAB=[];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossRotorHy_MotorLAB=[];

inputobj.LossParameters_MotorLAB.RawLossMap.FeEddyLossArray_MotorLAB=[];

inputobj.LossParameters_MotorLAB.RawLossMap.FeLossBackIronEd_MotorLAB=[];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossToothEd_MotorLAB=[];

inputobj.LossParameters_MotorLAB.RawLossMap.FeLossRotorEd_MotorLAB=[];
inputobj.LossParameters_MotorLAB.RawLossMap.FeLossRotorPoleEd_MotorLAB=[];

inputobj.LossParameters_MotorLAB.RawLossMap.MagLossArray_MotorLAB   =[];

inputobj.LossParameters_MotorLAB.RawLossMap.FEALossMap_RefSpeed_Lab=[];


inputobj.LossParameters_MotorLAB.FeLossUnit='[Watts]';

inputobj.ModelParameters_MotorLAB.RawLossMap.LossModel_AC_Lab=[]



FieldsNamesLossModelLAB=fieldnames(inputobj.LossParameters_MotorLAB.RawLossMap);
FieldsNamesModelParameters=fieldnames(inputobj.ModelParameters_MotorLAB.RawLossMap);

%%
mcad = actxserver('MotorCAD.AppAutomation');
proj=strcat(inputobj.file_path,'\',inputobj.file_name,'.mot');
refProj=strcat(inputobj.file_path,'\',inputobj.refFile,'.mot');

mcad.LoadFromFile(proj);

[success,ModelBuildPoints_Current_Lab]=mcad.GetVariable('ModelBuildPoints_Current_Lab')
[success,ModelBuildPoints_Gamma_Lab]=mcad.GetVariable('ModelBuildPoints_Gamma_Lab')


[success,FEALossMap_RefSpeed_Lab]=mcad.GetVariable('FEALossMap_RefSpeed_Lab')
NcurrentVec=ModelBuildPoints_Current_Lab;
NphaseVec=ModelBuildPoints_Gamma_Lab;
inputobj.LossParameters_MotorLAB.RawLossMap.FEALossMap_RefSpeed_Lab=FEALossMap_RefSpeed_Lab;
%% exportRawLossModel from .Mot file to MotorcadData  obj

for fieldIndex=1:length(FieldsNamesLossModelLAB)-2
    [success,charTypeData]=mcad.GetVariable(FieldsNamesLossModelLAB{fieldIndex});
    newStr = split(charTypeData,':');
    xy=cell2mat(newStr');
    [A,n] = sscanf(xy,'%f');
    inputobj.LossParameters_MotorLAB.RawLossMap.(FieldsNamesLossModelLAB{fieldIndex}) = (reshape(A,[NphaseVec,NcurrentVec]))';
    size(inputobj.LossParameters_MotorLAB.RawLossMap.(FieldsNamesLossModelLAB{fieldIndex}))
end

    [success,charTypeData]=mcad.GetVariable(FieldsNamesLossModelLAB{length(FieldsNamesLossModelLAB)-1});

%%


