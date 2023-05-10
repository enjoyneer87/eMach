function result=exportMotorcadResult(obj)
%% from motorcadResultExport.m -> 1. Calculation Options 2. Mag Calculation Fidelity 3. PointPer Cycle 4. Saving File 5.  Do Simulate if not done 6. Export Point data to csv file
% move 2 to simulation option apply fcn
% change 3 to get pointperCycle from .mot file
% delete 4. saving file  ( fcn simulation option에서 저장)
% Do simulate if not done -> SaveResults를 해서 Result가 되면 실행안하고 save안되면 해석하도록 변경 
% extractGraphMotorCAD fcn
%% InitInit
app = actxserver('MotorCAD.AppAutomation');

%% PointPer Cycle -> 만약 input에서 출력정보를 입력받으면 str을 읽어들여서 cycle 추출하기 

[done,PointsPerCycle]=app.GetVariable('BackEMFPointsPerCycle');
[done,NumberCycles]=app.GetVariable('BackEMFNumberCycles');

%% Do Simulate if not done (주의 Save데이터가 있어서 overwrite 메세지뜨면 yes 눌러야됨, no 누르면 다시 해석됨)
saved = app.SaveResults("EMagnetic");

if saved == 0  
        disp("결과가 저장되었습니다.");
else saved == -1
    disp("결과가 없습니다.");
    Calculated = app.DoMagneticCalculation();
    saved = 0;
    
end

%%  Export Point data to csv file (graph or point value)

% 체크할 폴더 경로
% folderPath = filename;
[success,folderPath]=app.GetVariable('CurrentMotFileDir_MotorLAB')


%% extract Graph 
simulInfo.PointsPerCycle=PointsPerCycle;
simulInfo.NumberCycles=NumberCycles;


if class(obj) == 'CalibrationMotorCAD'
   setGraphName={obj.calibrationObjectName};
   result=extractGraphMotorCad(simulInfo,setGraphName);
        
end
% output_strc.res=res
% % for i=1:length(data_names(TF))

 pause(1) 
end 


