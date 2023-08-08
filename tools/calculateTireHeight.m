function tire_Radius = calculateTireHeight(tire_spec)
    % 타이어 규격으로부터 타이어의 높이를 계산하는 함수
    
    % 타이어 규격 문자열을 "/"를 기준으로 분할
    specs = strsplit(tire_spec, '/');
    
    % 폭, 높이, 반지름 값을 추출
    width = str2double(specs{1}); %[mm] 
    width = mm2m(width);%[m]
    aspect_ratio = str2double(specs{2});
    WheelDia = inch2mm(str2double(strrep(specs{3}, 'R', '')));  % [mm]
    WheelDia = mm2m(WheelDia);   %[m]
    % 타이어 높이 계산 (폭 * 높이 비율 * 2 * 반지름)
    tire_height = 2*(width * aspect_ratio / 100) + (WheelDia);
    tire_Radius = tire_height/2 ;
end
