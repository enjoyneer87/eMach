function [ResultTableFromCSV,ResultCSVPath]=readJMAGWholeResultTables(filterName)
%%dev
% filterName=FqfilterName

%% Get CSVPath N Filter
    CSVInGitPath=findCSVFiles(pwd)';
    if iscell(filterName)
        numFilters=len(filterName);
        for FilterIndex=1:numFilters
            CSVInGitPath=CSVInGitPath(contains(CSVInGitPath,filterName{FilterIndex},"IgnoreCase",true));
        end
        ResultCSVPath=CSVInGitPath;
    else
    ResultCSVPath=CSVInGitPath(contains(CSVInGitPath,filterName,"IgnoreCase",true));
    end
    AppNumStudies=length(ResultCSVPath);
    tempCSVPath=ResultCSVPath{1};
%% read Per Studies
    for PJTStudyIndex=1:AppNumStudies
        %% 가져오기 옵션을 설정하고 데이터 가져오기
        opts= detectImportOptions(tempCSVPath,"ReadVariableNames",true,"VariableNamesRow",1);
        numVar=len(opts.VariableOptions);
        opts                =delimitedTextImportOptions("NumVariables", 1);
        ResultTableFromCSVPerStudy     =readtable(ResultCSVPath{PJTStudyIndex},opts);
        ResultTableFromCSVPerStudy.Properties.VariableNames{1}='case Range';
        varNames=ResultTableFromCSVPerStudy.Properties.VariableNames;
        ResultTableFromCSVPerStudy.Properties.VariableNames= cellfun(@(x) strrep(x,'Extra',''), varNames,'UniformOutput',false);
        [ResultCSVDir,StudyName,~]     =fileparts(ResultCSVPath{PJTStudyIndex});
        parsedResultTable5StudyPerStudy=parseJMAGResultTable(ResultTableFromCSVPerStudy);
        parsedResultTable5StudyPerStudy.Properties.Description=StudyName;
        %% Mat으로 저장
        ResultTableFromCSV{PJTStudyIndex} =parsedResultTable5StudyPerStudy;
        save(fullfile(ResultCSVDir,['ResultTabStudy',StudyName,'.mat']),"parsedResultTable5StudyPerStudy")
        clear opts
    end
     % save(fullfile(app.GetProjectFolderPath,'AllResultTab.mat'),"ResultTableFromCSV")
end
