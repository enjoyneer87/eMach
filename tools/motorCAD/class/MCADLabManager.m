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

    function obj = setupParallelPoolPyMCAD(obj)
        % 병렬 풀 설정
        if isempty(gcp('nocreate'))
            parpool(obj.NumMCAD);  % 새로운 크기로 병렬 풀 시작
        else
            currentPool = gcp('nocreate');
            if currentPool.NumWorkers ~= obj.NumMCAD
                delete(currentPool);  % 기존 풀이 적절한 크기가 아니면 종료
                parpool(obj.NumMCAD);  % 새로운 크기로 병렬 풀 시작
            end
        end
    
        % Python 환경 설정
        pyenv('Version', 'C:\ANSYS_Motor-CAD\2023_2_1\Python\Python\python.exe');
    
        % MCAD 인스턴스 생성
        if isempty(obj.MCADInstances)
            mcadInstances = Composite();
            spmd(obj.NumMCAD)
                % 각 병렬 워커에서 Python 모듈을 독립적으로 임포트
                pymotorcad = py.importlib.import_module('ansys.motorcad.core');
                mcad = pymotorcad.MotorCADCompatibility();
                mcadInstances{spmdIndex} = mcad;
            end
            obj.MCADInstances = mcadInstances;  % Composite 객체를 객체 속성에 저장
        end
    end

        function obj = setupParallelPool(obj)
            numWorkers=obj.NumMCAD;
            obj.MCADInstances = cell(1, numWorkers);
            for i = 1:numWorkers
                obj.MCADInstances{i} = actxserver('motorcad.appautomation');
            end
        end

    function obj = setupParallelPoolSPMD(obj)
        % 병렬 풀 설정
        if isempty(gcp('nocreate'))
            parpool(obj.NumMCAD);  % 새로운 크기로 병렬 풀 시작
        else
            currentPool = gcp('nocreate');
            if currentPool.NumWorkers ~= obj.NumMCAD
                delete(currentPool);  % 기존 풀이 적절한 크기가 아니면 종료
                parpool(obj.NumMCAD);  % 새로운 크기로 병렬 풀 시작
            end
        end
    
        % MCAD 인스턴스 생성
        if isempty(obj.MCADInstances)
            mcadInstances = Composite();
            spmd(obj.NumMCAD)
                mcad = actxserver('motorcad.appautomation');
                mcadInstances = mcad;
            end
            obj.MCADInstances = mcadInstances;  % Composite 객체를 객체 속성에 저장
        end
    end
    

    function obj = processSLFEA(obj)

    % 병렬 풀 설정
    if isempty(gcp('nocreate'))
        parpool(obj.NumMCAD);  % 새로운 크기로 병렬 풀 시작
    else
        currentPool = gcp('nocreate');
        if currentPool.NumWorkers ~= obj.NumMCAD
            delete(currentPool);  % 기존 풀이 적절한 크기가 아니면 종료
            parpool(obj.NumMCAD);  % 새로운 크기로 병렬 풀 시작
        end
    end

    % spmd 블록을 사용하여 파일 처리
    spmd(obj.NumMCAD)
        mcad = actxserver('motorcad.appautomation');  % 각 워커별로 ActiveX 인스턴스 생성
        obj.MCADInstances{spmdIndex} = mcad;  % Composite 객체에 인스턴스 저장

        % 각 워커가 처리할 파일의 범위 지정
        for idx = spmdIndex : spmdSize : length(obj.BuildList)
            motFileData = obj.BuildList(idx);  % 파일 데이터 접근
            Pole_Number=motFileData.SLScaledMachineData.refMachineData.Pole_Number;
            try
                mcad.SetVariable("MessageDisplayState", 2);
                %% 불러오기
                mcad.LoadFromFile(motFileData.SLFEAMotFilePath);  % 파일 로드
                mcad.RestoreCompatibilitySettings();  % 호환성 설정 복원
                %%
                mcad.SetVariable('ACLossHighFrequencyScaling_Method', 0);
                mcad.SetVariable('ShaftSolve', 0);
                pointPerElecCycle=60;
                mcad.SetVariable('TorquePointsPerCycle',pointPerElecCycle);
                mcad.SetVariable('BackEMFPointsPerCycle',pointPerElecCycle);
                PeriodModelAirGapPoints=calcAGPoint(Pole_Number,pointPerElecCycle);
                mcad.SetVariable('AirgapMeshPoints_layers',PeriodModelAirGapPoints);
                mcad.SetVariable('AirgapMeshPoints_mesh',PeriodModelAirGapPoints);                
                mcad.SetVariable('MagneticSolverMethod',2);
                mcad.SetVariable('FEASolutionCycle',1);
                % SLLAW 파일이 없는 경우 추가 설정
                if ~isfield(motFileData, 'SLLAWMotFilePath')
                    mcad.SetVariable('AirgapDefinition', 1);
                    setMcadVariable(motFileData.SLScaledMachineData, mcad);  % 기계 데이터 설정
                    setCustomRotorPoint(mcad);  % 로터 포인트 설정
                    setMcadTableVariable(obj.LabBuildSettingTable, mcad);  % 테이블 설정
                    mcad.SetVariable("CurrentSpec_MotorLAB", 0);
                    mcad.SetVariable("MaxModelCurrent_MotorLAB", max(motFileData.SLLabTable.Is));
                end
                mcad.ClearModelBuild_Lab();  % 모델 빌드 초기화
                mcad.SaveToFile(motFileData.SLFEAMotFilePath);  % 파일 저장
                mcad.BuildModel_Lab();  % 모델 빌드
                mcad.SaveToFile(motFileData.SLFEAMotFilePath);  % 파일 저장

                disp(['Task completed successfully for file: ', motFileData.SLFEAMotFilePath]);
            catch e
                disp(['Error processing file ', motFileData.SLFEAMotFilePath, ': ', e.message]);
            end
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
                    mcad.RestoreCompatibilitySettings()
                    mcad.SetVariable('ACLossHighFrequencyScaling_Method',0)
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
                        % [~,LabMatFileDir]=string(mcad.GetVariable('ResultsPath_MotorLAB'));
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
                    mcad.RestoreCompatibilitySettings()
                    setMcadVariable(motFileData.SLScaledMachineData, mcad);                    
                    mcad.ClearModelBuild_Lab()
                    mcad.SaveToFile(motFileData.SLLAWMotFilePath);
                end
            end
        end

    end
end
