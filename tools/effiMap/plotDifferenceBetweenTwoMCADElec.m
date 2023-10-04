function h = plotDifferenceBetweenTwoMCADElec(Mat_File_Path1, Mat_File_Path2, objectName, errorType, addText)
    % 기본적으로 절대 오차를 사용
    if nargin < 4
        errorType = 1;
    end
    
    % 기본적으로 등고선 텍스트를 추가
    if nargin < 5
        addText = false;
    end

    % 첫 번째 데이터셋 로드
    mcadMatData1 = load(Mat_File_Path1);
    Speed1 = mcadMatData1.Speed;
    Shaft_Torque1 = mcadMatData1.Shaft_Torque;
    data1 = mcadMatData1.(objectName);

    % 두 번째 데이터셋 로드
    mcadMatData2 = load(Mat_File_Path2);
    Speed2 = mcadMatData2.Speed;
    Shaft_Torque2 = mcadMatData2.Shaft_Torque;
    data2 = mcadMatData2.(objectName);

    if errorType==0
        errorType='absolute';
    elseif errorType==1
        errorType='relative';
    end

    % 데이터 값의 차이 계산
    
    if strcmp(errorType, 'absolute')
        dataDiff = abs(data1 - data2); % 절대 오차 계산
        errorTypeName = 'Absolute Error';
    elseif strcmp(errorType, 'relative')
        dataDiff = abs((data1 - data2) ./ data1); % 상대 오차 계산
        errorTypeName = 'Relative Error';
    else
        error('Invalid errorType. Use "absolute" or "relative".');
    end

    % 등고선 설정
    cmin = min(dataDiff(:));
    cmax = max(dataDiff(:));
    cntrs = linspace(cmin, cmax, 20); % 등고선 레벨 수를 조절할 수 있습니다.

    % 효율성 차이 등고선 플롯 (contour 함수 사용)
    h = contour(Speed1, Shaft_Torque1, dataDiff, cntrs, 'LineColor', 'k', 'DisplayName', ['Difference in ' replaceUnderscoresWithSpace(objectName)]);
    hold on;

    % 등고선에 색상 추가 (contourf 함수 사용)
    contourf(Speed1, Shaft_Torque1, dataDiff, cntrs, 'EdgeColor', 'none', 'DisplayName', ['Difference in ' replaceUnderscoresWithSpace(objectName)]);

    % 등고선 텍스트 추가
    if addText
        [~, h(2)] = contour3(Speed1, Shaft_Torque1, dataDiff, cntrs, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStep', 4, 'DisplayName', 'Contour3');
    end

    % 플롯 양식 설정
    xlabel('Speed, [RPM]');
    ylabel('Torque, [Nm]');
    title(['Difference in ' replaceUnderscoresWithSpace(objectName) ' (' errorTypeName ')']);
    colorbar('Location', 'eastoutside');
    legend(['Difference in ' replaceUnderscoresWithSpace(objectName)], 'Location', 'northeast');
    colormap(jet);
    view(0, 90); % 시야각 조절
    formatter_sci;
end
