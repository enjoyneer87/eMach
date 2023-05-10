function [data1_resampled, data2_resampled] = coherenceSampling(data1, data2)
    % 입력 데이터의 길이 계산
    data1_length = length(data1);
    data2_length = length(data2);
    duration_seconds =1
    % 입력 데이터의 샘플링 주파수 계산
    data1_fs = data1_length / duration_seconds; % 데이터1의 샘플링 주파수
    data2_fs = data2_length / duration_seconds; % 데이터2의 샘플링 주파수
    
    % 두 데이터의 샘플링 주파수 중 작은 값으로 샘플링 주파수 설정
    resampling_fs = min(data1_fs, data2_fs);
    
    % resample 함수를 사용하여 데이터의 길이를 동일하게 맞춤
    data1_resampled = resample(data1, resampling_fs, data1_fs);
    data2_resampled = resample(data2, resampling_fs, data2_fs);
end