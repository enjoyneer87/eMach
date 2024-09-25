function restoreView(ax, axisState, viewState,DataAspectRatio)
    % 플로팅 후 축과 view를 복원하는 함수
    % axis(ax, axisState);  % 축 복원
    ax.XLim=axisState(1,1:2)
    ax.YLim=axisState(1,3:4)
    % if ~isemtpy(axisState(1,5:6))
    ax.ZLim=axisState(1,5:6)
    % end
    view(ax, viewState);  % view 복원
    ax.DataAspectRatio=DataAspectRatio;
     % [axisState,viewState,DataAspectRatio]=lockAxisAndView()
end