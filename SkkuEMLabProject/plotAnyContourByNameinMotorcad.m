function data=plotAnyContourByNameinMotorcad(Mat_File_Path,objectName,plotType,level_contour)
%% dev
% Mat_File_Path=originMat.ElecMatFileList{:}
    %% 데이터 로드
    if ischar(Mat_File_Path)&&contains(Mat_File_Path,'.mat')
    data       =            load(Mat_File_Path)                ; % MAT 파일 로드
    elseif isstruct(Mat_File_Path)
        data=Mat_File_Path;
    end
    if all(size(data.(objectName))==size(data.Speed))&&~isempty(data.(objectName))
    Speed               =            data.Speed                ; % 속도
    Shaft_Torque        =            data.Shaft_Torque         ; % 축 토크         
    data4Plot          =            data.(objectName)           ; % 효율     
    if nargin<4
        level_contour=20;
    end
    %% MotorCad 그래프 작성
    % plot3(Shaft_Torque,Speed,Efficiency,'o')
    % contourf(Speed,Shaft_Torque,Efficiency);
    % h = zeros(1,3);
    % 
    % if length(unique(Efficiency))==1
    % [h(1)]=surface(Speed, Shaft_Torque, Efficiency,"EdgeColor",'none');
    % else
    %     % 등고선 설정    
    %     [~,h(1)]=contourf(Speed, Shaft_Torque, Efficiency, 'EdgeColor', 'none', 'DisplayName', objectName);
    %     hold on
    %     if strcmp(objectName,'Efficiency')
    %     % 효율성 등고선 플롯
    %     cntrs = [92:2:96 96:0.25:round(max(max(Efficiency)))];
    %     [~, h(2)] = contour3(Speed, Shaft_Torque, Efficiency, cntrs, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStepMode','auto');
    %     hold on
    %     contourf(Speed, Shaft_Torque, Efficiency, 'levels', 1000, 'EdgeColor', 'none', 'DisplayName', objectName);
    %     else
    %     [~,h(2)]  = contour3(Speed, Shaft_Torque, Efficiency, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStepMode','auto');
    %     end
    % end

    if length(unique(data4Plot))==1
        [h(1)]=surface(Speed, Shaft_Torque, data4Plot, "EdgeColor", 'none');
    else
        % contourf의 레벨을 설정합니다.
        minValue = min(data4Plot(:));
        data_without_min = data4Plot(data4Plot ~= minValue);
        secondMinValue = min(data_without_min);
        maxValue = max(data4Plot(:));
        data_without_max = data4Plot(data4Plot ~= maxValue);
        secondMaxValue = max(data_without_max);

        levels_contourf = linspace(secondMinValue, secondMaxValue, level_contour);
        % 등고선 설정

        if strcmp(objectName, 'Efficiency')
            % 효율성 등고선 플롯
            cntrs = [0:25:80 80:4:96 96:0.25:round(max(max(data4Plot)))];
            levels_contour3 = cntrs(1:2:end);  % 간격을 한 칸씩 띄웁니다.
            % contour3의 레벨을 설정합니다.
            [C,h(1)]=contourf(Speed, Shaft_Torque, data4Plot, cntrs, 'EdgeColor', 'none', 'DisplayName', objectName);
            hold on
            [C, h(2)] = contour3(Speed, Shaft_Torque, data4Plot, levels_contour3, 'EdgeColor', 'k',"ShowText",true,"LabelFormat","%0.2f");%  'ShowText', 'on'
            clabel(C,h(2),'FontName','Times New Roman');
        elseif strcmp(objectName,'Power_Factor')
        cntrs = [0:0.1:0.85 0.8:0.01:round(max(max(data4Plot)))];
            levels_contour3 = cntrs(1:2:end);  % 간격을 한 칸씩 띄웁니다.
            % contour3의 레벨을 설정합니다.
            [C,h(1)]=contourf(Speed, Shaft_Torque, data4Plot, cntrs, 'EdgeColor', 'none', 'DisplayName', objectName);
            hold on
            [C, h(2)] = contour3(Speed, Shaft_Torque, data4Plot, levels_contour3, 'EdgeColor', 'k',"ShowText",true,"LabelFormat","%0.2f");%  'ShowText', 'on'
            clabel(C,h(2),'FontName','Times New Roman');

        else
            % contour3의 레벨을 설정합니다.
            levels_contour3 = levels_contourf(1:round(level_contour/5):end);  % 간격을 한 칸씩 띄웁니다.
            [C,h(1)]=contourf(Speed, Shaft_Torque, data4Plot,levels_contourf, 'EdgeColor', 'none', 'DisplayName', objectName);
            hold on
            [C, h(2)] = contour3(Speed, Shaft_Torque, data4Plot, levels_contour3, 'EdgeColor', 'k',"ShowText",true,"LabelFormat","%0.2f");%  'ShowText', 'on'
            clabel(C,h(2),'FontName','Times New Roman');
        end
    end
    % contourf(Speed, Shaft_Torque, Efficiency,  'EdgeColor', 'none', 'DisplayName', objectName);
    % hold on
    % % [~, ~] = contour3(Speed, Shaft_Torque, Efficiency, cntrs, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStep', 2);
    % [~, ~] = contour3(Speed, Shaft_Torque, Efficiency, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStep', 2);
    % 
    % 
    %% Plot 양식
    % clim([80 100]);
    xlabel('Speed, [RPM]'); 
    ylabel('Torque, [Nm]'); 
    set(gcf, 'renderer', 'zbuffer');
    title([replaceUnderscoresWithSpace(objectName)]);


    %% 컬러맵 설정
    % 색상값 범위 설정
    cmin = 0;
    cmax = 1;

    % 컬러맵 생성
    n = 256;  % 색상 수
    cmap = jet(n);
    ind = round(1 + (n-1) * (cmax-cmin) / (cmax-cmin+eps));
    cmap = cmap(1:ind,:);

    % 적용
    colormap(cmap);
    
    % 컬러바 위치 설정
    cb = colorbar('Location', 'eastoutside');
    cb.Label.String = 'value';

    % legend(replaceSpacesWithUnderscores(objectName), 'Location', 'northeast');
    % legend();

    legend(h(1)); % Only display last two legend titles
    legend(strrep(objectName,'_',' '), 'Location', 'northeast'); % Only display last two legend titles


    % legend(replaceUnderscoresWith(objectName), 'Location', 'northeast');
     % title(objectName,'Visible','off');
        

    % 과학적 표기법 포맷
    formatter_sci;
    view(0,90); % 시야각 조절
    
    % 텍스트 핸들 가져오기
    % [C, h(2)] = contour3(Speed, Shaft_Torque, Efficiency, levels_contour3, 'EdgeColor', 'k');
    

 
    % % 각 텍스트의 자리수 조절
    % for k = 1:length(textHandles)
    %     value = str2double(textHandles(k).String);
    %     textHandles(k).String = sprintf('%.2f', value);  % 소수점 한 자리로 조절
    % end
    
    if nargin<3    
    title('')
    end
    end
    %% (예시) 기존 그래프 설정 로드
    % InfoMat=load('EffimapMeasureInfo.mat')
    % m1no=gca;
    % m1no.XLim=figInfo.xLim ;
    % m1no.YLim=figInfo.yLim ;
    % m1no.XTick= figInfo.xTick;
    % m1no.YTick= figInfo.yTick;
    % cellstr(get(gca,'XTickLabel'));=figInfo.xTickLabel
    % cellstr(get(gca,'YTickLabel'));=figInfo.yTickLabel
    % m1no1=gcf;
    % m1no1.Position=figInfo.size;
end
