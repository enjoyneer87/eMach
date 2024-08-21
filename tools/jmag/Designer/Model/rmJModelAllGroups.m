function rmJModelAllGroups(app)
    Model=app.GetCurrentModel();
    GroupList=Model.GetGroupList();
    GroupList.IsValid
    GroupList.RemoveAllGroups;
end
