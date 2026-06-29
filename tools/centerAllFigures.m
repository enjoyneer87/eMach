function centerAllFigures(monitorIdx)
    % monitorIdx: 피규어를 모으고 싶은 모니터 번호 (생략 시 1번 모니터)
    if nargin < 1
        monitorIdx = 1; 
    end

    openFigures = findall(0, 'type', 'figure');
    if isempty(openFigures)
        return;
    end

    % 연결된 모든 모니터의 개별 위치 정보 [left, bottom, width, height]를 가져옵니다.
    monitors = get(groot, 'MonitorPositions');
    
    % 모니터 인덱스 범위를 초과하지 않도록 보정
    if monitorIdx > size(monitors, 1)
        monitorIdx = 1;
    end
    
    target_monitor = monitors(monitorIdx, :);
    
    m_left   = target_monitor(1);
    m_bottom = target_monitor(2);
    m_width  = target_monitor(3);
    m_height = target_monitor(4);

    for i = 1:numel(openFigures)
        fig = openFigures(i);
        fig_w = fig.Position(3);
        fig_h = fig.Position(4);
        
        % 선택한 모니터 영역의 정중앙 좌표 계산
        figure_x = m_left   + (m_width/2  - fig_w/2);
        figure_y = m_bottom + (m_height/2 - fig_h/2);
        
        set(fig, 'Position', [figure_x, figure_y, fig_w, fig_h]);
    end
end
