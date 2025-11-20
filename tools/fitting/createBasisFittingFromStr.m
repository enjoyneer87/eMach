function [coeffVector, basisFunc, DataSet] = createBasisFittingFromStr(buildDataStr, varName, validationData)
    % buildDataStr: 학습용 데이터 (table 또는 struct)
    % varName: 보간할 변수명
    % validationData: (선택) 검증용 데이터 table 또는 struct

    %% 학습 데이터 정리
    if istable(buildDataStr)
        inputTable = buildDataStr;
    elseif isstruct(buildDataStr)
        [inputTable, ~] = createTableFromMCADSatuMapStr(buildDataStr);
    else 
        error('올바른 학습 데이터를 입력하세요');
    end

    if ~isvarofTable(inputTable, 'Id_Peak')
        [inputTable.Id_Peak, inputTable.Iq_Peak] = pkgamma2dq(inputTable.Is, inputTable.("Current Angle"));
    end

    if all(inputTable.(varName) == 0)
        coeffVector = [];
        basisFunc = [];
        DataSet = [];
        return;
    end

    [xData, yData, zData] = prepareSurfaceData(inputTable.Id_Peak, inputTable.Iq_Peak, inputTable.(varName));

    %% basis fitting
    % Basis matrix for 3차
    Phi = [
        ones(size(xData)), ...
        xData, yData, ...
        xData.^2, xData.*yData, yData.^2, ...
        xData.^3, (xData.^2).*yData, xData.*(yData.^2), yData.^3
    ];
    
    % 계수 계산
    coeffVector = Phi \ zData;
    
    % basis 함수 정의
    basisFunc = @(x, y) coeffVector(1) + coeffVector(2)*x + coeffVector(3)*y + ...
                        coeffVector(4)*x.^2 + coeffVector(5)*x.*y + coeffVector(6)*y.^2 + ...
                        coeffVector(7)*x.^3 + coeffVector(8)*x.^2.*y + coeffVector(9)*x.*y.^2 + coeffVector(10)*y.^3;

    %% DataSet 기본 구성
    DataSet.xData = xData;
    DataSet.yData = yData;
    DataSet.zData = zData;
    DataSet.varName = varName;

    yhat = basisFunc(xData, yData);
    DataSet.statics.rmse = sqrt(mean((zData - yhat).^2));
    DataSet.originDqTable = inputTable;
    DataSet.originDqTable.Properties.Description = 'Training Data';

    %% Validation 데이터 처리
    if nargin >= 3 && ~isempty(validationData)
        if isstruct(validationData)
            [validationTable, ~] = createTableFromMCADSatuMapStr(validationData);
        elseif istable(validationData)
            validationTable = validationData;
        else
            error('validationData는 table 또는 struct여야 합니다.');
        end

        if ~isvarofTable(validationTable, 'Id_Peak')
            [validationTable.Id_Peak, validationTable.Iq_Peak] = pkgamma2dq(validationTable.Is, validationTable.("Current Angle"));
        end

        DataSet.xValidation = validationTable.Id_Peak;
        DataSet.yValidation = validationTable.Iq_Peak;
        DataSet.zValidation = validationTable.(varName);

        validationTable.Properties.Description = 'Validation Data';
        DataSet.ValidationDqTable = validationTable;
    else
        DataSet.xValidation = [];
        DataSet.yValidation = [];
        DataSet.zValidation = [];
        DataSet.ValidationDqTable = inputTable;
        DataSet.ValidationDqTable.Properties.Description = 'No Validation';
    end
end
