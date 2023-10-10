function subplots=getSubplotObject(figureObj)
    % allFigures = findall(0, 'Type', 'figure');
    figureHandle = figureObj;  % 이 부분에서 원하는 figure의 인덱스를 선택하세요.
    % subplots = findall(figureHandle, 'Type', 'axes');    
    %% 
    % 만약 legend나 colorbar와 같은 추가적인 axes 객체를 제외하고 싶다면,
    % Tag 속성을 사용하여 필터링할 수 있습니다. 
    % 일반적으로 MATLAB은 subplot에 대해 'Tag' 속성을 비워 두는 반면, 
    % colorbar나 legend에는 특정한 'Tag' 값을 할당합니다. 
    % 따라서 'Tag' 속성이 비어 있는 'axes'만 필터링하여 선택하면 됩니다:    
    subplots = findall(figureHandle, 'Type', 'axes', 'Tag', '');
end