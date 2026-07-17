%% runLabEffmaps_fig15.m — Fig 15 효율맵 소스 3종 일괄 계산
% Motor-CAD Lab 모듈 효율맵(EmagneticCalcType_Lab=1)을 세 모델에서 순차
% 실행하고 MotorLAB_elecdata.mat을 map_exports/e10/effmaps/에 수집한다.
%   Ref        : e10Turn6V261.mot                     (48pt Lab, Hybrid)
%   SC_hyb     : e10Turn6V261SLFEA_Lab48.mot          (48pt Lab, Hybrid)
%   SC_fullfea : e10Turn6V261SLFEA_FullFEA_LAB.mot    (48pt Lab, FullFEA)
% 드라이브 설정(Vdc, 제어전략)은 각 .mot 저장값 유지, 로그로만 확인.
% 참고 플로우: runAFCustomLossLab.m S5 (baseline 효율맵)

scriptDir = fileparts(mfilename('fullpath'));
outDir = fullfile(scriptDir, 'map_exports', 'e10', 'effmaps');
if ~isfolder(outDir), mkdir(outDir); end

jobs = { ...
  'Ref',        'D:\KangDH\Thesis\e10\refModel\e10Turn6V261.mot',              460; ...
  'SC_hyb',     'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_Lab48.mot',      920; ...
  'SC_fullfea', 'D:\KangDH\Thesis\e10\SLFEA\e10Turn6V261SLFEA_FullFEA_LAB.mot', 920};

for j = 1:size(jobs, 1)
    tag = jobs{j, 1}; motPath = jobs{j, 2}; imax = jobs{j, 3};
    outMat = fullfile(outDir, sprintf('MotorLAB_elecdata_%s.mat', tag));
    if isfile(outMat)
        fprintf('[skip] %s 이미 존재\n', outMat);
        continue
    end
    assert(isfile(motPath), '.mot 없음: %s', motPath);
    fprintf('=== [%d/3] %s: %s (Imax %d A)\n', j, tag, motPath, imax);

    mcadApp = actxserver('motorcad.appautomation');
    cleaner = onCleanup(@() tryQuit(mcadApp));   %#ok<NASGU>
    mcadApp.SetVariable('MessageDisplayState', 2);
    mcadApp.LoadFromFile(motPath);
    [~, isBuilt] = mcadApp.GetModelBuilt_Lab();
    fprintf('  Lab 빌드 상태: %d\n', double(isBuilt));
    assert(double(isBuilt) == 1, 'Lab 모델이 빌드되지 않음: %s', tag);

    mcadApp.SetMotorLABContext();
    mcadApp.SetVariable('EmagneticCalcType_Lab', 1);   % Efficiency Map
    mcadApp.SetVariable('SpeedMin_MotorLAB', 0);
    mcadApp.SetVariable('SpeedMax_MotorLAB', 16000);
    mcadApp.SetVariable('Speedinc_MotorLAB', 500);
    mcadApp.SetVariable('CurrentSpec_MotorLAB', 1);    % RMS
    mcadApp.SetVariable('Imax_RMS_MotorLAB', imax);
    mcadApp.SetVariable('Imin_MotorLAB', 0);
    for v = {'DCBusVoltage', 'ControlStrat_MotorLAB', ...
             'ModulationIndex_MotorLAB', 'OperatingMode_Lab', ...
             'MaxModulationIndex_MotorLAB'}
        try
            [~, val] = mcadApp.GetVariable(v{1});
            fprintf('  %s = %s\n', v{1}, num2str(double(val)));
        catch
        end
    end

    fprintf('  효율맵 계산 시작 ...\n');
    tStart = tic;
    mcadApp.CalculateMagnetic_Lab();
    fprintf('  계산 완료 (%.1f s)\n', toc(tStart));

    [~, labResultDir] = mcadApp.GetVariable('ResultsPath_MotorLAB');
    srcMat = fullfile(strtrim(char(labResultDir)), 'MotorLAB_elecdata.mat');
    assert(isfile(srcMat), 'Lab 결과 mat 없음: %s', srcMat);
    copyfile(srcMat, outMat);
    fprintf('  저장: %s\n', outMat);

    tryQuit(mcadApp);
    clear cleaner mcadApp
end
fprintf('done — 3 elecdata mats in %s\n', outDir);

function tryQuit(app)
try
    app.Quit();
catch
end
end
