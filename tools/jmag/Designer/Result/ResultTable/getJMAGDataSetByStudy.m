function [DataSetAllNames,DataManager]=getJMAGDataSetByStudy(app)
    NumModels=app.NumModels;
    ModelNameList=cell(NumModels,1);
    for ModelIndex=1:NumModels
    ModelNameList{ModelIndex}=app.GetModel(NumModels-1).GetName;
    end
    % NumStudies=Model.NumStudies
    DataManager=app.GetDataManager();
    if DataManager.IsValid
        NumSets=DataManager.NumSets;
        DataSetAllNames=DataManager.GetAllNames;
    end

end