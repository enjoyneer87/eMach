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
                SCMatrixName= mkScalingNameMatrixFromMCADDOEList(FilteredTable);
                SCMatrixNameVector = reshape(SCMatrixName, [numel(SCMatrixName), 1]);
                kRadialMatrix=mkScalingMatrixFromMCADDOEList(FilteredTable);
                kRadialVector = reshape(kRadialMatrix, [numel(SCMatrixName), 1]);
                doubleCellArray = num2cell(kRadialVector);
                ScalingCell=[SCMatrixNameVector,doubleCellArray];
                nonZeroNumber=nnz(kRadialMatrix);

            % 각 워커가 처리할 파일의 범위 지정
                for idx = spmdIndex : spmdSize : nonZeroNumber
                    originalRowIndex = mod(idx-1, height(FilteredTable)) + 1;
                    motFileData = FilteredTable(originalRowIndex, :);
                    try
                        % SLLAW 관련 파일 로드 및 변수 설정
                                refPath=motFileData.MotFilePath{:};      
                                additionalOption=ScalingCell{idx,1};
                                SLLAWPath= mkMCADFileFromRefPath(refModelPath,'SLLAW',additionalOption);
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
                        mcad.RestoreCompatibilitySettings()
                        mcad.ClearModelBuild_Lab();
                        mcad.SetVariable('ACLossHighFrequencyScaling_Method',0)
                        %SLLAW가 있으면 그냥 열어서      Lab만들기
                        %SLFEA가 없으면 SetVariable하고  Lab만들기
                        % if isfield(motFileData,'samesameMotFilePath')
                        %    if ~isfile(motFileData.SLFEAMotFilePath)
                        mcad.SetVariable('AirgapDefinition', 1);
                        %% SLMachineData
                        setMcadVariable(motFileData.SLScaledMachineData, mcad);
                        %% SL Lab Building Setting
                        setMcadTableVariable(obj.LabBuildSettingTable,mcad);
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