set(gca,'FontName','Times New Roman','FontSize',40);

% set(gca,'FontSize',14)
grid on
% legend
% legend('Location', 'north');
% legend('Location', 'northoutside', 'Orientation', 'horizontal',NumColumns=6);

%%
% 범례 생성, 위치 설정 및 박스 표시 없애기
% lgd = legend('Location', 'northoutside','Orientation', 'horizontal',NumColumns=4);
% lgd.Box = 'off'; % 범례의 박스 표시를 없앰
% 
% 
% % 범례의 위치를 수동으로 조정
% % 예: 범례를 그래프 상단에 더 가깝게 위치시킴
% lgdPos = lgd.Position;
% lgd.Position = [lgdPos(1), lgdPos(2)+lgdPos(4), lgdPos(3), lgdPos(4)];
%%
% legend('Location', 'north', 'Orientation', 'horizontal',NumColumns=6);



% ax = gca;
ax.XLabel.FontName = 'Times New Roman';
ax.YLabel.FontName = 'Times New Roman';
box on
% ax.XLabel.String=HDEV_measured.I1(1).time.Properties.VariableNames
% ax.YLabel.String=convertCharsToStrings(HDEV_measured.I1(1).value.Properties.Description)
% 
% ax.Legend.String={'a','b','c','mean d','mean q','d','q'}
screenSize = get(0, 'ScreenSize');


% 현재 그래프 창을 전체 화면으로 설정
set(gcf, 'Position', screenSize*0.8);