function plotMOP(data)
    % correlation matrix 출력 함수
    data.Properties.VariableNames = strrep(data.Properties.VariableNames,'_',' ');
    data.Var1=strrep(data.Var1,'_',' ');
    % Y축 라벨 설정
    ylabels = data.Var1;
    
    % X축 라벨 설정
    xlabels = data.Properties.VariableNames(2:end);
    
    % Var1을 제외한 나머지 변수들로부터 상관 행렬 계산
    corr_matrix = table2array(data(:, 2:end));
    
    % imagesc 그리기
    imagesc(corr_matrix);
    colormap(jet);
    colorbar;
    title('Correlation Matrix Imagesc');
    set(gca, 'YTick', 1:size(data, 1) , 'YTickLabel', ylabels);
    % set(gca, 'XTick', 1:size(data, 2) - 1, 'XTickLabel', xlabels);
    
    % 각 셀의 값을 출력하기 위한 loop
    for i = 1:size(corr_matrix, 1)
        for j = 1:size(corr_matrix, 2)
            text(j, i, num2str(corr_matrix(i, j), '%.2f'),'FontName','Times New Roman' ,'HorizontalAlignment', 'center','Color',[255/256,255/256,255/256]);
        end
    end
    formatter_sci       
end
