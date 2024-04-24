classdef MCADLabManager
    properties
        NumMCAD        % Motor-CAD 인스턴스의 수
        BuildList      % 처리할 Motor-CAD 파일 목록
        MCADInstances  % 생성된 Motor-CAD 인스턴스를 저장하는 Composite 객체
        %
        LabBuildSettingTable
        %
        DutyCycleCalcSettingTable
        %
        Magnetic_LabCalcSettingTable
        
    end

    methods
        function obj = MCADLabManager(numMCAD, buildList)
            % 생성자 함수
            obj.NumMCAD = numMCAD;
            obj.BuildList = buildList;
            obj.MCADInstances = [];
            % Build Setting
            obj.LabBuildSettingTable =[];
            % DutyCycle_Lab
            obj.DutyCycleCalcSettingTable=[];
            % Magnetic_Lab
            obj.Magnetic_LabCalcSettingTable=[];
        end

        function setupParallelPool(obj)
            % 병렬 풀 설정 및 Motor-CAD 인스턴스 사전 생성
            if isempty(gcp('nocreate'))
                parpool(obj.NumMCAD);
            end
            spmd(obj.NumMCAD)
                % 각 병렬 워커에서 Motor-CAD 인스턴스 생성
                mcad = actxserver('motorcad.appautomation');
                obj.MCADInstances{spmdIndex} = mcad;
            end
        end

        function processSLFEA(obj)
            % spmd 블록을 사용하여 기존 mcad 인스턴스에 새 작업을 수행
            if isempty(gcp('nocreate'))
                parpool(obj.NumMCAD);
            end
        
            % spmd 블록을 사용하여 파일 처리
            spmd(obj.NumMCAD)
                if isempty(obj.MCADInstances) || length(obj.MCADInstances) < spmdIndex || isempty(obj.MCADInstances{spmdIndex})
                    error('MCAD instance is not properly initialized for worker %d.', spmdIndex);
                end
                % 기존에 생성된 mcad 인스턴스를 사용
                mcad = obj.MCADInstances{spmdIndex};                
                % 각 워커가 처리할 파일의 범위 지정
                for idx = spmdIndex:spmdSize:length(obj.BuildList)
                    % SLFEA 관련 파일 로드 및 변수 설정
                    motFileData = obj.BuildList(idx);
                    mcad.LoadFromFile(motFileData.SLFEAMotFilePath);
                    mcad.SetVariable("MessageDisplayState", 2);
                    %SLLAW가 없으면
                    if isfield(motFileData,'SLLAWMotFilePath')
                       if ~isfile(motFileData.SLLAWMotFilePath)
                        mcad.SetVariable('AirgapDefinition', 1);
                        %% SLMachineData
                        setMcadVariable(motFileData.SLScaledMachineData, mcad);
                        %% SL Lab Building Setting
                        setMcadTableVariable(obj.LabBuildSettingTable,mcad);
                        % BuildingData.LabBuildData=defLabBuildData(mcad(1));
                        mcad.SetVariable("CurrentSpec_MotorLAB",0);
                        mcad.SetVariable("MaxModelCurrent_MotorLAB",max(motFileData.SLLabTable.Is));                         
                        % mcad.SetVariable("MaxModelCurrent_RMS_MotorLAB",max(motFileData.SLLabTable.Is));                         
                       end
                    end
                    % Build Lab
                    mcad.ClearModelBuild_Lab()
                    mcad.BuildModel_Lab()
                    mcad.SaveToFile(motFileData.SLFEAMotFilePath);
                end
            end
        end

        function processSLLAW(obj)
            % spmd 블록을 사용하여 기존 mcad 인스턴스에 새 작업을 수행
            if isempty(gcp('nocreate'))
                parpool(obj.NumMCAD);
            end
        
            % spmd 블록을 사용하여 파일 처리
            spmd(obj.NumMCAD)
                if isempty(obj.MCADInstances) || length(obj.MCADInstances) < spmdIndex || isempty(obj.MCADInstances{spmdIndex})
                    error('MCAD instance is not properly initialized for worker %d.', spmdIndex);
                end
                % 기존에 생성된 mcad 인스턴스를 사용
                mcad = obj.MCADInstances{spmdIndex};                
                % 각 워커가 처리할 파일의 범위 지정
                for idx = spmdIndex:spmdSize:length(obj.BuildList)
                    % SLLAW 관련 파일 로드 및 변수 설정
                    motFileData = obj.BuildList(idx);
                    mcad.LoadFromFile(motFileData.SLLAWMotFilePath);
                    mcad.SetVariable("MessageDisplayState", 2);
                    %SLLAW가 있으면 그냥 열어서      Lab만들기
                    %SLFEA가 없으면 SetVariable하고 Lab만들기
                    if isfield(motFileData,'SLFEAMotFilePath')
                       if ~isfile(motFileData.SLFEAMotFilePath)
                        mcad.SetVariable('AirgapDefinition', 1);
                        %% SLMachineData
                        setMcadVariable(motFileData.SLScaledMachineData, mcad);
                        %% SL Lab Building Setting
                        setMcadTableVariable(obj.LabBuildSettingTable,mcad);
                        % BuildingData.LabBuildData=defLabBuildData(mcad(1));
                        mcad.SetVariable("CurrentSpec_MotorLAB",0);
                        mcad.SetVariable("MaxModelCurrent_MotorLAB",max(motFileData.SLLabTable.Is));                         
                        % mcad.SetVariable("MaxModelCurrent_RMS_MotorLAB",max(motFileData.SLLabTable.Is));                         
                       end
                    end
                    %% - SCLaw 맵 구성 (땡겨오기)                       
                    ExportLabLinkTxtPath=makeLabLinkTXTFromLabTable(motFileData.SLLabTable,LabMatFileDir);
                    if contains(LabMatFileDir,'SLLAW')
                        [~,LabMatFileDir]=mcad.GetVariable('ResultsPath_MotorLAB');
                        [newLabTxtDir,DesignName,~]=fileparts(motFileData.SLLAWMotFilePath);
                        designNumber = extractDesignNumber(DesignName);
                        NewLabTxtPath=[newLabTxtDir,['\',designNumber,'SLLAW_LabLink.txt']];
                        movefile(ExportLabLinkTxtPath,NewLabTxtPath);
                    end
                    motFileData.ImportLabLinkTxtPath=NewLabTxtPath;
                    BuildData         =motFileData.BuildingData;                
                    ScaledMachineData =motFileData.SLScaledMachineData       ;      
                    LabLinkTxtPath    =motFileData.ImportLabLinkTxtPath      ;      
                    ImportExternalTXTLabModel(LabLinkTxtPath,BuildData,mcad,ScaledMachineData)
                    mcad.SaveToFile(motFileData.SLFEAMotFilePath);
                end
            end
        end
        % processFiles
        function processFiles(obj)
            % 병렬 풀이 이미 설정되었는지 확인
            if isempty(gcp('nocreate'))
                parpool(obj.NumMCAD);
            end
        
            % spmd 블록을 사용하여 파일 처리
            spmd(obj.NumMCAD)
                % 이미 할당된 mcad 인스턴스 사용
                if isempty(obj.MCADInstances) || length(obj.MCADInstances) < spmdIndex || isempty(obj.MCADInstances{spmdIndex})
                    error('MCAD instance is not properly initialized for worker %d.', spmdIndex);
                end
                mcad = obj.MCADInstances{spmdIndex};
        
                % 각 워커가 처리할 파일의 범위 지정
                for idx = spmdIndex:spmdSize:length(obj.BuildList)
                    % 파일 로드 및 변수 설정
                    motFileData = obj.BuildList(idx);
                    mcad.LoadFromFile(motFileData.SLLAWMotFilePath);
                    mcad.SetVariable('AirgapDefinition', 1);
                    mcad.SetVariable("MessageDisplayState", 2);
                    setMcadVariable(motFileData.SLScaledMachineData, mcad);                    
                    mcad.ClearModelBuild_Lab()
                    mcad.SaveToFile(motFileData.SLLAWMotFilePath);
                end
            end
        end

    end
end
