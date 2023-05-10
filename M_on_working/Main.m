format long

%% -------------------------초기화-------------------------
clear; 
clc;
addpath('function\');
%%
delete('Output/*.csv');
% delete_idiq                       % idiq및 emf폴더 데이터 삭제 할때 활성화
% delete_loss_data                  % 각 폴더의 Loss Data 삭제 할때 활성화

%% --------------------------입력--------------------------

Input.skew=1;                                                               % Skew 설정 적용 시 1, 미적용시 0
Input.skew_floor=2;                                                         % Skew 단수 설정
Input.skew_angle=5;                                                      % Skew 적용할 각도 설정

Input.i_s = 0.1;                                                             % id,iq 시작 전류 크기
Input.interval = 25;                                                        % id,iq 전류 간격
Input.d_interval = 80;                                                     % id,iq 전류 간격 보간 크기 

Input.p=12;                                                                  % 극수
Input.base_rpm=1700;                                                        % Base RPM
Input.mode_w=1;                                                             % 권선 모드 : UWV = -1, UVW = 1
Input.mode_m=2;                                                             % 기기 모드 : 1,2,3,4분면 (dq 좌표계)
Input.initial_angle=0;                                                    % Initial Angle 설정

Input.Vmax = 750*0.85/sqrt(3);                                              % 상전압 제한
Input.i_max = 900;                                                          % 전류 제한
Input.Rs = 0.0100497;                                                     % Rs설정

% 액티브 파트와 엔드부의 저항비를 구하기 위함
Input.Stack = 130;                                                         % 적층길이 (마진 X)
Input.End_Winding = 70;                                                     % 엔드부 길이
Input.Stack_Margin = 0.97;                                                  % 적층의 마진비율

Input.freq = [0.1:100:5500];                                               % 성능곡선 RPM 간격
Input.RPM = [100:100:5500];                                           % 효율맵 RPM 간격          
Input.torque = [10:20:1400];                                                        % 효율맵 토크 간격

Input.steps=20;                                                             % Lamda 추출 스텝 (총스텝 -1)
Input.core_loss_step = 129;                                                 % Coreloss 추출 스텝

Input.AC = 0;                                                               % AC동손 반영 여부 결정 0 : 미사용, 1: 사용
Input.Mech=0;                                                               % 기계손 반영 여부 결정 0 : 미사용, 1: 사용
Input.iter=2;                                                               % 손실해석 주기 설정

Input.Mech_Loss = 'Mech_Loss.xlsx';                                           % 기계손 입력 엑셀 파일명 
Input.Motion_condi='Motion';                                                 % Motion Condition 이름
Input.Iron_condi_Stator ='Stator';                                      % Iron Loss Condition 이름
Input.Iron_condi_Rotor ='Rotor';
Input.JMAG_name_for_lamda = '210616_HDEV_1yr_4th_model_11T_LdLq_20deg.jproj';                    % Lamda 추출 JMAG 파일명
% Input.JMAG_name_for_loss = 'HDEV_201019_LdLq_Loss.jproj';                % Coreloss 추출 JMAG 파일명 
% Input.JMAG_name_for_AC_loss = '180314_s4v4r9_LdLq_Loss_7T3P_AC.jproj';            % AC Loss 추출 JMAG 파일명 

Input.torque_ripple=120/Input.p;
Input.Max_torque = 0;
Input=id_iq_map(Input);                                                   

Input

%% --------------------------Lamda a,b,c 추출 JMAG script 생성 후 JMAG실행

make_vbs_for_lamda(Input);

%% --------------------------Lamda-d Lamda-q 계산(in_power 생성)

in_power = trans_fun(Input);

%% --------------------------EMF 해석을 위한 JMAG 실행

[Lamda_fd] = make_vbs_for_emf(Input);

%% --------------------------성능곡선(characteristic_curve 생성)

[characteristic_curve, Max_Torque]=get_power_fun(Input,in_power);

%% --------------------------효율곡선 Map(Effy_Map 생성)

Effy_Map=Effy_map_fun(Input,in_power);

%% --------------------------Core_Loss 추츌 JMAG script 생성 후 JMAG실행

make_vbs_for_loss(Input,Effy_Map);

%% --------------------------효율곡선

Total_Effy = cal_effy(Input,Effy_Map,Lamda_fd);
