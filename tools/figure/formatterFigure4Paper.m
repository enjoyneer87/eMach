function formatterFigure4Paper(columnType, layoutType)
    % formatterFigure4Paper - 논문 형식에 맞는 피겨 크기 설정 및 폰트 크기 조정
    %
    % 사용법:
    % formatterFigure4Paper(columnType, layoutType)
    %
    % 입력 매개변수:
    %   columnType - 'single' (단일 컬럼) 또는 'double' (더블 컬럼)
    %   layoutType - '1x1' (단일 피겨), '2x1', '2x2' (서브 피겨 레이아웃)
    %
    % 예:
    %   formatterFigure4Paper('double', '2x1');

    % 논문 형식에 따른 크기 설정 (mm)

    if ~isnumeric(columnType)
        if contains(columnType, 'Double','IgnoreCase',true)
            columnType = 2;
        elseif contains(columnType, 'single','IgnoreCase',true)
            columnType = 1;
        else
            error('Invalid columnType. Use "single" or "double".');
        end
    end
    
    if columnType == 2
        paperWidth = 84;   % 더블 컬럼 너비 (mm)
    elseif columnType == 1
        paperWidth = 174;    % 단일 컬럼 너비 (mm)
    end
    
    % 레이아웃 타입에 따라 높이 조정
    if strcmp(layoutType, '1x1')
        aspectRatio = 3/4;  % 폭과 높이의 비율
    elseif strcmp(layoutType, '2x1')
        aspectRatio = 3/2;  % 2x1 레이아웃일 경우
    elseif strcmp(layoutType, '2x2')
        aspectRatio = 3/4;  % 2x2 레이아웃일 경우
    else
        error('Invalid layoutType. Use "1x1", "2x1", or "2x2".');
    end

    paperHeight = paperWidth * aspectRatio;  % 높이를 폭에 맞춰 설정

    % 현재 화면 크기 가져오기
    screenSize = get(0, 'ScreenSize');
    screenDPI = get(0, 'ScreenPixelsPerInch');

    % 논문 크기를 픽셀로 변환
    paperWidthPx = paperWidth / 25.4 * screenDPI;
    paperHeightPx = paperHeight / 25.4 * screenDPI;

    % 화면 크기에 맞춰 스케일링 비율 계산
    scaleFactor = min(screenSize(3) / paperWidthPx, screenSize(4) / paperHeightPx) * 0.9;  % 약간의 여백을 위해 0.9 적용

    % 스케일링된 피겨 창 크기 계산
    newWidthPx = paperWidthPx * scaleFactor;
    newHeightPx = paperHeightPx * scaleFactor;

    % 현재 피겨 창 핸들을 가져오기
    fig = gcf;

    % 피겨 창의 위치와 크기 설정
    fig.Position = [...
        (screenSize(3) - newWidthPx) / 2, ...  % 화면 가운데에 위치시키기 위해 X 좌표
        (screenSize(4) - newHeightPx) / 2, ... % 화면 가운데에 위치시키기 위해 Y 좌표
        newWidthPx, ...  % 새로운 폭
        newHeightPx ...  % 새로운 높이
    ];

    % 피겨 창을 설정한 크기로 맞춤
    set(fig, 'Units', 'pixels', 'Position', fig.Position);

    % 실제 논문에서 12pt로 보이게 폰트 크기 조정
    ax = gca;
    targetFontSizePt = 12;  % 목표 폰트 크기 (pt)
    ptToPxFactor = screenDPI / 72;  % 1pt = 1/72 inch
    targetFontSizePx = targetFontSizePt / ptToPxFactor * scaleFactor;

    % X, Y 라벨 폰트 크기 설정
    ax.XLabel.FontSize = targetFontSizePx;
    ax.YLabel.FontSize = targetFontSizePx;

    % 기타 폰트 크기 설정 (예: 제목, 축 번호)
    ax.Title.FontSize = targetFontSizePx;
    ax.FontSize = targetFontSizePx;

    % X, Y 축 레이블에 쉼표를 포함한 숫자 형식 설정
    xticks = get(ax, 'XTick');
    yticks = get(ax, 'YTick');
    % X, Y 축 레이블에 쉼표를 포함한 숫자 형식 설정
    if ~isduration(xticks)&xticks>1000
    ax.XTickLabel = arrayfun(@(x) formatNumberWithComma(x), xticks, 'UniformOutput', false);
    end
    if any(yticks>999)
    ax.YTickLabel = arrayfun(@(x) formatNumberWithComma(x), yticks, 'UniformOutput', false);
    end
    % 박스 및 기타 옵션 설정
    ax.XLabel.FontName = 'Aerial';
    ax.YLabel.FontName = 'Aerial';
    box on
end