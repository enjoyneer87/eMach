function [NewDOEStruct, DOEStruct] = tempfilterFieldsbySubField(DOEStruct, subFieldName, subFieldValue)
    fieldNameList = fieldnames(DOEStruct);
    NewDOEStruct = struct();
%     idx = 1;
    
    for i = 1:length(fieldNameList)
        FieldName = fieldNameList{i};
        
        % 필드가 비어있지 않고 필드 내에 'Weight'와 'SumofTotalLoss'가 있는 경우
        if ~isempty(DOEStruct.(FieldName)) && isfield(DOEStruct.(FieldName), 'Weight') && isfield(DOEStruct.(FieldName), 'SumofTotalLoss')
            % 필드 내의 subFieldName에 해당하는 값이 subFieldValue보다 작은 경우
            if DOEStruct.(FieldName).Weight.(subFieldName) < subFieldValue
                % 새로운 구조체에 필드 추가
                NewDOEStruct.(FieldName) = DOEStruct.(FieldName);
                DOEStruct = rmfield(DOEStruct, FieldName);

            else
                % 그렇지 않으면 원래 구조체에 필드 유지
                DOEStruct.(FieldName) = DOEStruct.(FieldName);
            end
        else
            % 필드가 조건을 만족하지 않는 경우도 원래 구조체에 필드 유지
            DOEStruct.(FieldName) = DOEStruct.(FieldName);
        end
    end
    
    % 필요한 경우 빈 필드를 제거하려면 다음 코드를 사용할 수 있습니다.
    % NewDOEStruct = rmfield(NewDOEStruct, fieldnames(NewDOEStruct));
end
