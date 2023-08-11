
% 해석이 돈 Case 만 체크
% New Folder and File Address
% numCases = height(DoEStruct.DoEInputTable);
% numCases=2

% load("testDoeTable.mat")
vehicleData=load("TeslaSPlaid.mat");                             % TeslaPlaid Define
vehicleData=vehicleData.TeslaPlaid;
vehiclePowerCurve=load("TeslaSPlaidPowerCurveDigitizer.mat");   % TeslaPowerCurve Define
vehiclePowerCurve=vehiclePowerCurve.TeslaPowerCurve;
labCalcSettingTable            = defMcadLabCalcSetting();

DoEStruct=struct();
DoEStruct.DoEInputTable=SampleTable;
DoEStruct.DoESimulCheckTable=createDoECheckTable(refMotFilePath,SampleTable);
%% 워커할당
parpool(numPorts);  % 병렬 풀 생성, default가 Processes, Threads로 하면 에러

spmd



%% 모터캐드 할당
mcad(spmdIndex) = actxserver('motorcad.appautomation');
%% Export 효율맵 & 동력 특성
% spmdIndex  각 워커의 index
% numCases
% numPorts   워커의 개수
%% DoETable 반복
for portCaseIndex = 1:1:(numCases/numPorts)
    % portCaseIndex  : 각워커별로 할당된 CaseIndex
    % caseNum은      : 전체 caseNumbering에서의 현재 caseIndex
    caseNum = ((spmdIndex-1)*(numCases/numPorts))+portCaseIndex;

    % 경로
    motFileDir =DoEStruct.DoESimulCheckTable.DesignFolderPath(caseNum);
    motFileName=DoEStruct.DoESimulCheckTable.motFileName(caseNum);
    
    % Update Variable 전류 및 셋팅
    newValue    =   DoEStruct.DoEInputTable.Imax_MotorLAB(caseNum);
    DesignLabCalcSettingTable   =   updateMcadTableVariable(labCalcSettingTable,'Imax_MotorLAB',newValue);
    DesignLabCalcSettingTable   =   updateMcadTableVariable(DesignLabCalcSettingTable,'TurnsCalc_MotorLAB',0.5);

    % Setting Variable &calc MagLab
    % [TC]Build가 된지를 확인할필요
    BasePointOutput             = calcMotorCADLabBasePoint(mcad(spmdIndex), motFileDir,motFileName , DesignLabCalcSettingTable);
    vehiclePerformData = calcVehiclePerformance(vehiclePowerCurve);   %vehiclePerformData define

    % tempPlot
    tempPlotEfficiencyMapVehiclePerfom(caseNum,DoEStruct,vehicleData,BasePointOutput,vehiclePerformData);

    % PNG로 저장 
    % 현재 떠 있는 모든 figure의 handle을 얻어옴
    folderPath =fullfile(motFileDir,motFileName,'Lab','PNG');
    mkdir(folderPath);
    saveFigures2png(folderPath);
    if portCaseIndex~=(numCases/numPorts)
        close all
    end
end

%% SPMD 종료
end

delete(gcp);

clear("caseNum", "motFileDir","motFileName","mcad","BasePointOutput","DesignLabCalcSettingTable","vehiclePerformData","newValue","portCaseIndex","vehicleData","vehiclePowerCurve","labCalcSettingTable","DoEStruct","folderPath")