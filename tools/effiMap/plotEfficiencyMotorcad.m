function Mat_File_Data=plotEfficiencyMotorcad(Mat_File_Path)
    %%
    Mat_File_Data       =            load(Mat_File_Path)                ;
    Speed               =            Mat_File_Data.Speed                ;
    Shaft_Torque        =            Mat_File_Data.Shaft_Torque         ;            
    Efficiency          =            Mat_File_Data.Efficiency           ;        
    Shaft_Power         =            Mat_File_Data.Shaft_Power          ;        
    DC_Bus_Voltage      =            Mat_File_Data.DC_Bus_Voltage       ;       
    %% Plot MotorCad
    % plot3(Shaft_Torque,Speed,Efficiency,'o')
    % contourf(Speed,Shaft_Torque,Efficiency);
    
    
    cntrs = [92:2:96 96:0.25:round(max(max(Efficiency)))];
    contourf(Speed, Shaft_Torque, Efficiency, 'levels', 0.25, 'EdgeColor', 'none', 'DisplayName', 'Efficiency Contour');
    hold on
    [C, h] = contour3(Speed, Shaft_Torque, Efficiency, cntrs, 'EdgeColor', 'k', 'ShowText', 'on', 'TextStep', 2);
    
    
    %% Plot 양식
    caxis([80 100])
    xlabel('Speed, [RPM]'); 
    ylabel('Torque, [Nm]'); 
    set(gcf, 'renderer', 'zbuffer');
    
    %colormap
    % 색상값 범위 설정
    cmin = 0;
    cmax = 1;
    
    % 컬러맵 생성
    n = 256;  % 색상 수
    cmap = jet(n);
    ind = round(1 + (n-1) * (cmax-cmin) / (cmax-cmin+eps));
    cmap = cmap(1:ind,:);
    % 적용 예시
    colormap(cmap)
    
    
    % Colorbar 위치 설정
        cb = colorbar('Location', 'eastoutside');
    cb.Label.String = 'Efficiency [%]';
    
    lg=legend('Efficiency Contour', 'Location', 'northeast');
    % Scientific notation formatter
    formatter_sci;
    view(0,90); % 시야각 조절
    
    
    % InfoMat=load('EffimapMeasureInfo.mat')
    % m1no=gca;
    % m1no.XLim=figInfo.xLim ;
    % m1no.YLim=figInfo.yLim ;
    % m1no.XTick= figInfo.xTick;
    % m1no.YTick= figInfo.yTick;
    %   cellstr(get(gca,'XTickLabel'));=figInfo.xTickLabel
    %   cellstr(get(gca,'YTickLabel'));=figInfo.yTickLabel
    % 
    % m1no1=gcf;
    % m1no1.Position=figInfo.size;