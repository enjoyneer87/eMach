function [axisState,viewState,DataAspectRatio]=lockAxisAndView()
    % 현재 figure의 축과 view 설정을 고정하는 함수
    ax = gca;  % 현재 axes 핸들
    axisState = axis;  % 현재 axis 설정 저장
    viewState = ax.View;  % 현재 view 설정 저장
    % hold on;  % hold on 상태 유지
    DataAspectRatio=ax.DataAspectRatio;
    % 
    % % 'XLim', 'YLim', 'ZLim'을 설정하여 자동으로 변경되지 않도록 고정
    % xlim(ax, ax.XLim);  
    % ylim(ax, ax.YLim);
    % zlim(ax, ax.ZLim);

    % 플로팅 이후에도 고정 상태 유지
    % addlistener(ax, 'MarkedClean', @(~,~) restoreView(ax, axisState, viewState));
end

