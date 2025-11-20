function max_angle = getMaxObjectAngle(entitiesTable)
    % GETMAXOBJECTANGLE 엔티티 테이블에서 모든 객체들의 최대 각도를 추출하는 함수
    %
    % 입력:
    %   entitiesTable - 엔티티들이 포함된 테이블 (arc, line 필드 포함)
    %
    % 출력:
    %   max_angle - 모든 객체들 중 최대 각도 (도 단위)
    %
    % 작성자: 사용자
    % 날짜: 2025
    
    max_angle = 0;
    if class(entitiesTable) ~= "table"&&isstruct(entitiesTable)
        % Convert struct to table if necessary
        entitiesTable = struct2table(entitiesTable);    
    end

    % Check angles in arc entities
    arcEntities = entitiesTable.arc(~cellfun(@isempty, entitiesTable.arc), :);
    if ~isempty(arcEntities)
        for i = 1:length(arcEntities)
            arc = arcEntities{i};
            if length(arc) >= 5
                try
                    % Get arc center and calculate positions
                    [PosX, PosY] = PosArc(arc);
                    [theta, ~] = cart2pol(PosX, PosY);
                    angles = rad2deg(theta);
                    max_angle = max(max_angle, max(angles));
                    
                    % Also check arc start/end angles if centered at origin
                    if arc(1) == 0 && arc(2) == 0
                        max_angle = max(max_angle, max(arc(4), arc(5)));
                    end
                catch ME
                    % PosArc 함수 호출 실패 시 arc의 시작/끝 각도만 확인
                    fprintf('Warning: PosArc 함수 호출 실패 (arc %d): %s\n', i, ME.message);
                    if arc(1) == 0 && arc(2) == 0 && length(arc) >= 5
                        max_angle = max(max_angle, max(arc(4), arc(5)));
                    end
                end
            end
        end
    end
    
    % Check angles in line entities
    lineEntities = entitiesTable.line(~cellfun(@isempty, entitiesTable.line), :);
    if ~isempty(lineEntities)
        for i = 1:length(lineEntities)
            line = lineEntities{i};
            if length(line) >= 4
                [angle1, ~] = cart2pol(line(1), line(2));
                [angle2, ~] = cart2pol(line(3), line(4));
                angle1 = rad2deg(angle1);
                angle2 = rad2deg(angle2);
                
                % 음수 각도를 양수로 변환 (필요한 경우)
                if angle1 < 0
                    angle1 = angle1 + 360;
                end
                if angle2 < 0
                    angle2 = angle2 + 360;
                end
                
                max_angle = max(max_angle, max(angle1, angle2));
            end
        end
    end
    
    % 결과 출력 (디버깅용)
    fprintf('검출된 최대 객체 각도: %.2f°\n', max_angle);
    
end
