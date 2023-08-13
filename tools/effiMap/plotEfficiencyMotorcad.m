function Mat_File_Data=plotEfficiencyMotorcad(Mat_File_Path)
    %% 데이터 로드
    Mat_File_Data       =            load(Mat_File_Path)                ; % MAT 파일 로드
    Speed               =            Mat_File_Data.Speed                ; % 속도
    Shaft_Torque        =            Mat_File_Data.Shaft_Torque         ; % 축 토크         
    Efficiency          =            Mat_File_Data.Efficiency           ; % 효율     
    %% MotorCad 그래프 작성
    % plot3(Shaft_Torque,Speed,Efficiency,'o')
    % contourf(Speed,Shaft_Torque,Efficiency);

    % 등고선 설정
    cntrs = [92:2:96 96:0.25:round(max(max(Efficiency)))];
    
    % 효율성 등고선 플롯
    contourf(Speed, Shaft_Torque, Efficiency, 'levels', 0.25, 'EdgeColor', 'none', 'DisplayName', 'Efficiency Contour');
    hold on
    [~, ~] = contour3(Speed, Shaft_Torque, Efficiency, cntrs, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStep', 2);
    
    
    %% Plot 양식
    clim([80 100]);
    xlabel('Speed, [RPM]'); 
    ylabel('Torque, [Nm]'); 
    set(gcf, 'renderer', 'zbuffer');
    
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
    cb.Label.String = 'Efficiency [%]';
    
    legend('Efficiency Contour', 'Location', 'northeast');
    
    % 과학적 표기법 포맷
    formatter_sci;
    view(0,90); % 시야각 조절
    
    
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
