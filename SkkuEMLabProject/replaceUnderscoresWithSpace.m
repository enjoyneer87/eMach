function input = replaceUnderscoresWithSpace(input)
    % 함수 설명:
    % 이 함수는 입력이 테이블인 경우에만 변수 이름에서 언더스코어를 공백으로 대체하여
    % 변수 이름을 수정하는 역할을 합니다.
     
    if istable(input)
        % 입력이 테이블인 경우에만 실행됩니다.

        % 입력 테이블의 이전 변수 이름을 얻습니다.
        oldVarNames = input.Properties.VariableNames;

        % 이전 변수 이름에서 언더스코어를 공백으로 대체하여 새로운 변수 이름을 생성합니다.
        newVarNames = strrep(oldVarNames, '_', ' ');

        % 새로운 변수 이름을 입력 테이블의 변수 이름으로 할당하여 변수 이름을 수정합니다.
        input.Properties.VariableNames = newVarNames;
    elseif  ischar(input)|isstring(input)
        % 입력이 테이블이 아닌 경우, 경고 메시지를 표시합니다.
        input=strrep(input, '_', ' ');
    elseif iscell(input)
        for i=1:length(input)
        input{i}=strrep(input{i},'_',' ');
        end
        % disp('입력이 테이블이 아닙니다. 함수는 테이블에만 적용됩니다.');
    end
end
