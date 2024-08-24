function ResultTableFromCSV=readJMAGWholeResultTables(app)
%% Get AllCaseTables
    NumModel         =app.NumModels;
    NumTotalStudy    =app.NumStudies;
for PJTStudyIndex=1:NumTotalStudy
    curStudyObj=app.GetStudy(PJTStudyIndex-1);
     if curStudyObj.HasResult
        DTObj               =curStudyObj.GetDesignTable;
        NumCases            =DTObj.NumCases;
        ResultFileNamesCell =curStudyObj.GetResultFileNames;
        ResultFile4Path     =curStudyObj.GetResultFileName;
        PathInfoList        =strsplit(ResultFile4Path,'/');
        jplotName           =PathInfoList(end);
        caseName            =PathInfoList(end-1);
        StudyName           =PathInfoList(end-2);
        ModelName           =strrep(PathInfoList(end-3),'~','');
        ResultCSVName       =[ModelName{1},curStudyObj.GetName,'.csv'];        
        ResultCSVPath       =fullfile(app.GetProjectFolderPath,ResultCSVName); 
        %% CSV 만들기
        ResultTableObj      =curStudyObj.GetResultTable;
        ResultTableObj.WriteAllCaseTables(ResultCSVPath,'Step')
        %% 가져오기 옵션을 설정하고 데이터 가져오기
        opts                =delimitedTextImportOptions("NumVariables", 521);
        ResultTableFromCSV{PJTStudyIndex}      =readtable(ResultCSVPath,opts);
        %% Mat으로 저장
        save(fullfile(app.GetProjectFolderPath,'AllResultTab.mat'),"ResultTableFromCSV")
     end
      clear opts
end

