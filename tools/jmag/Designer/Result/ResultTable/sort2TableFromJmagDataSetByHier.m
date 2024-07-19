function Jproj=sort2TableFromJmagDataSetByHier(DataSetCellArray,app)
Jproj=setJMagHierStudyName(app);

% 셀 배열을 테이블로 변환
DataSetTable = cell2table(DataSetCellArray, "VariableNames", {'StudyModel', 'Graph', 'DataTable','GraphNumberInJmag'});

% 셀 배열의 각 요소에 대해 strsplit 적용하여 StudyName과 ModelName 변수 생성
splitResults = cellfun(@(x) strsplit(x, '_of_'), DataSetTable.StudyModel, 'UniformOutput', false);

% StudyName과 ModelName 변수 추출
DataSetTable.StudyName = cellfun(@(x) x{1}, splitResults, 'UniformOutput', false);
DataSetTable.ModelName = cellfun(@(x) x{2}, splitResults, 'UniformOutput', false);

DataSetTable=movevars(DataSetTable,"ModelName","Before","StudyModel");
DataSetTable=movevars(DataSetTable,"StudyName","After","ModelName");
DataSetTable=removevars(DataSetTable,"StudyModel");


for DataSetTableIndex=1:height(DataSetTable)
    GraphName=removeAllSpecialCharacters(DataSetTable.Graph{DataSetTableIndex});
    GraphName=replaceSpacesWithUnderscores(GraphName);
    Jproj.(DataSetTable.ModelName{DataSetTableIndex}).([DataSetTable.StudyName{DataSetTableIndex},'_of_',DataSetTable.ModelName{DataSetTableIndex}]).(GraphName)=GraphTable(DataSetTable.DataTable{DataSetTableIndex});
end

end