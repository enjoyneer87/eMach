function scaledResistance = scaleResistancebyTemp(resistance, temperature, tempInitial,alpha)
    % resistance: 원래 저항 값
    % temperature: 스케일링할 온도 값
    % varargin: 추가 인자 (alpha, T0)
    
    % 기본값 설정
    % alpha = 0.003862;  % 기본 온도 계수
    WindingAlpha_MotorLAB=0.00393;
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
    scaledResistance = resistance .* (1 + WindingAlpha_MotorLAB * (temperature - T0));
end