function plot1DFFT(table2Plot,fullorHalf)
%% 
if nargin>1
fullorHalf=1;
else
fullorHalf=2;
end

%%
    for i = 1:width(table2Plot)
        varName = table2Plot.Properties.VariableNames{i}; % 변수 이름
        varUnit = table2Plot.Properties.VariableUnits{1}; % 변수 단위
        ticks=(0:1:height(table2Plot)/fullorHalf-1);
        bar(ticks,table2Plot.(varName)(1:end/fullorHalf), 'DisplayName', strrep(varName, '_', ' '))
        hold on;
        % Y축 라벨 설정: 변수 이름과 단위를 포함
        
        ylabel(['[', varUnit, ']']);
    end

    xlabel('Order','FontName','Times New Roman', 'FontSize',12,'FontWeight','B');
box on


end