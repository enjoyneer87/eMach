function scaledResistanceValue = scaleResistancebyTemp(resistance, temperature, tempInitial,alpha)
    % resistance: 원래 저항 값
    % temperature: 스케일링할 온도 값
    % varargin: 추가 인자 (alpha, T0)
    
    % 기본값 설정
    WindingAlpha_MotorLAB = 0.003862;  % 기본 온도 계수
    % WindingAlpha_MotorLAB=0.00393;
    T0 = 20;           % 기본 기준 온도

    % 입력된 옵션 처리
    if nargin > 2
        % if ~isempty(varargin{1})
            T0=tempInitial;
        % end
    end
    if nargin > 3
        % if ~isempty(varargin{2})
            % alpha = varargin{2};
            WindingAlpha_MotorLAB=alpha;
        % end
    end
    
    % 스케일링된 저항 계산
    % 온도 계수 (alpha)
    alpha = WindingAlpha_MotorLAB; % 여기에 적절한 값을 할당하세요.
    
    % 참조 온도 (Tref), 일반적으로 20도로 가정할 수 있지만, 필요에 따라 변경 가능
    Tref = T0;
    
    % 계산하려는 온도 (Tcalc)
    Tcalc = temperature; % 여기서 'temperature'는 계산하려는 온도 변수
    
    % 참조 온도에서의 직류 저항 (Rdc^Tref), 이는 'resistance' 변수로 주어짐
    Rdc_Tref = resistance; % 여기서 'resistance'는 참조 온도에서의 저항값
    
    % 계산된 새로운 저항값 (Rph) 계산
    Rph = (1 + alpha * (Tcalc - 20)) / (1 + alpha * (Tref - 20)) * Rdc_Tref;


    scaledResistanceValue = Rph;

    % scaledResistanceValue = resistance .* (1 + WindingAlpha_MotorLAB * (temperature - T0));
    % scaledResistance = sprintf('%.16f', scaledResistanceValue);

end