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



ax = gca;
ax.XLabel.FontName = 'Times New Roman';
ax.YLabel.FontName = 'Times New Roman';
box on
% ax.XLabel.String=HDEV_measured.I1(1).time.Properties.VariableNames
% ax.YLabel.String=convertCharsToStrings(HDEV_measured.I1(1).value.Properties.Description)
% 
% ax.Legend.String={'a','b','c','mean d','mean q','d','q'}

% 현재 화면 크기 가져오기
screenSize = get(0, 'ScreenSize');

% 화면의 폭과 높이 중 작은 길이를 계산
minLength = min(screenSize(3:4));

% 스케일링 비율 설정 (80%)
scaleFactor = 0.8;

% 새로운 피겨 창 크기 계산
newWidth = minLength * scaleFactor;
newHeight = minLength * scaleFactor;

% 현재 피겨 창 핸들을 가져오기
fig = gcf;

% 피겨 창의 위치와 크기 설정
fig.Position = [...
    (screenSize(3) - newWidth) / 2, ...  % 화면 가운데에 위치시키기 위해 X 좌표
    (screenSize(4) - newHeight) / 2, ... % 화면 가운데에 위치시키기 위해 Y 좌표
    newWidth, ...  % 새로운 폭
    newHeight ...  % 새로운 높이
];


% 현재 그래프 창을 전체 화면으로 설정
