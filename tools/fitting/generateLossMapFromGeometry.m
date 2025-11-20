function [loss_map, ID_grid, IQ_grid] = generateLossMapFromGeometry(dnn_model, geometry_params, current_norm, id_range, iq_range, varargin)
% GENERATELOSSMAPAROMGEOMETRY DNN 모델을 사용하여 새로운 geometry에 대한 손실 맵 생성
%
% 입력:
%   dnn_model      - 학습된 DNN 모델 (trainRBF_DNN의 출력)
%   geometry_params - geometry 파라미터 구조체
%                    .stator_slot_num, .rotor_pole_num, .air_gap, 
%                    .stack_length, .magnet_thickness
%   current_norm   - 전류 크기 (A)
%   id_range       - Id 범위 [min_id, max_id] 또는 벡터
%   iq_range       - Iq 범위 [min_iq, max_iq] 또는 벡터
%
% 선택적 입력 (Name-Value pairs):
%   'GridSize'     - 그리드 크기 [n_id, n_iq] (기본값: [20, 20])
%   'Centers'      - RBF 센터 좌표 [N×2] (기본값: 자동 생성)
%   'Bias'         - RBF bias 값 (기본값: 0)
%   'Verbose'      - 진행상황 출력 여부 (기본값: true)
%
% 출력:
%   loss_map - 예측된 손실 맵 [n_iq × n_id]
%   ID_grid  - Id 그리드
%   IQ_grid  - Iq 그리드
%
% 예시:
%   % 새로운 geometry 정의
%   geo = struct('stator_slot_num', 24, 'rotor_pole_num', 16, ...
%                'air_gap', 1.0, 'stack_length', 80, 'magnet_thickness', 4.0);
%   
%   % 손실 맵 생성
%   [loss_map, ID, IQ] = generateLossMapFromGeometry(dnn_model, geo, 120, ...
%                                                   [-200, 0], [0, 300], ...
%                                                   'GridSize', [30, 30]);
%   
%   % 시각화
%   figure; contourf(ID, IQ, loss_map, 20); colorbar;
%   xlabel('Id (A)'); ylabel('Iq (A)'); title('예측된 손실 맵');

% 작성자: MATLAB Copilot
% 버전: 1.0
% 날짜: 2024

%% 입력 파라미터 처리
p = inputParser;
addRequired(p, 'dnn_model');
addRequired(p, 'geometry_params', @isstruct);
addRequired(p, 'current_norm', @(x) isscalar(x) && x > 0);
addRequired(p, 'id_range', @(x) isnumeric(x) && length(x) >= 2);
addRequired(p, 'iq_range', @(x) isnumeric(x) && length(x) >= 2);
addParameter(p, 'GridSize', [20, 20], @(x) length(x) == 2 && all(x > 0));
addParameter(p, 'Centers', [], @(x) isempty(x) || (isnumeric(x) && size(x,2) == 2));
addParameter(p, 'Bias', 0, @isscalar);
addParameter(p, 'Verbose', true, @islogical);

parse(p, dnn_model, geometry_params, current_norm, id_range, iq_range, varargin{:});

grid_size = p.Results.GridSize;
centers = p.Results.Centers;
bias = p.Results.Bias;
verbose = p.Results.Verbose;

%% 입력 검증
required_fields = {'stator_slot_num', 'rotor_pole_num', 'air_gap', 'stack_length', 'magnet_thickness'};
for i = 1:length(required_fields)
    if ~isfield(geometry_params, required_fields{i})
        error('geometry_params에 필수 필드 ''%s''가 없습니다.', required_fields{i});
    end
end

if verbose
    fprintf('새로운 geometry에 대한 손실 맵을 생성합니다...\n');
    fprintf('Geometry 파라미터:\n');
    fprintf('  - Stator slots: %d\n', geometry_params.stator_slot_num);
    fprintf('  - Rotor poles: %d\n', geometry_params.rotor_pole_num);
    fprintf('  - Air gap: %.2f mm\n', geometry_params.air_gap);
    fprintf('  - Stack length: %.1f mm\n', geometry_params.stack_length);
    fprintf('  - Magnet thickness: %.2f mm\n', geometry_params.magnet_thickness);
    fprintf('  - Current norm: %.1f A\n', current_norm);
end

%% Id, Iq 그리드 생성
if length(id_range) == 2
    id_vec = linspace(id_range(1), id_range(2), grid_size(1));
else
    id_vec = id_range;
    grid_size(1) = length(id_vec);
end

if length(iq_range) == 2
    iq_vec = linspace(iq_range(1), iq_range(2), grid_size(2));
else
    iq_vec = iq_range;
    grid_size(2) = length(iq_vec);
end

[ID_grid, IQ_grid] = meshgrid(id_vec, iq_vec);

if verbose
    fprintf('그리드 크기: %d × %d\n', grid_size(1), grid_size(2));
    fprintf('Id 범위: [%.1f, %.1f] A\n', min(id_vec), max(id_vec));
    fprintf('Iq 범위: [%.1f, %.1f] A\n', min(iq_vec), max(iq_vec));
end

%% DNN으로 RBF 계수 예측
try
    % Geometry 특성 벡터 생성
    geo_vector = [geometry_params.stator_slot_num, ...
                 geometry_params.rotor_pole_num, ...
                 geometry_params.air_gap, ...
                 geometry_params.stack_length, ...
                 geometry_params.magnet_thickness, ...
                 current_norm];
    
    % DNN 예측
    predicted_coeffs = predict(dnn_model, geo_vector);
    
    if verbose
        fprintf('DNN으로 RBF 계수를 예측했습니다. (계수 개수: %d)\n', length(predicted_coeffs));
    end
    
catch ME
    error('DNN 예측 실패: %s', ME.message);
end

%% RBF 센터 설정
if isempty(centers)
    % 기본값: Id, Iq 그리드에서 균등하게 선택
    n_centers = min(length(predicted_coeffs), 50); % 최대 50개 센터
    center_ids = linspace(min(id_vec), max(id_vec), ceil(sqrt(n_centers)));
    center_iqs = linspace(min(iq_vec), max(iq_vec), ceil(sqrt(n_centers)));
    [C_ID, C_IQ] = meshgrid(center_ids, center_iqs);
    centers = [C_ID(:), C_IQ(:)];
    centers = centers(1:min(size(centers,1), length(predicted_coeffs)), :);
    
    if verbose
        fprintf('자동 생성된 RBF 센터 개수: %d\n', size(centers, 1));
    end
end

% 계수 개수와 센터 개수 맞추기
n_centers_actual = size(centers, 1);
if length(predicted_coeffs) > n_centers_actual
    weights = predicted_coeffs(1:n_centers_actual);
elseif length(predicted_coeffs) < n_centers_actual
    weights = [predicted_coeffs; zeros(n_centers_actual - length(predicted_coeffs), 1)];
else
    weights = predicted_coeffs;
end

%% 손실 맵 계산
loss_map = zeros(size(ID_grid));
n_points = numel(ID_grid);
failed_points = 0;

if verbose
    fprintf('손실 맵을 계산합니다... (%d개 점)\n', n_points);
    if n_points > 1000
        fprintf('진행률: ');
        update_interval = round(n_points / 20); % 5% 간격으로 업데이트
    end
end

for i = 1:n_points
    try
        query_point = [ID_grid(i), IQ_grid(i)];
        loss_map(i) = evaluateRBFThinplate(query_point, weights, centers, bias);
        
        % NaN 체크
        if isnan(loss_map(i))
            loss_map(i) = 0; % 또는 interpolation
            failed_points = failed_points + 1;
        end
        
    catch
        loss_map(i) = 0;
        failed_points = failed_points + 1;
    end
    
    % 진행률 표시
    if verbose && n_points > 1000 && mod(i, update_interval) == 0
        fprintf('%.0f%% ', 100*i/n_points);
    end
end

if verbose
    if n_points > 1000
        fprintf('\n');
    end
    fprintf('손실 맵 계산 완료!\n');
    if failed_points > 0
        fprintf('경고: %d개 점에서 계산 실패 (%.1f%%)\n', failed_points, 100*failed_points/n_points);
    end
    fprintf('예측된 손실 범위: [%.2e, %.2e]\n', min(loss_map(:)), max(loss_map(:)));
end

%% 후처리: 이상값 제거
if any(isinf(loss_map(:))) || any(loss_map(:) < 0)
    if verbose
        fprintf('이상값을 처리합니다...\n');
    end
    
    % 무한대값 제거
    loss_map(isinf(loss_map)) = NaN;
    
    % 음수값 처리 (손실은 일반적으로 양수)
    loss_map(loss_map < 0) = 0;
    
    % NaN 보간
    if any(isnan(loss_map(:)))
        loss_map = fillmissing(loss_map, 'linear');
    end
end

if verbose
    fprintf('손실 맵 생성이 완료되었습니다.\n');
    fprintf('최종 손실 범위: [%.2e, %.2e]\n', min(loss_map(:)), max(loss_map(:)));
end

end

%% 예시 사용법
%{
% 1. DNN 모델 로드
load('dnn_rbf_model.mat', 'dnn_model');

% 2. 새로운 geometry 정의
new_geo = struct();
new_geo.stator_slot_num = 36;
new_geo.rotor_pole_num = 24;
new_geo.air_gap = 0.8;
new_geo.stack_length = 100;
new_geo.magnet_thickness = 5.0;

% 3. 손실 맵 생성
[loss_map, ID, IQ] = generateLossMapFromGeometry(dnn_model, new_geo, 150, ...
                                                [-300, 0], [0, 400], ...
                                                'GridSize', [25, 25], ...
                                                'Verbose', true);

% 4. 시각화
figure('Position', [100, 100, 1200, 400]);

subplot(1,3,1);
surf(ID, IQ, loss_map);
title('3D 손실 맵'); xlabel('Id (A)'); ylabel('Iq (A)'); zlabel('손실');

subplot(1,3,2);
contourf(ID, IQ, loss_map, 20);
title('Contour 손실 맵'); xlabel('Id (A)'); ylabel('Iq (A)'); colorbar;

subplot(1,3,3);
imagesc(loss_map); axis xy;
title('Heat Map'); xlabel('Id 인덱스'); ylabel('Iq 인덱스'); colorbar;

% 5. 특정 점에서의 값 확인
id_test = -100; iq_test = 200;
[~, id_idx] = min(abs(ID(1,:) - id_test));
[~, iq_idx] = min(abs(IQ(:,1) - iq_test));
fprintf('Id=%.0f, Iq=%.0f에서의 예측 손실: %.2e\n', id_test, iq_test, loss_map(iq_idx, id_idx));
%}
