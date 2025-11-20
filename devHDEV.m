
    requiredWorkers = min(18, height(ListTable4Scaling));
mcad=callMCAD

  
    % 문자열을 datetime 형식으로 변환
    dateFormat = "dd-MM-yyyy HH:mm:ss";

    fileDateTime = datetime(strtrim(result), 'InputFormat', dateFormat);
    
    % 특정 시점 설정 (예: 2023-01-01 00:00:00)
    specificDateTime = datetime('2024-06-26 03:00:00', 'InputFormat', 'yyyy-MM-dd HH:mm:ss');
    
 
    for idx = length(newFileList):-1:1
     LastWriteDate=getFileLastWriteDate(newFileList{idx});
     LastWriteDate=datetime(strtrim(LastWriteDate), 'InputFormat', dateFormat);
   if LastWriteDate > specificDateTime
                            newFileList(idx)=[];
   end
    end



    parentPath='D:\KangDH\Thesis\Sensitivity__f3'
    requiredWorkers=12;
    spmd(requiredWorkers)
                mcad = actxserver('motorcad.appautomation');  % 각 워커별로 ActiveX 인스턴스 생성
                % obj.MCADInstances{spmdIndex} = mcad;  % Composite 객체에 인스턴스 저장      
            % 각 워커가 처리할 파일의 범위 지정
                for idx = spmdIndex : spmdSize : height(newFileList)
                        if isfile(newFileList{idx})
                            % LastWriteDate=getFileLastWriteDate(newFileList{idx});
                            % LastWriteDate=datetime(strtrim(LastWriteDate), 'InputFormat', dateFormat);
                            % if LastWriteDate < specificDateTime
                            mcad.LoadFromFile(newFileList{idx});
                            mcad.SetVariable("MessageDisplayState", 2);
                            mcad.RestoreCompatibilitySettings();
                            mcad.SaveToFile(newFileList{idx});  
                            disp(['Task completed successfully for file: ', newFileList{idx}]);
                            % else
                            % newFileList(idx)=[];
                            % end
                        end
                end
    end
% requiredWorkers=12
delete(gcp)
%     spmd(requiredWorkers)
%                 for idx = spmdIndex : spmdSize : height(copiedFilePath)
% 
                  motMatFileListTable       = getMotMatFileListTable(parentPath);
                motFileListTable = motMatFileListTable(contains(motMatFileListTable.FileType,'mot'),:)
               
                    motFileList = findMOTFiles(parentPath)';

    % Mot 파일 중 AutoSave가 포함되지 않은 파일 선택
    motFileList = motFileList(~contains(motFileList, 'AutoSave'));
    motFileList = motFileList(~contains(motFileList, 'Backup'));
        motFileList = motFileList(~contains(motFileList, '2024'));

  % 파일명, 파일종류, 상대경로, 상위경로를 저장할 변수 초기화
    allFiles = [motFileList;];
    numFiles = numel(allFiles);
    fileNames = cell(numFiles, 1);
    fileTypes = cell(numFiles, 1);
    fileDirs = cell(numFiles, 1);
    parentPaths = cell(numFiles, 1); % 상위 경로 저장을 위한 셀 배열 초기화

    % 파일 정보 추출
    for i = 1:numFiles
        [path, name, ext] = fileparts(allFiles{i});
        fileNames{i} = [name ext]; % 확장자를 포함한 파일 이름
        relativeDir = strrep(path, parentPath,''); % 상대 디렉토리 추출 
        fileDirs{i} = relativeDir;
        parentPaths{i} = parentPath; % 모든 파일에 대해 상위 경로 저장

        % 파일 타입 설정
        if i <= numel(motFileList)
            fileTypes{i} = 'motFile';
        elseif i <= numel(motFileList) + numel(driveMatFiles)
            fileTypes{i} = 'DutyCycleMatFile';
        elseif i <= numel(motFileList) + numel(driveMatFiles) + numel(elecMatFiles)
            fileTypes{i} = 'ElecMatFile';
        elseif i <= numel(motFileList) + numel(driveMatFiles) + numel(elecMatFiles) + numel(satuMatFiles)
            fileTypes{i} = 'SatuMatFile';
        else
            fileTypes{i} = 'OtherMatFile';
        end
    end

    % 결과를 테이블로 조합
    tbl = table(fileNames, fileTypes, fileDirs, parentPaths, ...
                'VariableNames', {'FileName', 'FileType', 'FileDir', 'ParentPath'});


    refFilesList=motFileList
    newFileList=fullfile('D:\KangDH\Thesis\Sensitivity__f3',tbl.FileDir,tbl.FileName);

    [~,fileNameList,~]=fileparts(tbl.FileName)

    requiredWorkers=16

    spmd(requiredWorkers)
                for idx = spmdIndex : spmdSize : height(refFilesList)
                    if ~isfolder(fullfile('D:\KangDH\Thesis\Sensitivity__f3',tbl.FileDir{idx},fileNameList{idx},'LAB'))
                    % mkdir(fullfile('D:\KangDH\Thesis\Sensitivity__f3',tbl.FileDir{idx}))
                    mkdir(fullfile('D:\KangDH\Thesis\Sensitivity__f3',tbl.FileDir{idx},fileNameList{idx},'Lab'))

                    end
                % copyfile(refFilesList{idx},newFileList{idx})

                end
    end

    requiredWorkers=16
    spmd(requiredWorkers)
                for idx = spmdIndex : spmdSize : height(copiedFilePath)

                delete(copiedFilePath{idx})
                end
    end
%                 end
%     end
%     delete(gcp)