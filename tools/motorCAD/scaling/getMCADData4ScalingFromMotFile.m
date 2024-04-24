function [BuildingData,filteredTable]=getMCADData4ScalingFromMotFile(MotFilePath)

%% 데이터 가져오기
ActiveXParametersStruct = getMcadActiveXTableFromMotFile(MotFilePath);

%% Machine Data & Build Data
MachineData                                         = getMcadMachineDataFromMotFile (ActiveXParametersStruct)    ;
BuildingData                                        = getMCADBuildingDataFromMotFile(ActiveXParametersStruct);
MachineData                                         = mergeSubStructs(MachineData);
[BuildingData.MotorCADGeo,b]                        = mergeStructs(BuildingData.MotorCADGeo,MachineData);
BuildingData.MotorCADGeo.LabMaxRMSCurrentDensity    = calcCurrentDensity(BuildingData.MotorCADGeo.Imaxrms,double(BuildingData.MotorCADGeo.ParallelPaths),double(BuildingData.MotorCADGeo.NumberStrandsHand),BuildingData.MotorCADGeo.ArmatureConductorCSA);
BuildingData.T0data.ResistanceActivePart            = BuildingData.Resistance_MotorLAB-BuildingData.EndWindingResistance_Lab;

%% filteredTable
filteredTable           = getMCADLabDataFromMotFile(ActiveXParametersStruct);
filteredTable           = reNameLabTable2LabLink(filteredTable);    

end