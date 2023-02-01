function file_list = fcn_read_dat(file_list,allornot)

if allornot=='all'
    number2read=length(file_list.c1);
else 
    number2read=allornot;
end

    for i=1:number2read
    c1_file_name=file_list.c1(i).name;
    c2_file_name=file_list.c2(i).name;
    c3_file_name=file_list.c3(i).name;
    c4_file_name=file_list.c4(i).name;
    file_list.c1(i).rpm=extractBetween(convertCharsToStrings(file_list.c1(i).name),'650Vdc_','Rpm');
    
    
    opts = delimitedTextImportOptions("NumVariables", 2);
    
    
    % 범위 및 구분 기호 지정
    % if nargin < 2
    %     dataLines = [1, Inf];
    % end
    % opts.DataLines = dataLines;
    opts.Delimiter = " ";
    
    % 열 이름과 유형 지정
    opts.VariableNames = ["time", "data"];
    opts.VariableTypes = ["double", "double"];
    
    % 파일 수준 속성 지정
    opts.ImportErrorRule = "omitrow";
    opts.MissingRule = "omitrow";
    opts.ExtraColumnsRule = "ignore";
    opts.EmptyLineRule = "read";
    opts.ConsecutiveDelimitersRule = "join";
    opts.LeadingDelimitersRule = "ignore";
    
    % 데이터 가져오기
    c1_logg= readtable(c1_file_name, opts);
    file_list.c1(i).time=(c1_logg(:,1));
    file_list.c1(i).value=c1_logg(:,2);
    
    c2_logg= readtable(c2_file_name, opts);
    file_list.c2(i).value=c2_logg(:,2);
    
    c3_logg= readtable(c3_file_name, opts);
    file_list.c3(i).value=c3_logg(:,2);
    
    c4_logg= readtable(c4_file_name, opts);
    file_list.c4(i).value=c4_logg(:,2);
    
    % voltage=table(c3_logg, c4_logg.data);
    
    
    
    % 
    % 
end
end