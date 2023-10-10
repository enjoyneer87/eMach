function copySubplot2NewFigure(subplots)
% 원래 subplot 핸들을 가져옵니다.
original_subplot = subplots;

% 새로운 figure와 axes를 생성합니다.
new_fig = figure;
new_axes = axes;

% 원래 subplot의 모든 자식 객체를 새로운 axes로 복사합니다.
children = get(original_subplot, 'Children');
copyobj(children, new_axes);

%% 이부분을 추가로 확장해야될수도 원래 subplot의 주요 속성을 새로운 axes에 복사합니다. 
properties_to_copy = {'XLim', 'YLim', 'ZLim', 'XLabel', 'YLabel', 'ZLabel', 'Title','view'};

%%
for k = 1:length(properties_to_copy)
    prop_value = get(original_subplot, properties_to_copy{k});
    set(new_axes, properties_to_copy{k}, prop_value);
end

end
