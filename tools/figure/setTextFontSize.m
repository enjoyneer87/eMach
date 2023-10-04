function setTextFontSize(h, fontSize)
    % h: Text 객체의 부모 핸들 (예: contour3의 반환값)
    % fontSize: 설정하려는 글씨체 크기

    % Text 객체들의 핸들을 찾아 크기 변경
    textObjects = findall(h, 'Type', 'Text');
    for i = 1:length(textObjects)
        set(textObjects(i), 'FontSize', fontSize);
    end
end
