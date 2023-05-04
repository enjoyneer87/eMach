% Load input/output data from the table
% data = readtable('input_output_table.csv');
data=F1;
% Separate input and output variables
input = data(:,2:29);
output = data(:,30:end);
input_data=table2array(input);
output_data=table2array(output);
numSamples=(length(input_data));
numInputs = width(input_data);
numOutputs  = width(output_data);


% Sobol Indices 계산을 위해 필요한 변수 초기화
n_inputs = size(input_data, 2); % 입력 변수 수
n_outputs = size(output_data, 2); % 출력 변수 수
total_effects = zeros(n_inputs, n_outputs); % Total Effect Sensitivity를 저장할 변수

% Sobol 시퀀스 생성
p = sobolset(n_inputs);
p = net(p, 1000); % 1000개의 샘플 생성

% Monte Carlo 시뮬레이션을 사용하여 Total Effect Sensitivity 계산
for i = 1:n_inputs % 각 입력 변수에 대해
    X = repmat(input_data, size(p, 1), 1); % 입력 데이터를 p의 행 수만큼 복사하여 행렬 X 생성
    X(:, i) = p(:, i); % 해당 입력 변수에 대한 Sobol 시퀀스 데이터를 X 행렬에 대입
    Y = repmat(output_data, size(p, 1), 1); % 출력 변수 데이터를 p의 행 수만큼 복사하여 행렬 Y 생성
    % Sobol Indices 계산
    [S, ST] = sobsa(X, Y); % sobsa 함수를 사용하여 Sobol Indices 계산
    total_effects(i, :) = ST'; % 결과를 total_effects 변수에 저장
end

% 결과 출력
disp('Total Effect Sensitivity:')
disp(total_effects)