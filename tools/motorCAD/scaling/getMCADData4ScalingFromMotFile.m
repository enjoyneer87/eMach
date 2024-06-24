function [BuildingData,filteredLabTable4Scaling]=getMCADData4ScalingFromMotFile(MotFilePath)
%% 데이터 가져오기
ActiveXParametersStruct = getMcadActiveXTableFromMotFile(MotFilePath);

% motcelldata=data;
% splitMotDataStruct = splitDataByMCADcategory(motcelldata);
% mcad=callMCAD

%% Machine Data & Build Data
MachineData                                         = getMcadMachineDataFromMotFile(ActiveXParametersStruct)    ;
BuildingData                                        = getMCADBuildingDataFromMotFile(ActiveXParametersStruct);
MachineData                                         = mergeSubStructs(MachineData);
[BuildingData.MotorCADGeo,b]                        = mergeStructs(BuildingData.MotorCADGeo,MachineData);
%% HairPin
if BuildingData.MotorCADGeo.Armature_CoilStyle==1
BuildingData.MotorCADGeo.LabMaxRMSCurrentDensity    = calcCurrentDensity(BuildingData.MotorCADGeo.Imaxrms,double(BuildingData.MotorCADGeo.ParallelPaths),double(BuildingData.MotorCADGeo.NumberStrandsHand),BuildingData.MotorCADGeo.ArmatureConductorCSA);
%% 환선 
elseif  BuildingData.MotorCADGeo.Armature_CoilStyle==0
BuildingData.T0data.ResistanceActivePart            = BuildingData.Resistance_MotorLAB-BuildingData.EndWindingResistance_Lab;
end
%% filteredTable
filteredLabTable4Scaling           = getMCADLabDataFromMotFile(ActiveXParametersStruct);
filteredLabTable4Scaling           = reNameLabTable2LabLink(filteredLabTable4Scaling);    

end