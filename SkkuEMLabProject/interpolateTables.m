function [newMotorCurve, newMotorRequiredCurve1] = interpolateTables(motorCurve, motorRequiredCurve)
    % 긴 RPM 배열을 결정
    if height(motorCurve) > height(motorRequiredCurve)
        longTable = motorCurve;
        shortTable = motorRequiredCurve;
    else
        longTable = motorRequiredCurve;
        shortTable = motorCurve;
    end


    % 중복 RPM 값에 작은 노이즈 추가
    [~, uniqueIdx] = unique(shortTable.rpm, 'stable');
    noiseLevel = 1e-10; % 노이즈 수준 조정
    for i = 1:height(shortTable)
        if ~ismember(i, uniqueIdx)
            shortTable.rpm(i) = shortTable.rpm(i) + noiseLevel;
            noiseLevel = noiseLevel + 1e-10;
        end
    end

    % 보간을 위한 변수들을 배열로 변환
    shortArray = table2array(shortTable);
    longArray = table2array(longTable);
    shortRPM = shortArray(:, 1);
    longRPM = longArray(:, 1);
    longLength2Interpolate  =length(longRPM);

    if longRPM(end)>shortRPM(end)
        shortSpeedLinVec = linspace(min(shortRPM), max(shortRPM), longLength2Interpolate);
        newShortArrayWithShortRPMEnd = interp1(shortRPM, shortArray, shortSpeedLinVec, 'linear', 'extrap');
        newShortTableWithShortRPMEnd  = array2table(newShortArrayWithShortRPMEnd, 'VariableNames', shortTable.Properties.VariableNames);
        newlongArrayWithShortRPMEnd = interp1(longRPM, longArray, shortSpeedLinVec, 'linear', 'extrap');
        newlongTableWithShortRPMEnd  = array2table(newlongArrayWithShortRPMEnd, 'VariableNames', shortTable.Properties.VariableNames);
    % elseif shortRPM(end)>longRPM(end)
    else
        newShortArrayWithShortRPMEnd = interp1(shortRPM, shortArray, longRPM, 'linear', 'extrap');
        newShortTableWithShortRPMEnd  = array2table(newShortArrayWithShortRPMEnd, 'VariableNames', shortTable.Properties.VariableNames);
        newlongArrayWithShortRPMEnd = interp1(longRPM, longArray, longRPM, 'linear', 'extrap');
        newlongTableWithShortRPMEnd  = array2table(newlongArrayWithShortRPMEnd, 'VariableNames', shortTable.Properties.VariableNames);
    end
    % 
    % % 짧은 테이블의 모든 변수를 긴 테이블의 RPM에 맞게 보간
    %     newShortArrayWithLongRPMEnd = interp1(shortRPM, shortArray, longRPM, 'linear', 'extrap');
    % % 보간된 배열을 테이블로 변환
    %     newShortTableWithLongRPMEnd  = array2table(newShortArrayWithLongRPMEnd, 'VariableNames', shortTable.Properties.VariableNames);
    % 
    %     newlongArrayWithLongRPMEnd = interp1(longRPM, longArray, longRPM, 'linear', 'extrap');
    %     newlongTableWithLongRPMEnd  = array2table(newlongArrayWithLongRPMEnd, 'VariableNames', shortTable.Properties.VariableNames);
    % else
    % 원래 긴 테이블을 그대로 사용하거나 보간된 짧은 테이블을 사용하여 결과 할당
    if height(motorCurve) > height(motorRequiredCurve)
        newMotorCurve           = newlongTableWithShortRPMEnd;
        newMotorRequiredCurve1  = newShortTableWithShortRPMEnd;
    else
        newMotorCurve           = newShortTableWithShortRPMEnd;
        newMotorRequiredCurve1  = newlongTableWithShortRPMEnd; % 원하시는 대로 수정
    end

end
