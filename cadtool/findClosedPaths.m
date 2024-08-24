function closedPaths = findClosedPaths(lines)
    % lines는 선분의 시작점과 끝점 좌표 정보를 가지고 있는 N-by-4 크기의 배열입니다.
    % 각 행은 [x1, y1, x2, y2] 형태로 시작점과 끝점 좌표를 나타냅니다.

    numLines = size(lines, 1);
    closedPaths = {};

    for i = 1:numLines
        startPoint = lines(i, 1:2);
        endPoint = lines(i, 3:4);

        % 현재 선분을 시작점에서 끝점으로 연결
        currentPath = [startPoint; endPoint];
        remainingLines = lines;

        while ~isempty(remainingLines)
            connected = false;

            for j = 1:size(remainingLines, 1)
                nextStartPoint = remainingLines(j, 1:2);
                nextEndPoint = remainingLines(j, 3:4);

                % 현재 경로의 끝점과 다음 선분의 시작점 또는 끝점이 일치하면 연결
                if isequal(currentPath(end, :), nextStartPoint)
                    currentPath = [currentPath; nextEndPoint];
                    remainingLines(j, :) = [];
                    connected = true;
                    break;
                elseif isequal(currentPath(end, :), nextEndPoint)
                    currentPath = [currentPath; nextStartPoint];
                    remainingLines(j, :) = [];
                    connected = true;
                    break;
                end
            end

            % 더 이상 연결할 선분이 없으면 종료
            if ~connected
                break;
            end
        end

        % 폐경로인 경우 결과에 추가
        if isequal(currentPath(1, :), currentPath(end, :))
            closedPaths{end+1} = currentPath;
        end
    end
end