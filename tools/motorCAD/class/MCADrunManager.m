classdef MCADrunManager
   %% Emag calculation을 table을 돌리는 클래스
    %   자세한 설명 위치

    properties
        NumMCAD                  % Motor-CAD 인스턴스의 수   
        runListTable             % 처리할 Motor-CAD 파일 목록
        MCADInstance             % 생성된 Motor-CAD 인스턴스를 저장하는 Composite 객체
    end

    methods
        function obj = MCADLabManager(numMCAD, runListTable)
            % 생성자 함수
            obj.NumMCAD = numMCAD;
            obj.runListTable = runListTable;     %  테이블형태
            obj.MCADInstances = [];
            % % Build Setting
            % obj.LabBuildSettingTable =[];
            % % DutyCycle_Lab
            % obj.DutyCycleCalcSettingTable=[];
            % % Magnetic_Lab
            % obj.Magnetic_LabCalcSettingTable=[];
        end
    %% 병렬 method들 
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
            pyenv('Version', 'C:\ANSYS_Motor-CAD\2025_1_1\Python\Python\python.exe');
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
%% setupParallelPoolSPMD
        function obj = setupParallelPoolSPMD(obj)
            runListTable = obj.runListTable;
            if isfield(runListTable,'IsCalculated')
            FilteredTable = runListTable(runListTable.IsCalculated == 0, :);  %% 생성 안된 애들
            else
            FilteredTable =runListTable;
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

    %% processEmag
            function obj = processEmag(obj)
         
            obj=obj.setupParallelPoolSPMD();
            %% 생성할 목록
            runListTable=obj.runListTable;
            FilteredTable = runListTable(runListTable.IsCalculated == 0, :);
            requiredWorkers = min(obj.NumMCAD, height(FilteredTable));
            if requiredWorkers>0

      %% spmd 블록을 사용하여 파일 처리
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
                            setMcadVariable(motFileData.SLScaledMachineData, mcad);  % 기계 데이터 설정
                            mc.do_magnetic_calculation; 
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
    end



end