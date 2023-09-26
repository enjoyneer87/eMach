function matFileListStruct=getDOEResultMatFiles(directory)
    % 디렉토리 내의 모든 파일 목록을 얻어옴
    matFiles=findMatFiles(directory)';
    for matFildeIndex=1:length(matFiles)
    itemInDIRStruct=dir(fileparts(matFiles{matFildeIndex}));
        
        for dirIndex=1:length(itemInDIRStruct)
            if contains(itemInDIRStruct(dirIndex).name,'mat')
            sourceFilePath=fullfile(itemInDIRStruct(dirIndex).folder,itemInDIRStruct(dirIndex).name);

                if isfile(sourceFilePath)  % 파일이 있으면 실행하는 코드
                    destinationFileName=[strrep(itemInDIRStruct(dirIndex).name,'.mat',''),strrep(removeAllSpecialCharacters(itemInDIRStruct(dirIndex).date),' ','_'),'.mat'];
                    destinationDir=strrep(itemInDIRStruct(dirIndex).folder,'DOE','DOEResult');
                    destinationDir=fileparts(fileparts(destinationDir));
            
                    if ~isfolder(destinationDir)  % destinationDir이 없으면 폴더 만드는 코드
                     mkdir(destinationDir)
                    end
            
                    destinationFilePath=fullfile(destinationDir,destinationFileName);
                    if ~isfile(destinationFilePath) % 없으면 copy하는 코드
                        copyfile(sourceFilePath, destinationFilePath);
                    end
                end
            end
        end
    end
    matFileList=findMatFiles(fileparts(destinationDir))';
    DutyCycleMatFileList=findDriveCycleDataList(matFileList);
    ElecMatFileList=findElecDataList(matFileList);
    matFileListStruct.DutyCycleMatFileList=DutyCycleMatFileList;
    matFileListStruct.ElecMatFileList=ElecMatFileList;
end
