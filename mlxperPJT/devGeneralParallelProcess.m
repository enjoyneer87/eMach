%% 파일목록 만들기
% 해석셋팅 목록만들기, 속도
% 목록만들기, 기존에 DOE테이블처럼 만들기
% 파일복사
% 병렬로
% Load 
% set


%%  getMCADData4ScalingList s내부 함수실행
Obj_SLLAWLabList_8p48sVV                               =MCADBuildList(refPath);
% 
getLabBuildDateFromMotFile(refPath)

MCADrunManager
    NumMCAD
    runListTable
    MCADInstance


Obj_SLLAWLabList = MCADBuildList(refDir);
buildListTable=Obj_SLLAWLabList.toTable;
            SLLAWmotorCADManager = MCADLabManager(6, buildListTable);

%% 
    refDir='F:\KDH\Thesis\JEET\e10\refModel\'
    refPath="F:\KDH\Thesis\JEET\e10\refModel\e10_UserRemesh.mot";
  
    %% 참고
    input2GetData=refDir
    BuildList               =getMCADData4ScalingList(refPath);
    [Data2Scaling4Building, filteredLabTable4Scaling] = getMCADData4ScalingFromMotFile(refPath);
%% option에 따라 해석돌리기
% 해석이 되어있지 않으면 돌리기




%% 기존에 파일이 해석되어있지않으면 해석
% 열려고하는 파일이 이미 열려있으면 그냥해석




%% 데이터 추출 > 파일로부터 추출! or 열려있으니까 그냥가져오기 