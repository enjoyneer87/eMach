% devSettingJplotReader

% main("path_to_your_jplot_file.jplot", 16001) 
% % # 주석 처리된 예시, 실제 사용 시 주석 해제
% setPythonEnv('jmag')
% pyversion
% 
% % Jplot 파일 경로와 postkey ID를 설정
% % jplot_file_path = 'C:\path\to\your\file.jplot';
% jplot_file_path='Z:\Simulation\JEETACLossValid_e10_v24\refModel\e10_v24.jfiles\ref_e10_Coil~16\ref_e10_Coil_Load~25\Case1\Designer.jplot'
% postkey_id = 16001;
% 
% % Python 모듈 import 및 함수 호출
% mainJplotReader = py.importlib.import_module('mainJplotReader');  % 파일명(mainJplotReader)을 모듈로 import
% mainJplotReader.main(jplot_file_path, postkey_id);  % main 함수를 호출


%% matlab 2024a에서 python 3.8 미지원으로 인해 vscode에서 실행

outputMatPath='Z:\01_Codes_Projects\git_Pyleecan_fork\output_data.mat'

AData=load(outputMatPath)