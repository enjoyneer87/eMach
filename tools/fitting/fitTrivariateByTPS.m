function [model, fID,fIQ]= fitTrivariateByTPS(fitresults, z_assigned, grid_size)
    % RBF 네트워크를 사용하여 id, iq, RPM에 대한 손실값 예측 모델 생성
    % fitresults: 여러 개의 fitresult 셀 배열
    % z_assigned: 각 fitresult에 대응하는 RPM 값 벡터
    % grid_size: id, iq 그리드 크기 (ex: [100, 100])

    % z_assigned가 fitresult의 개수와 동일한지 확인
    num_fits = length(fitresults);
    if num_fits ~= length(z_assigned)
        error('The number of fitresults and assigned RPM values must be equal.');
    end

    % 첫 번째 fitresult에서 id, iq 범위를 추출 (모든 fitresult가 동일한 범위를 가진다고 가정)
    figure;
    h = plot(fitresults{1});
    id_range = [min(min(h.XData)), max(max(h.XData))];
    iq_range = [min(min(h.YData)), max(max(h.YData))];
    close all;

    % id, iq 그리드 생성
    id_vals = linspace(id_range(1), id_range(2), grid_size(1));
    iq_vals = linspace(iq_range(1), iq_range(2), grid_size(2));
    [ID, IQ] = meshgrid(id_vals, iq_vals);
    fID=ID(:)
    fIQ=IQ(:)

    % 데이터 준비
    X_train = [];  % 입력 데이터 (id, iq, RPM)
    y_train = [];  % 출력 데이터 (손실값)

    % 각 fitresult에서 데이터를 수집
    for i = 1:num_fits
        z_at_rpm = feval(fitresults{i}, ID, IQ);  % 각 RPM에서 손실값 계산
        X_temp = [ID(:), IQ(:), z_assigned(i) * ones(numel(ID), 1)];  % id, iq, RPM 데이터
        X_train = [X_train; X_temp];  % 입력 데이터 쌓기
        y_train = [y_train; z_at_rpm(:)];  % 출력 데이터 (손실값)
    end

    % GPR 모델 학습
    % % gpr_model = fitrgp(X_train, y_train);
    model = fitrgp(X_train, y_train, 'BasisFunction', 'constant', 'KernelFunction', 'ardsquaredexponential', 'FitMethod', 'exact');

    % 다항 회귀 모델 학습 (3차 다항식 예시)
    % model = fit(X_train, y_train, 'poly3');

    % 예측
    % y_pred = predict(model, [id_val, iq_val, rpm_val]);
    % 예측
    % y_pred = predict(gpr_model, [fID, fIQ 12000*ones(len(fIQ),1)]);
    
    % plot(fitresults{3})
    % hold on
    % scatter3(fID, fIQ,y_pred)
end

% X_train: [id, iq, RPM] 형식의 입력 데이터 (N x 3)
% y_train: 대응하는 손실값 (N x 1)
