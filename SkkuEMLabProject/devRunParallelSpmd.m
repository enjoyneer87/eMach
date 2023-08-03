% function runParallelSpmd(refMotFilePath, NumberOfPorts, NumberOfCases, DoETable, FixVariableTable, message_on)
% 2023.8.2 수정사항
% * 멈췄다가 다시 돌때 기능 점검
%     * Lab으로 Build 여부 체크
%     * Lab Folder와 parent Path가 다르면 clear
%     * DoeTable 저장
% *
OrderInPort = 1;
%% 병렬풀 초기화 및 배치
delete(gcp('nocreate'));  % 사전에 실행 중인 병렬 풀 있을까봐 끄고 시작
parpool(NumberOfPorts);  % 병렬 풀 생성, default가 Processes, Threads로 하면 에러
% mcad

%% spmd loop : numPorts 병렬 실행
time_before_spmd = dispDateTime(message_on, NumberOfPorts, NumberOfCases);

% spmd

    mcad=actxserver('motorcad.appautomation');
    mcad.SetVariable('MessageDisplayState', 2); % 모든 메시지를 별도의 창에 표시하도록 설정 - 주의: 이로 인해 파일 저장, 데이터 덮어쓰기 등 중요한 팝업 메시지가 비활성화될 수 있으니 주의하시기 바랍니다.
    mcad.LoadFromFile(refMotFilePath);
    screens = {'Radial','StatorWinding'};

    for OrderInPort = 1:1:(NumberOfCases/NumberOfPorts)
    %% Path 생성
        % parallel case number seperation
        CaseNumber = (spmdIndex-1)*(NumberOfCases/NumberOfPorts)+OrderInPort;
        % New Folder  Name & Path
        parts               = strsplit(refMotFilePath, filesep);
        parentPath          = fullfile(parts{1:end-2});
        [~,name,~]          = fileparts(refMotFilePath);  
        newDesignFolderName = [name, '_Design', sprintf('%03d', CaseNumber)];
        newFolderPath       = fullfile(parentPath, 'DOE', newDesignFolderName);
        % New File Name
        parts               = strsplit(newFolderPath, filesep);
        newFileName         =strcat(parts{end}, '.mot');
        newMotFilePath      = fullfile(newFolderPath, newFileName);
        % Check Build
        parts               =strsplit(newMotFilePath, filesep);        
        newMotSimulPath     =fullfile(newFolderPath,newDesignFolderName);
        resultCheckFolder   =fullfile(newMotSimulPath,'Lab');  % 해석 완료된 모델 체크용 
    %% [Lab]Result Check/Build Check
       if exist(resultCheckFolder,"dir") == false            % false 경우 (Lab Folder가 없으면)    
        mcad.LoadFromFile(newMotFilePath);                   % Load File
        mcad.ClearModelBuild_Lab();                           
        [~, isBuildSucceeded]=mcad.GetModelBuilt_Lab();  % Motorcar 자체 Build Check            
            % 이중 check  
            if isBuildSucceeded==0                      % Build 안되어 있으면 0, 되면 1이라서 if문 나감
                mcad.BuildModel_Lab();  % isBuildSucceeded==0  일때 빌드

                mcad.SaveToFile(newMotFilePath);  % 파일 재저장   
            end
       end

    %% mcad.BuildModel_Lab();  % 빌드
                    [Success, isBuildSucceeded]=mcad.GetModelBuilt_Lab();  % 모델 빌드 여부 체크
                    if isBuildSucceeded==1  % 빌드 돼있으면
                        mkdir(resultCheckFolder);  % 빌드 완료됨을 표시하는 폴더 생성
                    end
                    time_after=datetime;
                    if message_on>0
                        disp(['case ',num2str(CaseNumber),' (', num2str(OrderInPort), 'th in port ', num2str(spmdIndex),') build done'])
                        disp(['Time after build : ', char(time_after)])
                        disp(['Time cost of build : ', char(time_after-time_before)])
                    end
                    mcad.SaveToFile(newMotFilePath);  % 파일 재저장
                    
                    %% Radial, Axial, Winding Screenshoot 저장
                    for j = 1:numel(screens)
                        screenname = screens{j};
                        fileName = [newFolderPath, '\Pic_', screenname, '.png'];
                        mcad.SaveScreenToFile(screenname, fileName);
                    end
        if ~exist(resultCheckFolder, 'dir')
            if exist(newFolderPath, 'dir')
                % 폴더 통체로 삭제하고 싶은데 잘 모르겠음
                if exist(newMotFilePath, 'file')
                    delete(newMotFilePath);
                    if message_on>1
                        disp('No result file delete')
                    end
                end
            else
                mkdir(newFolderPath);  % 폴더 생성
            end
            mcad.SaveToFile(newMotFilePath);  % 빌드 전 저장
            if message_on>1
                disp(['case ',num2str(CaseNumber),' new file save'])
            end
    %% Geometry Check
            mcad.CheckIfGeometryIsValid(1);  % check?

    %% Weigth Calc
            mcad.DoWeightCalculation();
            [~,o_Weight_Stat_Core]=mcad.GetVariable('Weight_Total_Stator_Lam');


    %%  Variable Setting
        % StatorVariable Struct
        devSetVariableFromTable(DoETable(OrderInPort,:))
        setMcadVariable(StatorVariable,mcad);
        setMcadVariable(RotorVariable,mcad);
        setMcadVariable(EtcVariable,mcad);
        % Winding
        setMcadVariable(settedConductorData,mcad);        
        % 형상 적용을 위한 저장
        validGeometry=mcad.CheckIfGeometryIsValid(1);  % Motor-CAD 자체 기능
        devMakeScreenGIFwithSetVariables(PNGFolder)
        mcad.SaveToFile(newMotFilePath);  
    %% Hair Pin 
    
        % Hairpin coil
        if validGeometry==1
          NewConductorData=calcConductorSize(settedConductorData, message_on);  % 현재 셋팅된 값 기반으로 copper 사이즈 계산
          setMcadVariable(NewConductorData,mcad);
        end  

    %% Build 
  
    % for 문 끝
    end  

    if message_on>0
        disp(['port ', num2str(spmdIndex), ' loop end'])
    end

    % 종료
    % invoke(mcad, 'Quit');
    % activeServers=0;

% spmd end
end
dispEndDateTime(message_on, NumberOfPorts, NumberOfCases, time_before_spmd);


%% 병렬 풀
% delete(gcp);

% end