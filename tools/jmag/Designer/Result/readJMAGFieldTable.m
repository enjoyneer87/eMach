function FieldData=readJMAGFieldTable(filePath)
%% dev
% filePath=exportFilePath{1};
%%
opts = detectImportOptions(filePath,'VariableNamesLine',1,'VariableNamingRule','preserve');
% 파일 경로 설정
% 데이터를 가져오기
filedTable = readtable(filePath, opts);


filedTable = setVarAsRowNames(filedTable, 'Element ID');
filedTable = removevars(filedTable,'Element ID');

BoolPositionCol = contains(filedTable.Properties.VariableNames, 'position','IgnoreCase',true);
positionTable = filedTable(:, BoolPositionCol);
filedTable(:,BoolPositionCol)=[];
BoolAbsCol = contains(filedTable.Properties.VariableNames, 'Abs','IgnoreCase',true);
BoolxCol = contains(filedTable.Properties.VariableNames, 'x','IgnoreCase',true);
BoolyCol = contains(filedTable.Properties.VariableNames, 'y','IgnoreCase',true);
BoolzCol = contains(filedTable.Properties.VariableNames, 'z','IgnoreCase',true);

BoolrCol = contains(filedTable.Properties.VariableNames, 'r','IgnoreCase',true);
BoolthetaCol = contains(filedTable.Properties.VariableNames, 'θ','IgnoreCase',true);
BoolzCol = contains(filedTable.Properties.VariableNames, 'z','IgnoreCase',true);
AbsTable    = filedTable(:, BoolAbsCol);
xTable      = filedTable(:, BoolxCol);
yTable      = filedTable(:, BoolyCol);
zTable      = filedTable(:, BoolzCol);

rTable      = filedTable(:, BoolrCol);
thetaTable      = filedTable(:, BoolthetaCol);

FieldData.positionTable       =           positionTable   ;         
FieldData.AbsTable        =           AbsTable            ; 
FieldData.xTable          =           xTable              ; 
FieldData.yTable          =           yTable              ; 
FieldData.zTable          =           zTable              ; 

FieldData.rTable          =           rTable              ; 
FieldData.yTable          =           yTable              ; 
FieldData.thetaTable      =           thetaTable              ; 
end