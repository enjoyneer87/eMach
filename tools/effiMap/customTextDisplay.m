% 등고선 텍스트 추가
% 텍스트 표시 함수 정의
function customTextDisplay(x, y, labels)
    labelValue = str2double(labels);
    if labelValue >= 1 && labelValue < 10
        textLabel = sprintf('%.1f', labelValue);
    else
        textLabel = sprintf('%.0f', labelValue);
    end
    text(x, y, textLabel, 'Interpreter', 'latex', 'Color', 'k', 'FontSize', 10, 'HorizontalAlignment', 'center');
end