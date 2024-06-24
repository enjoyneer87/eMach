classdef MCADLabManager
    %% Lab Build 하고 FEA 돌리는 클래스
    properties
        NumMCAD        % Motor-CAD 인스턴스의 수
        BuildListTable      % 처리할 Motor-CAD 파일 목록
        MCADInstances  % 생성된 Motor-CAD 인스턴스를 저장하는 Composite 객체
        LabBuildSettingTable
        DutyCycleCalcSettingTable
        Magnetic_LabCalcSettingTable
        
    end

    methods
        function obj = MCADLabManager(numMCAD, buildListTable)
            % 생성자 함수
            obj.NumMCAD = numMCAD;
            obj.BuildListTable = buildListTable;     %  테이블형태
            obj.MCADInstances = [];
            % Build Setting
            obj.LabBuildSettingTable =[];
            % DutyCycle_Lab
            obj.DutyCycleCalcSettingTable=[];
            % Magnetic_Lab
            obj.Magnetic_LabCalcSettingTable=[];
        end
%% setupParallelPoolPyMCAD
        function obj = setupParallelPoolPyMCAD(obj)
            % 병렬 풀 설정
            if isempty(gcp('nocreate'))
                parpool();  % 새로운 크기로 병렬 풀 시작
            else
                currentPool = gcp('nocreate');
                if currentPool.NumWorkers ~= obj.NumMCAD
                    delete(currentPool);  % 기존 풀이 적절한 크기가 아니면 종료
                    parpool(obj.NumMCAD);  % 새로운 크기로 병렬 풀 시작
                end
            end
        
            % Python 환경 설정
            pyenv('Version', 'C:\ANSYS_Motor-CAD\2024_1_1\Python\Python\python.exe');
            currentPool = gcp('nocreate');
            % MCAD 인스턴스 생성
            if isempty(obj.MCADInstances)
                mcadInstances = Composite();
                spmd(currentPool.NumWorkers)
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
%%
        function obj = setupParallelPoolSPMD(obj)
            BuildTable = obj.BuildListTable;
            if isfield(BuildTable,'IsBuildFromDate')
            FilteredTable = BuildTable(BuildTable.IsBuildFromDate == 0, :);  %% 생성 안된 애들
            else
            FilteredTable =BuildTable;
            end
            % 필요한 워커 수 결정
            requiredWorkers = min(obj.NumMCAD, height(FilteredTable));
        
            % 현재 병렬 풀 상태 확인
            currentPool = gcp('nocreate');
            myCluster=getHPCProfile();
            if myCluster.NumWorkers<requiredWorkers
                requiredWorkers=myCluster.NumWorkers;
                obj.NumMCAD=requiredWorkers;
            end
            % defaultClusterProfile=parallel.defaultClusterProfile
            
            % 병렬 풀 재설정 필요성 확인 및 requiredWorkers가 0보다 클 때만 풀 생성
            if requiredWorkers > 0
                if isempty(currentPool) || currentPool.NumWorkers ~= requiredWorkers
                    if ~isempty(currentPool)
                        delete(currentPool);  % 기존 풀이 적절한 크기가 아니면 종료                       
                    end
                    parpool(requiredWorkers);  % 필요한 크기로 병렬 풀 시작
                end
            else
                fprintf('workers가 필요없어요 as there are no applicable tasks.\n');
            end
        end

        %%
    
        function obj = processSLFEA(obj)
         
            obj=obj.setupParallelPoolSPMD();
            %% 생성할 목록
            BuildTable=obj.BuildListTable;
            FilteredTable = BuildTable(BuildTable.IsBuildFromDate == 0, :);
            requiredWorkers = min(obj.NumMCAD, height(FilteredTable));
            if requiredWorkers>0
            % spmd 블록을 사용하여 파일 처리
            spmd(requiredWorkers)
                mcad = actxserver('motorcad.appautomation');  % 각 워커별로 ActiveX 인스턴스 생성
                % obj.MCADInstances{spmdIndex} = mcad;  % Composite 객체에 인스턴스 저장
 
                % 각 워커가 처리할 파일의 범위 지정
                for idx = spmdIndex : spmdSize : height(FilteredTable)
                    motFileData = FilteredTable(idx,:);  % 파일 데이터 접근
                    
                        try
                            SLFEAPath=motFileData.sameMotFilePath{:};
                            mcad.SetVariable("MessageDisplayState", 2);
                            mcad.LoadFromFile(SLFEAPath);  % 파일 로드
                            mcad.RestoreCompatibilitySettings();
                            mcad.SetVariable('ACLossHighFrequencyScaling_Method', 0);
                            mcad.SetVariable('ShaftSolve', 0);
        
                            % 계산 및 설정
                            pointPerElecCycle = 60;
                            mcad.SetVariable('TorquePointsPerCycle', pointPerElecCycle);
                            mcad.SetVariable('BackEMFPointsPerCycle', pointPerElecCycle);
                            PeriodModelAirGapPoints = calcAGPoint(motFileData.SLScaledMachineData.refMachineData.Pole_Number, pointPerElecCycle);
                            mcad.SetVariable('AirgapMeshPoints_layers', PeriodModelAirGapPoints);
                            mcad.SetVariable('AirgapMeshPoints_mesh', PeriodModelAirGapPoints);                
                            mcad.SetVariable('MagneticSolverMethod', 2);
                            mcad.SetVariable('FEASolutionCycle', 1);
            
                            % SLLAW 파일이 없는 경우 추가 설정
                            % if ~isfield(motFileData, 'SLLAWMotFilePath')
                            if ~isfield(motFileData, 'samesameMotFilePath')
                                mcad.SetVariable('AirgapDefinition', 1);
                                setMcadVariable(motFileData.SLScaledMachineData, mcad);  % 기계 데이터 설정
                                setCustomRotorPoint(mcad);  % 로터 포인트 설정
                                setMcadTableVariable(obj.LabBuildSettingTable, mcad);  % 테이블 설정
                                mcad.SetVariable("CurrentSpec_MotorLAB", 0);
                                mcad.SetVariable("MaxModelCurrent_MotorLAB", max(motFileData.SLLabTable{:}.Is));
                            end
                            % 빌드 설정 및 저장
                            mcad.ClearModelBuild_Lab();
                            mcad.BuildModel_Lab();
                            mcad.SaveToFile(SLFEAPath);  % 파일 저장
        
                            disp(['Task completed successfully for file: ', SLFEAPath]);
                        catch e
                            disp(['Error processing file ',SLFEAPath, ': ', e.message]);
                        end
                    
                end
            end
            else
                        disp('workers가 필요없어요 as there are no applicable tasks.\n');
            end
        end

%% processSLLAW
 function obj=processSLLAW(obj)
         
            obj=obj.setupParallelPoolSPMD();
            %% 
            BuildTable    =obj.BuildListTable;
            if isfield(BuildTable,'IsBuildFromDate')
            FilteredTable = BuildTable(BuildTable.IsBuildFromDate == 0, :);  %% 생성 안된 애들
            else
            FilteredTable =BuildTable;
            end
            %%
            requiredWorkers = min(obj.NumMCAD, height(FilteredTable));

            if requiredWorkers>0
            % spmd 블록을 사용하여 파일 처리
            spmd(requiredWorkers)
                mcad = actxserver('motorcad.appautomation');  % 각 워커별로 ActiveX 인스턴스 생성
                % obj.MCADInstances{spmdIndex} = mcad;  % Composite 객체에 인스턴스 저장
                SCMatrixName= mkScalingNameMatrixFromMCADDOEList(FilteredTable)';
                SCMatrixNameVector = reshape(SCMatrixName, [numel(SCMatrixName), 1]);
                kRadialMatrix=mkScalingMatrixFromMCADDOEList(FilteredTable)';
                kRadialVector = reshape(kRadialMatrix, [numel(SCMatrixName), 1]);
                doubleCellArray = num2cell(kRadialVector);
                ScalingCell=[SCMatrixNameVector,doubleCellArray];
                nonZeroNumber=numel(kRadialMatrix);
            
            % 각 워커가 처리할 파일의 범위 지정
                for idx = spmdIndex : spmdSize : nonZeroNumber
                    originalRowIndex = mod(idx-1, height(FilteredTable)) + 1;
                    motFileData = FilteredTable(originalRowIndex, :);
                    try
                        % SLLAW 관련 파일 로드 및 변수 설정
                                refPath=motFileData.MotFilePath{:};      
                                additionalOption=ScalingCell{idx,1};
                                SLLAWPath= mkMCADFileFromRefPath(refPath,'SLLAW',additionalOption);
                                refLabTable  =motFileData.refTable{:};
                                BuildingData =motFileData.BuildingData(:);
                                %%scalingFactorStruct
                                if ScalingCell{idx,2}==0
                                scalingFactorStruct.k_Radial   =1 ;
                                else
                                scalingFactorStruct.k_Radial   = ScalingCell{idx,2};
                                end
                                scalingFactorStruct.k_Axial    = 1;
                                scalingFactorStruct.a_p    = BuildingData.MotorCADGeo.ParallelPaths;
                                scalingFactorStruct.n_c    = BuildingData.MotorCADGeo.MagTurnsConductor;
                                scalingFactorStruct.k_Winding   = 1;
                                %% Scale
                                [SLScaledMachineData,SLLawScaledLabTable,~] = scaleTable4LabTable(scalingFactorStruct,refLabTable,BuildingData);                                        
                                                        %% 
                        motFileData.SLScaledMachineData=SLScaledMachineData;
                        motFileData.SLLawScaledLabTable={SLLawScaledLabTable};
                                                        % SLLAWPath=motFileData
                        mcad.LoadFromFile(SLLAWPath);
                        mcad.SetVariable("MessageDisplayState", 2);
                        mcad.RestoreCompatibilitySettings();
                        mcad.ClearModelBuild_Lab();
                        mcad.SetVariable('ACLossHighFrequencyScaling_Method',0);
                        %SLLAW가 있으면 그냥 열어서      Lab만들기
                        %SLFEA가 없으면 SetVariable하고  Lab만들기
                        % if isfield(motFileData,'samesameMotFilePath')
                        %    if ~isfile(motFileData.SLFEAMotFilePath)
                        mcad.SetVariable('AirgapDefinition', 1);
                        %% SLMachineData
                        setMcadVariable(motFileData.SLScaledMachineData, mcad);
                        %% SL Lab Building Setting
                        LabBuildSettingTable=obj.LabBuildSettingTable;
                        setMcadTableVariable(LabBuildSettingTable,mcad);
                        mcad.SetVariable("CurrentSpec_MotorLAB",0);
                        mcad.SetVariable("MaxModelCurrent_MotorLAB", max(motFileData.SLLawScaledLabTable{:}.Is));                        
                        %% - SCLaw 맵 구성 (땡겨오기)                       
                        [~,LabMatFileDir]=mcad.GetVariable('ResultsPath_MotorLAB');
                        ExportLabLinkTxtPath=makeLabLinkTXTFromLabTable(motFileData.SLLawScaledLabTable{:},LabMatFileDir);
                        if contains(LabMatFileDir,'SLLAW')
                            [newLabTxtDir,DesignName,~]=fileparts(SLLAWPath);
                            designNumber = extractDesignNumber(DesignName);
                            NewLabTxtPath=[newLabTxtDir,['\',designNumber,'SLLAW_LabLink.txt']];
                            movefile(ExportLabLinkTxtPath,NewLabTxtPath);
                        end
                        motFileData.ImportLabLinkTxtPath=NewLabTxtPath;
                        BuildData         =motFileData.BuildingData;                
                        ScaledMachineData =motFileData.SLScaledMachineData       ;      
                        LabLinkTxtPath    =motFileData.ImportLabLinkTxtPath      ;      
                        ImportExternalTXTLabModel(LabLinkTxtPath,BuildData,mcad,ScaledMachineData)
                        mcad.SaveToFile(SLLAWPath);
  
                        disp(['Task completed successfully for file: ', SLLAWPath]);
                       catch e
                            disp(['Error processing file ',SLLAWPath, ': ', e.message]);
                    end
                end
            end
            else
                    disp('workers가 필요없어요 as there are no applicable tasks.\n');
            end
        end

        % function obj=processSLLAW(obj)
        % 
        %     obj=obj.setupParallelPoolSPMD();
        %     %% 
        %     BuildTable    =obj.BuildListTable;
        %     if isfield(BuildTable,'IsBuildFromDate')
        %     FilteredTable = BuildTable(BuildTable.IsBuildFromDate == 0, :);  %% 생성 안된 애들
        %     else
        %     FilteredTable =BuildTable;
        %     end
        %     %%
        %     requiredWorkers = min(obj.NumMCAD, height(FilteredTable));
        %     if requiredWorkers>0
        %     % spmd 블록을 사용하여 파일 처리
        %     spmd(requiredWorkers)
        %         mcad = actxserver('motorcad.appautomation');  % 각 워커별로 ActiveX 인스턴스 생성
        %         % obj.MCADInstances{spmdIndex} = mcad;  % Composite 객체에 인스턴스 저장
        % 
        %     % 각 워커가 처리할 파일의 범위 지정
        %         for idx = spmdIndex : spmdSize : height(FilteredTable)
        %             motFileData = FilteredTable(idx,:);  % 파일 데이터 접근
        % 
        %             try
        %                 % SLLAW 관련 파일 로드 및 변수 설정
        %                 SLLAWPath=motFileData.sameMotFilePath{:};
        %                 % SLLAWPath=motFileData
        %                 mcad.LoadFromFile(SLLAWPath);
        %                 mcad.SetVariable("MessageDisplayState", 2);
        %                 mcad.RestoreCompatibilitySettings()
        %                 mcad.ClearModelBuild_Lab();
        %                 mcad.SetVariable('ACLossHighFrequencyScaling_Method',0)
        %                 %SLLAW가 있으면 그냥 열어서      Lab만들기
        %                 %SLFEA가 없으면 SetVariable하고  Lab만들기
        %                 % if isfield(motFileData,'samesameMotFilePath')
        %                 %    if ~isfile(motFileData.SLFEAMotFilePath)
        %                 mcad.SetVariable('AirgapDefinition', 1);
        %                 %% SLMachineData
        %                 setMcadVariable(motFileData.SLScaledMachineData, mcad);
        %                 %% SL Lab Building Setting
        %                 setMcadTableVariable(obj.LabBuildSettingTable,mcad);
        %                 mcad.SetVariable("CurrentSpec_MotorLAB",0);
        %                 mcad.SetVariable("MaxModelCurrent_MotorLAB", max(motFileData.SLLabTable{:}.Is));                        
        %                 %% - SCLaw 맵 구성 (땡겨오기)                       
        %                 [~,LabMatFileDir]=mcad.GetVariable('ResultsPath_MotorLAB');
        %                 ExportLabLinkTxtPath=makeLabLinkTXTFromLabTable(motFileData.SLLabTable{:},LabMatFileDir);
        %                 if contains(LabMatFileDir,'SLLAW')
        %                     [newLabTxtDir,DesignName,~]=fileparts(SLLAWPath);
        %                     designNumber = extractDesignNumber(DesignName);
        %                     NewLabTxtPath=[newLabTxtDir,['\',designNumber,'SLLAW_LabLink.txt']];
        %                     movefile(ExportLabLinkTxtPath,NewLabTxtPath);
        %                 end
        %                 motFileData.ImportLabLinkTxtPath=NewLabTxtPath;
        %                 BuildData         =motFileData.BuildingData;                
        %                 ScaledMachineData =motFileData.SLScaledMachineData       ;      
        %                 LabLinkTxtPath    =motFileData.ImportLabLinkTxtPath      ;      
        %                 ImportExternalTXTLabModel(LabLinkTxtPath,BuildData,mcad,ScaledMachineData)
        %                 mcad.SaveToFile(SLLAWPath);
        % 
        %                 disp(['Task completed successfully for file: ', SLLAWPath]);
        %             catch e
        %                     disp(['Error processing file ',SLLAWPath, ': ', e.message]);
        %             end
        %         end
        %     end
        %     else
        %             disp('workers가 필요없어요 as there are no applicable tasks.\n');
        %     end
        % end
        %% processFiles
        function processFiles(obj)
            % 병렬 풀이 이미 설정되었는지 확인
            if isempty(gcp('nocreate'))
                parpool();
            end
        
            % spmd 블록을 사용하여 파일 처리
            spmd(obj.NumMCAD)
                % 이미 할당된 mcad 인스턴스 사용
                if isempty(obj.MCADInstances) || length(obj.MCADInstances) < spmdIndex || isempty(obj.MCADInstances{spmdIndex})
                    error('MCAD instance is not properly initialized for worker %d.', spmdIndex);
                end
                mcad = obj.MCADInstances{spmdIndex};
        
                % 각 워커가 처리할 파일의 범위 지정
                for idx = spmdIndex:spmdSize:length(obj.BuildListTable)
                    % 파일 로드 및 변수 설정
                    motFileData = obj.BuildListTable(idx);
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
