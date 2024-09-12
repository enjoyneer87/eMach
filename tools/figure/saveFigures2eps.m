function saveFigures2eps(folderDIR)
    % 주어진 폴더 경로에 있는 그래프들을 PNG 파일로 저장하는 함수
    % 폴더 경로에 있는 모든 figure 핸들을 찾음
    figHandles = findobj('Type', 'figure');
    
    % 각각의 figure에 대해 처리
    for figureIndex = 1:length(figHandles)
        figHandle = figHandles(figureIndex);
        
        % figure의 title을 가진 axes들을 찾음
        titleChildren = findAxesWithTitles(figHandle);
        
        % figure 이름 생성 및 처리
        for titleIndex = 1:length(titleChildren)
            titleAx = titleChildren(titleIndex);
            figName = titleAx.Title.String;
            if isempty(figName)
            label='figure';
            figName=[label,'_',num2str(figureIndex)];
            % figName = 'figure';
            else
            figName = strrep(figName, ' ', '_');        % 공백을 언더바로 변경
            figName = strrep(figName, '.', '');         % '.'을 제거
            end
            
            if contains(figName,'=')
            figName = strrep(figName, '=', '');         % '='을 제거
            end

            filename = fullfile(folderDIR, ['pic_' figName '.eps']);    % 저장할 파일명과 경로를 합침
            
            % 그래프를 PNG로 저장
            print(figHandle,filename);

            % exportgraphics(figHandle, filename, 'Resolution', 600, 'BackgroundColor', 'White');
        end
        
    end
end
