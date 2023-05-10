function tablesCell=readDatasfromPath(path)
    StructPath=dir(path)
    StringPathFileName = string.empty;
%     for i=1:length(StructPath)
%         StringPathFileName(i,1) = string(StructPath(i).name);
%     end
%    
    for j=1:length(StructPath)
        if contains(lower(StructPath(j).name), '.csv') || contains(lower(StructPath(j).name), ".xlsx")
            % csv나 xlsx 파일이름이 포함되어 있다면 실행할 코드 작성
        OP2_20210909FileName=StructPath(j).name
        tablesCell{j}=readDataFile(fullfile(path,OP2_20210909FileName),40);

        end
    end


