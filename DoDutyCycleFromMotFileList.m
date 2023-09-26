function DoDutyCycleFromMotFileList(motFileList4Weight,numPorts)
readMotFileList=motFileList4Weight;
% numPorts=6;
clear spmdIndex
delete(gcp('nocreate'));  % 사전에 실행 중인 병렬 풀 있을까봐 끄고 시작
parpool(numPorts);  % 병렬 풀 생성, default가 Processes, Threads로 하면 에러
spmd
mcad(spmdIndex) = actxserver('motorcad.appautomation');
mcad(spmdIndex).SetVariable("MessageDisplayState",2)

lastPortCaseIndex=double(int32(length(readMotFileList)/numPorts));
for portCaseIndex = 1:1:lastPortCaseIndex
    i = ((spmdIndex-1)*lastPortCaseIndex)+portCaseIndex;
    BuildScaledMotFilePath=readMotFileList{i};
%     BuildScaledMotFilePath=readMotFileList{i};
    [FileDir,MotFileName,FileExt]=fileparts(BuildScaledMotFilePath);
    LabMatFileDir=fullfile(FileDir,MotFileName,'Lab');
    SatuMapFilePath = fullfile(LabMatFileDir,[MotFileName,'SatuMapExport.mat']);      
%     [MotorCADGeo,SatuMapData,LabBuildingData]=devExportSatuMapFromMCADLabModel(SatuMapFilePath,mcad(spmdIndex),0);
%     [SatuMapTable,SatuMapInfo]=createTableFromMCADSatuMapStr(SatuMapData);
%     [ScaledMachineData,ScaledSatuMapTable] = devScaleTablebyStiepetic(Factor,SatuMapTable,MotorCADGeo);
% BuildScaledMotFilePath=fullfile(ScaledBuildDir,['ScaleBuildModel',MotFileName],['ScaleBuildModel',MotFileName,FileExt]);
    if isfile(BuildScaledMotFilePath)    
    mcad(spmdIndex).LoadFromFile(BuildScaledMotFilePath)
    end
    [~,BuildCheck]=mcad(spmdIndex).GetModelBuilt_Lab();
    if BuildCheck==0
    mcad(spmdIndex).BuildModel_Lab();
    mcad(spmdIndex).SaveToFile(BuildScaledMotFilePath);
    end
    MachineData=tempDefMCADMachineData4Scaling(mcad(spmdIndex));

    % settingLabBuildTable = defMcadLabBuildSetting()    
    labDriveSettingTable=defMcadLabCalcSetting(); % 이게 잘안된것도 있네    
    mcad(spmdIndex).SetVariable("CurrentSpec_MotorLAB",0);
    labDriveSettingTable=updateMcadTableVariable(labDriveSettingTable,"Imax_MotorLAB",900);

     
%     updateMcadTableVariable(labDriveSettingTable,"Imax_RMS_MotorLAB",900);
    setMcadTableVariable(labDriveSettingTable,mcad(spmdIndex));
    
            % Vehicle Setting 기어비 변경 
    TeslaSPlaidDutyCycleTable=defMcadDutyCycleSetting;
    setMcadTableVariable(TeslaSPlaidDutyCycleTable,mcad(spmdIndex));
    RefGearRatio = findMcadTableVariableFromAutomationName(TeslaSPlaidDutyCycleTable, 'N_d_MotorLAB');
    mcad(spmdIndex).SetVariable('N_d_MotorLAB',3);
    mcad(spmdIndex).CalculateDutyCycle_Lab();
    
    mcad(spmdIndex).SaveToFile(BuildScaledMotFilePath);
end
end
end