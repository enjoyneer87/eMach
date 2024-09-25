function targetFigs=mergeFigures(figNumbers,closefigure)
    % mergeFigureContents3D - 입력된 figure 번호들의 2D/3D 내용을 하나의 figure로 병합
    %
    % 사용법:
    % mergeFigureContents3D([figure1, figure2, ...])
    %
    % 입력:
    %   figNumbers: 병합할 figure 번호들의 배열

    % 새 figure 생성 및 axes 준비
    sourceFig = findobj('Type', 'figure');
    for figIdx=1:len(figNumbers)
    BoolFig=[sourceFig.Number]==figNumbers(figIdx);
    targetFigs(figIdx)=sourceFig(BoolFig);
    end
    %% MergeName
    mergedFigName=targetFigs(1).Name;
    for figIdx=2:len(figNumbers)
        mergedFigName=[mergedFigName,'&', targetFigs(figIdx).Name];
    end
    %% newFig
    newFig = figure('Name', ['merged:',mergedFigName ], 'NumberTitle', 'on');
    newAxes = axes('Parent', newFig);
    hold(newAxes, 'on'); % 여러 그래프를 중첩하기 위해 hold on
    
    % 이미 추가된 플롯 데이터를 저장할 cell 배열
    existingPlots = {};

    % 축 범위를 저장할 배열
    xLimits = [];
    yLimits = [];
    zLimits = [];
    
    % 첫 번째 figure의 레이블을 가져오기 위한 플래그
    labelSet = false;

    % 입력된 figure들의 내용을 하나의 figure로 복사
    for i = 1:length(figNumbers)
        % 원본 figure를 찾음
        sourceFig = findobj('Type', 'figure', 'Number', figNumbers(i));
        sourceAxes = findall(sourceFig, 'Type', 'axes');
        

        % 각 figure의 모든 axes에서 데이터를 복사
        for j = 1:length(sourceAxes)
            % 첫 번째 figure의 레이블을 가져옴
            if ~labelSet
                xlabel(newAxes, sourceAxes(j).XLabel.String);
                ylabel(newAxes, sourceAxes(j).YLabel.String);
                if ~isempty(sourceAxes(j).ZLabel)
                    zlabel(newAxes, sourceAxes(j).ZLabel.String);
                end
                labelSet = true; % 레이블 설정 완료
            end

            % 축 범위를 갱신 (가장 큰 범위를 찾아서 설정)
            xLimits = [xLimits; get(sourceAxes(j), 'XLim')];
            yLimits = [yLimits; get(sourceAxes(j), 'YLim')];
            if isprop(sourceAxes(j), 'ZLim')
                zLimits = [zLimits; get(sourceAxes(j), 'ZLim')];
            end

            % 복사할 플롯 객체들 (lines, scatter, surface 등)
            plotObjs = findall(sourceAxes(j), '-not', 'Type', 'axes','-not','Type','Text');

            % 각각의 plot 객체 복사하여 새로운 axes에 추가
            for k = 1:length(plotObjs)
                objType=class(plotObjs(k));
                if    contains(objType,'ConstantLine')
                 % TypeLine = get(plotObjs(k), 'InterceptAxis');
   
                    copyObj = copyobj(plotObjs(k), newAxes);
                    set(copyObj, 'Parent', newAxes);
                        % 복사된 객체의 데이터를 기존 목록에 저장
                        % existingPlots{end+1} = plotData;
                else
                    % 현재 객체의 데이터를 가져옴
                    xData = get(plotObjs(k), 'XData');
                    yData = get(plotObjs(k), 'YData');
                    
                    % ZData가 있는 객체인지 확인
                    if isprop(plotObjs(k), 'ZData')
                        zData = get(plotObjs(k), 'ZData');
                    else
                        zData = [];
                    end
                    % 중복 여부 확인
                    isDuplicate = false;
                    for m = 1:length(existingPlots)
                        % 기존 데이터와 비교하여 중복 여부 판단 (2D/3D 모두 처리)
                        if isequal(existingPlots{m}.XData, xData) && ...
                           isequal(existingPlots{m}.YData, yData) && ...
                           (isempty(zData) || isequal(existingPlots{m}.ZData, zData))
                            isDuplicate = true;
                            break;
                        end
                    end
                    
                    % 중복되지 않으면 객체 복사 및 저장
                    if ~isDuplicate
                        copyObj = copyobj(plotObjs(k), newAxes);
                        set(copyObj, 'Parent', newAxes);
                        % 복사된 객체의 데이터를 기존 목록에 저장
                        plotData.XData = xData;
                        plotData.YData = yData;
                        plotData.ZData = zData;
                        existingPlots{end+1} = plotData;
                    end
                end              
            end
        end
    end
    
    % 축 범위 설정 (가장 큰 범위로 설정)
    set(newAxes, 'XLim', [min(xLimits(:, 1)), max(xLimits(:, 2))]);
    set(newAxes, 'YLim', [min(yLimits(:, 1)), max(yLimits(:, 2))]);
    if ~isempty(zLimits)
        set(newAxes, 'ZLim', [min(zLimits(:, 1)), max(zLimits(:, 2))]);
    end
    
    % 병합 완료
    hold(newAxes, 'off');
    view(newAxes, 3); % 3D 시각화 지원을 위해 기본 3D 뷰로 설정
    disp('Figure의 2D/3D 내용이 성공적으로 병합되었습니다.');

    %% 병합후 기존 figure close
    if nargin>1

    for figIdx=2:len(targetFigs)
    close(targetFigs(figIdx));
    end

    end
end