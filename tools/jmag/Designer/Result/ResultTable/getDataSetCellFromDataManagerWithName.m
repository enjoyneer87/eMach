function tempGrName=getDataSetCellFromDataManagerWithName(app, DataSetName,GroupName)

    DataManager=app.GetDataManager();
    if DataManager.IsValid
        NumSets=DataManager.NumSets;
        % DataSetAllNames=DataManager.GetAllNames;
    end    
    % DataSetName='load';
    cellIndex=1;
    for DataSetIndex=1:NumSets
        %% DataSet
        DataSet{DataSetIndex}=app.GetDataManager().GetDataSet(DataSetIndex-1);
        if DataSet{DataSetIndex}.IsValid
            StudyName  =DataSet{DataSetIndex}.GetGroupName();
            GraphName  =DataSet{DataSetIndex}.GetName();
                if  contains(StudyName,GroupName,"IgnoreCase",true) && contains(GraphName,DataSetName,"IgnoreCase",true)
                tempGrName{cellIndex,1}=StudyName;
                tempGrName{cellIndex,2}=GraphName;
                %% getDataSetTable    
                tempGrName{cellIndex,3}=getJMagDataSet2MLabTable(DataSet{DataSetIndex});
                tempGrName{cellIndex,4}=DataSetIndex;
                cellIndex=cellIndex+1;
                end
        end
    end
    % GraphTable=cell2table(tempGrName);

end