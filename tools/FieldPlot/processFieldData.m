function [FieldDataSteps] = processFieldData(FieldData,startStep)

    % 필터링된 데이터에서 첫 번째 행 추출 (Post Key ID)
    
    BoolKeyIndex=contains(FieldData.Var1,'16001')&isnan(FieldData.Var2);
    FieldKeyIndex=find(contains(FieldData.Var1,'16001')&isnan(FieldData.Var2));
    postKeyIDRow =FieldData.Var1(FieldKeyIndex);

    % 두 번째 행: Step number, step, Output type, Physical quantity type, Value type
    stepNumberRow = FieldData.Var1(FieldKeyIndex+1,:);
    stepRow = FieldData.Var2(FieldKeyIndex+1,:);
    outputTypeRow = FieldData.Var3(FieldKeyIndex+1,:);
    physicalQuantityRow = FieldData.Var4(FieldKeyIndex+1,:);
    valueTypeRow = FieldData.Var5(FieldKeyIndex+1,:);
    
    % 세 번째 행: 요소 또는 노드의 개수
    elementOrNodeCount = FieldData.Var1(FieldKeyIndex+2,:);
    
    FieldDataSteps = separateFieldDataByStep(FieldData, FieldKeyIndex,startStep);
end