function setlegendBoxShape(NumColumn)

% legend
% legend('Location', 'north');
lgd=legend('Location', 'north', 'Orientation', 'horizontal',NumColumns=NumColumn);
%%
% 범례 생성, 위치 설정 및 박스 표시 없애기
% lgd = legend('Location', 'northoutside','Orientation', 'horizontal',NumColumns=4);
% lgd.Box = 'off'; % 범례의 박스 표시를 없앰
% 
% 
% % 범례의 위치를 수동으로 조정
% % 예: 범례를 그래프 상단에 더 가깝게 위치시킴
lgdPos = lgd.Position;
lgd.Position = [lgdPos(1), lgdPos(2)+lgdPos(4), lgdPos(3), lgdPos(4)];
%%
% legend('Location', 'north', 'Orientation', 'horizontal',NumColumns=6);

end