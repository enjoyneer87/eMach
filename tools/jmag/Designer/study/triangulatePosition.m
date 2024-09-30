function [x0, y0] = triangulatePosition(x, y, d)
    % x, y: 이미 알고 있는 임의의 점들의 좌표 (벡터)
    % d: 해당 점들과 미지의 점 사이의 거리 (벡터)
    % 이 함수는 미지의 점의 좌표 x0, y0을 반환합니다.

    % 초기 추정 좌표값 (평균값으로 설정)
    x0_guess = mean(x);
    y0_guess = mean(y);

    % 비선형 방정식을 푸는 함수
    options = optimoptions('fsolve','Algorithm','Levenberg-Marquardt', 'Display', 'off','MaxFunctionEvaluations',1000,'MaxIterations',500); % 옵션 설정
    result = fsolve(@(vars) distanceEquations(vars, x, y, d), [x0_guess, y0_guess], options);

    % 결과 반환
    x0 = result(1);
    y0 = result(2);
end

function F = distanceEquations(vars, x, y, d)
    % vars: 추정하는 미지의 점 좌표 [x0, y0]
    x0 = vars(1);
    y0 = vars(2);

    % 거리 방정식 설정
    F = sqrt((x0 - x).^2 + (y0 - y).^2) - d;
end