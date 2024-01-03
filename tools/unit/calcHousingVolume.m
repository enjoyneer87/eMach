function V_housing = calcHousingVolume(housing_outer_diameter, housing_inner_diameter, housing_height)
    % calcHousingVolume: 주택의 부피를 계산하는 함수
    %
    % 입력:
    %   housing_outer_diameter - 주택 외부 지름 (단위: mm)
    %   housing_inner_diameter - 주택 내부 지름 (단위: mm)
    %   housing_height - 주택의 높이 (단위: mm)
    %
    % 출력:
    %   V_housing - 계산된 주택의 부피 (단위: m³)
    %
    % 설명:
    %   이 함수는 주어진 외부 지름, 내부 지름, 그리고 높이를 사용하여 원통형 주택의 부피를 계산합니다.
    %   계산은 외부 원통의 부피에서 내부 원통의 부피를 빼고, 추가로 상단의 반구형 부분의 부피를 더하여 이루어집니다.

    V_housing = (((pi * (housing_outer_diameter / 2)^2 - pi * (housing_inner_diameter / 2)^2) * housing_height) + (pi * (housing_outer_diameter / 2)^2) * (housing_outer_diameter - housing_inner_diameter)) / 1e9;
end
