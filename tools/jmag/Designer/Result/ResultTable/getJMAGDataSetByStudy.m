function [DataSetAllNames,DataManager]=getJMAGDataSetByStudy(app)
    NumModels=app.NumModels;
    for ModelIndex=1:NumModels
    ModelNameList=app.GetModel(NumModels-1).GetName;

    end
     Model.NumStudies
    DataManager=app.GetDataManager();
    if DataManager.IsValid
        NumSets=DataManager.NumSets;
        DataSetAllNames=DataManager.GetAllNames;

    end

end