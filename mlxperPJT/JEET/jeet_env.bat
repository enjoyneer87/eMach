@echo off
rem 저자 로컬 환경 — 이 워크트리에서 그림/데이터가 원고·원자료 경로로 가게 한다.
rem (현재 cmd 세션에만 적용. 절대경로는 이 파일과 jeet_env.sh 에만 둔다.)
rem 사용:  call jeet_env.bat
set "JEET_FIGDIR=E:\KDH\Overleaf\JEET-2024_rev1\fig"
set "JEET_FEA_ROOT=D:\KangDH\Thesis\e10"
set "JEET_RESULTS_DIR=J:\내 드라이브\EveryMotor_JEET_data\results"
set "JEET_EFFMAP=D:\KangDH\EveryMotor\eMach\mlxperPJT\JEET\efficiency_map_results.mat"
echo JEET env set: FIGDIR=%JEET_FIGDIR%
