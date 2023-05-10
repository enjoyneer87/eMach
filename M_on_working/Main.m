format long

%% -------------------------�ʱ�ȭ-------------------------
clear; 
clc;
addpath('function\');
%%
delete('Output/*.csv');
% delete_idiq                       % idiq�� emf���� ������ ���� �Ҷ� Ȱ��ȭ
% delete_loss_data                  % �� ������ Loss Data ���� �Ҷ� Ȱ��ȭ

%% --------------------------�Է�--------------------------

Input.skew=1;                                                               % Skew ���� ���� �� 1, ������� 0
Input.skew_floor=2;                                                         % Skew �ܼ� ����
Input.skew_angle=5;                                                      % Skew ������ ���� ����

Input.i_s = 0.1;                                                             % id,iq ���� ���� ũ��
Input.interval = 25;                                                        % id,iq ���� ����
Input.d_interval = 80;                                                     % id,iq ���� ���� ���� ũ�� 

Input.p=12;                                                                  % �ؼ�
Input.base_rpm=1700;                                                        % Base RPM
Input.mode_w=1;                                                             % �Ǽ� ��� : UWV = -1, UVW = 1
Input.mode_m=2;                                                             % ��� ��� : 1,2,3,4�и� (dq ��ǥ��)
Input.initial_angle=0;                                                    % Initial Angle ����

Input.Vmax = 750*0.85/sqrt(3);                                              % ������ ����
Input.i_max = 900;                                                          % ���� ����
Input.Rs = 0.0100497;                                                     % Rs����

% ��Ƽ�� ��Ʈ�� ������� ���׺� ���ϱ� ����
Input.Stack = 130;                                                         % �������� (���� X)
Input.End_Winding = 70;                                                     % ����� ����
Input.Stack_Margin = 0.97;                                                  % ������ ��������

Input.freq = [0.1:100:5500];                                               % ���ɰ RPM ����
Input.RPM = [100:100:5500];                                           % ȿ���� RPM ����          
Input.torque = [10:20:1400];                                                        % ȿ���� ��ũ ����

Input.steps=20;                                                             % Lamda ���� ���� (�ѽ��� -1)
Input.core_loss_step = 129;                                                 % Coreloss ���� ����

Input.AC = 0;                                                               % AC���� �ݿ� ���� ���� 0 : �̻��, 1: ���
Input.Mech=0;                                                               % ���� �ݿ� ���� ���� 0 : �̻��, 1: ���
Input.iter=2;                                                               % �ս��ؼ� �ֱ� ����

Input.Mech_Loss = 'Mech_Loss.xlsx';                                           % ���� �Է� ���� ���ϸ� 
Input.Motion_condi='Motion';                                                 % Motion Condition �̸�
Input.Iron_condi_Stator ='Stator';                                      % Iron Loss Condition �̸�
Input.Iron_condi_Rotor ='Rotor';
Input.JMAG_name_for_lamda = '210616_HDEV_1yr_4th_model_11T_LdLq_20deg.jproj';                    % Lamda ���� JMAG ���ϸ�
% Input.JMAG_name_for_loss = 'HDEV_201019_LdLq_Loss.jproj';                % Coreloss ���� JMAG ���ϸ� 
% Input.JMAG_name_for_AC_loss = '180314_s4v4r9_LdLq_Loss_7T3P_AC.jproj';            % AC Loss ���� JMAG ���ϸ� 

Input.torque_ripple=120/Input.p;
Input.Max_torque = 0;
Input=id_iq_map(Input);                                                   

Input

%% --------------------------Lamda a,b,c ���� JMAG script ���� �� JMAG����

make_vbs_for_lamda(Input);

%% --------------------------Lamda-d Lamda-q ���(in_power ����)

in_power = trans_fun(Input);

%% --------------------------EMF �ؼ��� ���� JMAG ����

[Lamda_fd] = make_vbs_for_emf(Input);

%% --------------------------���ɰ(characteristic_curve ����)

[characteristic_curve, Max_Torque]=get_power_fun(Input,in_power);

%% --------------------------ȿ��� Map(Effy_Map ����)

Effy_Map=Effy_map_fun(Input,in_power);

%% --------------------------Core_Loss ���� JMAG script ���� �� JMAG����

make_vbs_for_loss(Input,Effy_Map);

%% --------------------------ȿ���

Total_Effy = cal_effy(Input,Effy_Map,Lamda_fd);
