function Data = replaceSimilarData(Data)
    tolerance = 0.01;
    [~, idx] = unique(round(Data/10)*(1+tolerance));
    uniqueData = round(Data(idx));

    % 소수점 이하 버리기
    uniqueData = floor(uniqueData / 10) * 10;

    % speed_measured 리스트의 각 숫자를 검사하여 unique_speed의 유사한 값으로 대체
    for i = 1:numel(Data)
        diff = abs(uniqueData - Data(i));  % 각 unique_speed와 speed_measured 숫자 간의 차이 계산
        if any(diff < uniqueData*0.01)  % 차이가 1% 이내인 유사한 값이 있다면
            [~, idx] = min(diff);  % 차이가 최소인 값의 인덱스를 찾아
            Data(i) = uniqueData(idx);  % 해당 인덱스의 unique_speed 값으로 speed_measured 값을 대체
        end
    end
end