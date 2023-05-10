function [output] = runCalibration(input)

% ANSYS Mechanical 해석 변수 설정
% input으로부터 값을 받아와서 ANSYS Mechanical 실행

% % 목적 함수 정의
% function [residual] = obj_function(input)
%     % 목적 함수는 ANSYS Mechanical 출력값과 실험 데이터 사이의 출력 오차의 제곱을 최소화하는 것
%     ansys_output = get_ansys_mechanical_output(input);
%     experiment_data = load_experiment_data();
%     residual = norm(ansys_output - experiment_data)^2;
% end


function y = objfun(x)
    global calibrationObj
    if ~isequal(x,xLast) % Check if computation is necessary
        calibrationObj
        BEMFsample = exportMotorcadResult(calibrationObj);
        
        [myf,myc,myceq] 

        xLast = x;
    end
    % Now compute objective function
    y = myf + 20*(x(3) - x(4)^2)^2 + 5*(1 - x(4))^2;
end

% % 최적화 함수 실행
% options = optimoptions('fmincon', 'Display', 'iter', 'Algorithm', 'interior-point');
% input_lb = [0, 0, 0]; % input lower bound
% input_ub = [10, 10, 10]; % input upper bound
% x0 = [5, 5, 5]; % initial input value
% [optimized_input, fval] = fmincon(@obj_function, x0, [], [], [], [], input_lb, input_ub, [], options);

% 최적화 결과 확인
output = get_ansys_mechanical_output(optimized_input);
disp(['Optimized Input: ', num2str(optimized_input)]);
disp(['Optimized Output: ', num2str(output)]);
disp(['Residual: ', num2str(fval)]);