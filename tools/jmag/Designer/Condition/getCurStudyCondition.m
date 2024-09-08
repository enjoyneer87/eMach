function cdList=getCurStudyCondition(curStudyObj)

    % 기존 Condition 삭제
        if curStudyObj.IsValid
        NumConditions=curStudyObj.NumConditions;
             for conditionIndex=1:NumConditions
                 curCdObj=curStudyObj.GetCondition(conditionIndex-1);
                 if curCdObj.IsValid
                 cdList{conditionIndex,1}=curCdObj.GetName;
                 cdList{conditionIndex,2}=curCdObj.GetType;
                 end
             end
        end
end