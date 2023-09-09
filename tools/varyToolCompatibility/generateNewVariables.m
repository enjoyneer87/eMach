function newVariables = generateNewVariables(originalVariable, multiplierArray, variableName)
    % originalVariable을 multiplierArray의 각 요소와 곱하여 새로운 변수 생성
    
    % multiplierArray의 길이 확인
    numVariables = length(multiplierArray);
    
    % 결과를 저장할 테이블 초기화
    newVariables = table();
    
    % 변수 생성 루프
    for i = 1:numVariables
        % 새로운 변수 이름 설정
        newVarName = [variableName, num2str(i)];
        
        % originalVariable과 multiplierArray(i)를 곱하여 새로운 변수 생성
        newVariables.(newVarName) = originalVariable * multiplierArray(i);
    end
end
