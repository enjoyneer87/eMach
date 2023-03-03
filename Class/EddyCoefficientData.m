classdef EddyCoefficientData
    properties
        CoeffName
        CoeffValue
        CoeffUnit
    end
    
    methods
        function obj = EddyCoefficientData(matData)
            % matData에서 Eddy_Coefficient 필드의 이름과 값을 가져와서
            % 해당 클래스의 속성값으로 설정합니다.

            if isempty(matData) || isempty(matData.varStr)
                myField = matData.varStr;
            else
                myField = fieldnames(matData);
            end
    
            fieldListEddy = myField(contains(myField, 'Eddy_Coefficient'));
            obj.CoeffName = fieldListEddy;
            
            obj.CoeffValue = struct();
            obj.CoeffUnit = cell(length(fieldListEddy), 1);
            for ii = 1:length(fieldListEddy)
                obj.CoeffValue.(fieldListEddy{ii}) = getfield(matData, fieldListEddy{ii});
                idx = ismember(matData.varStr, fieldListEddy{ii},'row');
                if matData.varUnits(idx, :)=='W.s$^2$'
                    obj.CoeffUnit{ii} = '[W/Hz^2]'
                else
                    obj.CoeffUnit{ii} = matData.varUnits(idx, :);
                end
            end
        end
    end
end