function N52UH=readMCADMaterialDBFile(fileName)
%% 가져오기 옵션을 설정하고 데이터 가져오기
opts = delimitedTextImportOptions("NumVariables", 2);

% 범위 및 구분 기호 지정
opts.DataLines = [4 Inf];
opts.Delimiter = "=";

% 열 이름과 유형 지정
opts.VariableNames = ["AutomationName", "Value"];
opts.VariableTypes = ["string", "double"];

% 파일 수준 속성 지정
opts.ExtraColumnsRule = "ignore";
opts.EmptyLineRule = "read";

% 변수 속성 지정
% opts = setvaropts(opts, "Type", "WhitespaceRule", "preserve");
% opts = setvaropts(opts, "Type", "EmptyFieldRule", "auto");

% 데이터 가져오기
N52UH = readtable(fileName, opts);


%% 임시 변수 지우기
clear opts
end