%% 일괄 Formatter
% 현재 떠 있는 모든 figure의 handle을 얻어옴
figHandles = findobj('Type', 'figure');

num_figures = numel(findall(0,'type','figure'))
% for i = 1:num_figures
%     figure(figHandles(i))
%     grid on
%     % legend
% 
%     % subplot(1,2,1)
%     ax=gca;
%     % box on
%     ax.YLabel.String='Idpk[A]'
%     ax.XLabel.String='Iqpk[A]'
% 
%     % 해당 figure에 대한 format 변경 코드 작성
% end



%% 각 figure를 png 형태로 저장
folderPath = 'Z:\01_Codes_Projects\Thesis_skku\Thesis_SKKU\figure\ACCESS2023'; % 저장할 폴더 경로



for i = 1:length(figHandles)
    figHandle = figHandles(i);
    figAxis=figHandle.Children
    figName = figAxis.Title.String;
    figName = strrep(figName, ' ', '_'); % 공백을 언더바로 변경
    figName = strrep(figName, '.', ''); % '.'을 제거
    filename = fullfile(folderPath, [figName '.png']); % 저장할 파일명과 경로를 합칩니다.
    exportgraphics(figHandle, filename, 'Resolution', 600,'BackgroundColor', 'none');
end
