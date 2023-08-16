
% 해석이 돈 Case 만 체크
%BuildListResult
% 덮어 씌울지 넘어갈지 선택하는 기능 추가필요
vehicleData=load("TeslaSPlaid.mat");                             % TeslaPlaid Define
vehicleData=vehicleData.TeslaPlaid;
vehicleData.N_d_MotorLAB=7.56;  %[TC] 범용성 증가 필요
TeslaPlaidCurve
% vehiclePowerCurve=load("TeslaSPlaidPowerCurveDigitizer.mat");   % TeslaPowerCurve Define
% vehiclePowerCurve=vehiclePowerCurve.TeslaPowerCurve;

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
    
    % BuildResultList
    buildMotFileName = findMatchedValueinCell(BuildListResult, caseNum,4,3);
    buildMotFileDirName = findMatchedValueinCell(BuildListResult, caseNum,4,2);

    % 경로
    motFileDir =    DoEStruct.DoESimulCheckTable.DesignFolderPath(caseNum);
    motFileName=    DoEStruct.DoESimulCheckTable.motFileName(caseNum);

    if ~isempty(buildMotFileName)


        motFileDir          = changeLastPartOfPath(motFileDir,buildMotFileDirName);
        motFileName         = buildMotFileName;

        DoEStruct.DoESimulCheckTable.DesignFolderPath(caseNum) = motFileDir;
        DoEStruct.DoESimulCheckTable.motFileName(caseNum)      = motFileName;
        
        %% 
        % DoeTable에 Imax_MotorLab있는지 Check
        targetTable=DoEStruct.DoEInputTable;
        if strcmp(targetTable.Properties.VariableNames,'Imax_MotorLAB')
            newValue    =   DoEStruct.DoEInputTable.Imax_MotorLAB(caseNum);
        else
            % [~,newValue]    =   mcad(spmdIndex).GetVariable('MaxModelCurrent_MotorLAB');
              newValue    = 900; %일괄적으로
        end        
   %% [TC] Update Variable  전류 및 셋팅 -LabProject 교수님 일단 적층, 전류고정 해서 자료 1) 적층, 전류 perturb하면서 자료2
        DesignLabCalcSettingTable   =   updateMcadTableVariable(labCalcSettingTable,'Imax_MotorLAB',newValue);
        % DesignLabCalcSettingTable   =   updateMcadTableVariable(DesignLabCalcSettingTable,'TurnsCalc_MotorLAB',0.5);
        DesignLabCalcSettingTable   =   updateMcadTableVariable(DesignLabCalcSettingTable,'"SpeedMax_MotorLAB"',25000);
    
        % Setting Variable &calc MagLab
        % [TC]Build가 된지를 확인할필요
        
        % initialMatFileDir       = fullfile(motFileDir, motFileName, 'Lab', 'MotorLAB_elecdata');
    %% elec Data가 있으면 넘어가도록
        MatFileList=findMatFiles(motFileDir)';
        elecMatFileList = contains(MatFileList, 'elecdata') & contains(MatFileList, 'm.mat');

        if ~any(elecMatFileList) 
            % BasePointOutput             = calcMotorCADLabBasePoint(mcad(spmdIndex), motFileDir,motFileName , DesignLabCalcSettingTable);
            BasePointOutput             = calcMotorCADLabBasePoint(mcad, motFileDir,motFileName , DesignLabCalcSettingTable);
            % vehiclePerformData          = calcVehiclePerformance(vehiclePowerCurve);   %vehiclePerformData define
            % [TC]tempPlot
              % make vehiclePerformData
            [matData,motorSplitStruct]=tempPlotEfficiencyMapVehiclePerfom(caseNum,DoEStruct,vehicleData,BasePointOutput,vehiclePerformData);
            %%  요구사양 만족 - 판단 알고리즘
            [smallPoint,vehiclePerformData]=tempCallDecideSimulationTargetPoint(matData,motorSplitStruct,dividedMotorCurve,vehiclePerformData);
            
            figure(6)
            scatter(BasePointOutput.BaseSpeed_modified,BasePointOutput.BaseTorque_modified)
            hold on
            scatter(BasePointOutput.FluxWeakeningSpeed_modified,BasePointOutput.FluxWeakeningTorque_modified)
        %% PNG가 있으면 넘어가도록          
            % PNG로 저장 
            % 현재 떠 있는 모든 figure의 handle을 얻어옴
            folderPath =fullfile(motFileDir,motFileName,'Lab','PNG');
            mkdir(folderPath);
            saveFigures2png(folderPath);
            close all
        end
        % if portCaseIndex~=(numCases/numPorts)
        % end
        % end
    else
       % Build 되지 않은 폴더이름 변경
       if exist(motFileDir,'dir')==7
          disp("Code Error")
       else           
           motFileDirName=getMotFileDirNameFromBuildList(BuildList,caseNum);
           motFileDir=changeLastPartOfPath(motFileDir,motFileDirName);
           % 경로 권한 추가
           addPathWithSubPath(motFileDir)
           % 변경할 폴더가 존재하면
           if exist(motFileDir,'dir')==7
              % 폴더 변경
              addString2PathName(motFileDir,'NotBuild');
              % Table변경
              DoEStruct.DoESimulCheckTable.DesignFolderPath(caseNum) = strcat(motFileDir,'NotBuild');
              disp([motFileDir,'will be changed Folder Name to '])
           end
       end
    end
end
    %% SPMD 종료
end
delete(gcp);

clear("caseNum", "motFileDir","motFileName","mcad","BasePointOutput","DesignLabCalcSettingTable","vehiclePerformData","newValue","portCaseIndex","folderPath","folderPath")