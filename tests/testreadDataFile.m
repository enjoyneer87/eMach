path1='Z:\01_Codes_Projects\Testdata_post\Test_Measured_Data\Load\Test_20210909\20210909\온도\';
path1_strc=dir(path1)

path1_strc=dir(path1)
path1_file = string.empty;
for i=1:length(path1_strc)
    path1_file(i) = string(path1_strc(i).name);
end



for j=1:length(path1_strc)
    if contains(lower(path1_strc(j).name), '.csv') || contains(lower(path1_strc(j).name), ".xlsx")
        % csv나 xlsx 파일이름이 포함되어 있다면 실행할 코드 작성
    OP2_20210909FileName=path1_strc(j).name
    OP2_20210909=readDataFile(fullfile(path1,OP2_20210909FileName),40);
    %     figure(j)
    end
end

checkdata=0.1

assert(OP2_20210909.("Time[s]")(1) == checkdata,"working")