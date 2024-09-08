function result = Am2_to_Amm2(value)
    % Am2_to_Amm2 - A/m^2를 A/mm^2로 변환하는 함수
    %
    % 사용법:
    %   result = Am2_to_Amm2(value)
    %
    % 입력 매개변수:
    %   value - A/m^2 값(숫자형 배열 또는 스칼라)
    %
    % 출력 매개변수:
    %   result - A/mm^2로 변환된 값

    % 변환 계수 (1 m^2 = 1e6 mm^2)
    conversionFactor = 1e-6;

    % 변환 수행
    result = value * conversionFactor;
end