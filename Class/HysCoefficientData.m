classdef HysCoefficientData
    properties
        CoeffName
        CoeffValue
        CoeffUnit
    end
    
    methods
        function obj = HysCoefficientData(matData)
            % matData에서 Eddy_Coefficient 필드의 이름과 값을 가져와서
            % 해당 클래스의 속성값으로 설정합니다.
            if isempty(matData) || isempty(matData.varStr)
                myField = matData.varStr;
            else
                myField = fieldnames(matData);
            end
    
            fieldListHys = myField(contains(myField, 'Hysteresis_Coefficient'));
            obj.CoeffName = fieldListHys;

            obj.CoeffValue = struct();
            obj.CoeffUnit = cell(length(fieldListHys), 1);

            for ii = 1:length(fieldListHys)
                obj.CoeffValue.(fieldListHys{ii}) = getfield(matData, fieldListHys{ii});
                idx = ismember(matData.varStr, fieldListHys{ii},'row');
                if contains(matData.varUnits(idx, :),'W.s')==1
                    obj.CoeffUnit{ii} = '[W/Hz]';
                else
                    obj.CoeffUnit{ii} = matData.varUnits(idx, :);
                end
            end                 
        end
    end
end