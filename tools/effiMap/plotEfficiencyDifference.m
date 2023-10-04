function plotEfficiencyDifference(Mat_File_Path1, Mat_File_Path2)
    % 첫 번째 데이터셋 로드
    Mat_File_Data1 = load(Mat_File_Path1);
    Speed1 = Mat_File_Data1.Speed;
    Shaft_Torque1 = Mat_File_Data1.Shaft_Torque;
    Efficiency1 = Mat_File_Data1.Efficiency;

    % 두 번째 데이터셋 로드
    Mat_File_Data2 = load(Mat_File_Path2);
    Speed2 = Mat_File_Data2.Speed;
    Shaft_Torque2 = Mat_File_Data2.Shaft_Torque;
    Efficiency2 = Mat_File_Data2.Efficiency;

    % Efficiency 값의 차이 계산
    EfficiencyDiff = abs(Efficiency1 - Efficiency2);

    % 등고선 설정
    cntrs = [0:0.1:5]; % 원하는 등고선 범위로 조정

    % 효율성 차이 등고선 플롯
    [~,h] = contourf(Speed1, Shaft_Torque1, EfficiencyDiff, cntrs, 'EdgeColor', 'none', 'DisplayName', 'Efficiency Difference');
    hold on;
    contour(Speed1, Shaft_Torque1, EfficiencyDiff, [0 0], 'LineColor', 'k', 'LineWidth', 2, 'DisplayName', 'Zero Difference Contour');

    % 플롯 양식 설정
    xlabel('Speed, [RPM]');
    ylabel('Torque, [Nm]');
    % title('Efficiency Difference');
    colorbar('Location', 'eastoutside');
    legend('Efficiency Difference', 'Zero Difference Contour', 'Location', 'northeast');
    colormap(jet);
    view(0, 90); % 시야각 조절
    formatter_sci
    hold off;
end
