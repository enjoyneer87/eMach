function runMCADIterativeProcess(SLLAWMotFileParentPath,BuildListTable, type)
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
            % MCADSLLAWList2Build 객체 만들기 
            Obj_SLLAWLabList = MCADBuildList(SLLAWMotFileParentPath);
            SLLAWLabListTable = Obj_SLLAWLabList.toTable;  % MCADBuildList class를 테이블로
            
            % BuildTable과 MCADBuildList 객체 테이블 합치기
            mergeSLLAWTable = mergeTables(BuildListTable, SLLAWLabListTable);
            
            % MCADLabManager 만들기
            SLLAWmotorCADManager = MCADLabManager(6, mergeSLLAWTable);
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
