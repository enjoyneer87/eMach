function runMCADIterativeProcess(SLLAWMotFileParentPath,BuildTable, type)
    maxAttempts = 5;
    attempt = 0;
    success = false;

    while ~success && attempt < maxAttempts
        try
            currentPool = gcp('nocreate');
            if ~isempty(currentPool) && currentPool.NumWorkers == 1
                fprintf('Only one worker is available. Exiting loop.\n');
                success = true;  % 에러가 발생하지 않았으므로 성공적으로 완료
                break;
            end
            % 첫 번째 명령
            Obj_SLLAWLabList = MCADBuildList(SLLAWMotFileParentPath);
            SLLAWLabListTable = Obj_SLLAWLabList.toTable;
            
            % 두 번째 명령
            mergeSLLAWTable = mergeTables(BuildTable, SLLAWLabListTable);
            
            % 세 번째 명령
            SLLAWmotorCADManager = MCADLabManager(12, mergeSLLAWTable);
            SLLAWmotorCADManager.LabBuildSettingTable = defMcadLabBuildSetting();
            
            % 네 번째 명령
            if strcmpi(type, 'SLLAW')
                SLLAWmotorCADManager = SLLAWmotorCADManager.processSLLAW();
            elseif strcmpi(type, 'SLFEA')
                SLLAWmotorCADManager = SLLAWmotorCADManager.processSLFEA();
            else
                error('Unknown type specified. Must be ''SLLAW'' or ''SLFEA''.');
            end
            
            success = true;  % 에러가 발생하지 않았으므로 성공적으로 완료
        catch ME
            attempt = attempt + 1;  % 시도 횟수 증가
            fprintf('Attempt %d failed: %s\n', attempt, ME.message);
            pause(1);  % 잠시 대기 후 재시도
        end
    end
    
    if ~success
        fprintf('All attempts failed. Please check the system settings or the inputs.\n');
    end
end
