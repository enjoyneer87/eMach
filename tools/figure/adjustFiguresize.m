function adjustFiguresize(xscale,yscale)
% 현재 화면 크기 가져오기
screenSize = get(0, 'ScreenSize');

% 화면의 폭과 높이 중 작은 길이를 계산
minLength = min(screenSize(3:4));

% 스케일링 비율 설정 (80%)
scaleFactor = 0.8;

% 새로운 피겨 창 크기 계산
newWidth = minLength * scaleFactor*xscale;
newHeight = minLength * scaleFactor*yscale;

% 현재 피겨 창 핸들을 가져오기
fig = gcf;

% 피겨 창의 위치와 크기 설정
fig.Position = [...
    (screenSize(3) - newWidth) / 2, ...  % 화면 가운데에 위치시키기 위해 X 좌표
    (screenSize(4) - newHeight) / 2, ... % 화면 가운데에 위치시키기 위해 Y 좌표
    newWidth, ...  % 새로운 폭
    newHeight ...  % 새로운 높이
];


end