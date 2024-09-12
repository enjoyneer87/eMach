function restoreView(ax, axisState, viewState,DataAspectRatio)
    % 플로팅 후 축과 view를 복원하는 함수
    axis(ax, axisState);  % 축 복원
    view(ax, viewState);  % view 복원
    ax.DataAspectRatio=DataAspectRatio;
     % [axisState,viewState,DataAspectRatio]=lockAxisAndView()
end