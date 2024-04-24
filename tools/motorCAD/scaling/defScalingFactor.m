function Factor = defScalingFactor(k_radial, k_axial, defineType, varargin)
    Factor.k_Axial = k_axial;  % Axial 방향 스케일링 팩터
    Factor.k_Radial = k_radial;  % Radial 방향 스케일링 팩터

    if defineType == 0
        if nargin < 4
            error('defineType 0에 대한 충분한 입력 인수가 없습니다.');
        end
        Factor.k_Winding = varargin{1};  % Winding 스케일링 팩터
    elseif defineType == 1
        if nargin < 5
            error('defineType 1에 대한 충분한 입력 인수가 없습니다.');
        end
        Factor.turns_per_coil = varargin{1};  % 턴당 코일 수
        Factor.a_p = varargin{2};  % a_p (병렬 경로)
    elseif defineType == 2 % 전체턴수 입력
        if nargin < 7
            error('defineType 2에 대한 충분한 입력 인수가 없습니다.');
        end
        Factor.turns_per_coil = varargin{1};  % 턴당 코일 수
        Factor.a_p = varargin{2};  % a_p (병렬 경로)
        n_c_ref = varargin{3};  % n_c_ref (참조값)
        a_p_ref = varargin{4};  % a_p_ref (참조값)
        Factor.k_Winding = (Factor.turns_per_coil / Factor.a_p) / (n_c_ref / a_p_ref);  % Winding 스케일링 팩터 계산
    elseif defineType == 3
        if nargin < 4
            error('defineType 3에 대한 충분한 입력 인수가 없습니다.');
        end
        Factor.turns_per_coil = varargin{1};  % 턴당 코일 수
        Factor.a_p = varargin{2};  % a_p (병렬 경로)
        MotorCADGeo = varargin{3};  % MotorCADGeo 데이터 입력

        if MotorCADGeo.Armature_CoilStyle == 0
            n_c_ref = double(MotorCADGeo.MagTurnsConductor); % turn per Coil
        elseif MotorCADGeo.Armature_CoilStyle == 1
            n_c_ref = MotorCADGeo.WindingLayers;
        end

        a_p_ref = double(MotorCADGeo.ParallelPaths); % Parallel Path
        Factor.k_Winding = (Factor.turns_per_coil / Factor.a_p) / (n_c_ref / a_p_ref);  % Winding 스케일링 팩터 계산
    else
        error('잘못된 defineType입니다. 0, 1, 2 또는 3이어야 합니다.');
    end
end
