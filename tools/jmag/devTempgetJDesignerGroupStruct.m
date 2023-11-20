function  GroupStruct=getJDesignerGroupStruct(app)
    Model=app.GetCurrentModel();
    GroupList=Model.GetGroupList();
    GroupList.IsValid
    NumGroups=GroupList.NumGroups;

    for GroupIndex=1:NumGroups
        GroupList.GetGroupName(0)
        GroupObj            =GroupList.GetGroup(GroupIndex);
        GroupPartIds        =GroupObj.GetPartIDs;
        for PartInGroupIndex=1:length(GroupPartIds)
        PartofGroup=GroupObj.GetPart(GroupPartIds{PartInGroupIndex});
        PartofGroup.IsValid




        end
