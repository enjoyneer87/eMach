
%% 가져오기 옵션을 설정하고 데이터 가져오기
function C1testEMF500rrpm00000=csv_to_table(file_path,a)

in_path=file_path;
file_name=a;


opts = delimitedTextImportOptions("NumVariables", 3);

% 범위 및 구분 기호 지정

opts.DataLines = [6, Inf];
opts.Delimiter = ",";

% 열 이름과 유형 지정
opts.VariableNames = ["Segment", "TrigTime", "Var3"];
opts.SelectedVariableNames = ["Segment", "TrigTime"];
opts.VariableTypes = ["double", "double", "string"];

% 파일 수준 속성 지정
opts.ExtraColumnsRule = "ignore";
opts.EmptyLineRule = "read";

% 변수 속성 지정
opts = setvaropts(opts, "Var3", "WhitespaceRule", "preserve");
opts = setvaropts(opts, "Var3", "EmptyFieldRule", "auto");
file_path_name=[in_path,file_name]
% 데이터 가져오기
C1testEMF500rrpm00000 = readtable(file_path_name, opts);


%% 임시 변수 지우기
clear opts