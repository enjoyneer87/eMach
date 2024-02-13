function output = removeNumbersFromString(inputString)
    % 이 함수는 주어진 문자열에서 모든 숫자를 제거합니다.
    
    % 숫자에 해당하는 아스키 코드 범위를 정의합니다 (0부터 9까지)
    numbersAscii = '0':'9';

    % 문자열에서 숫자를 제거합니다.
    output = inputString(~ismember(inputString, numbersAscii));
end
