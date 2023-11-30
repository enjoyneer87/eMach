function importJMAGCoilsFromCSV(fileName)
    % winding_aa
    % pyrunfile("pySlotPoleWireTemplate.py")
    % filename = 'your_file.csv';

% pyrunfile('winding_aa.py', 'fname', fname); % Python 스크립트를 호출하고 fname을 전달
% fileName = "Z:\01_Codes_Projects\git_fork_emach\tools\jmag\aaa.csv"; % MATLAB에서 파일 이름을 정의); % main 함수 호출 및 fname 전달

    pyrunfile('winding_aa.py', 'fname', fileName)


    % % fname: CSV 파일 경로
    % 
    % % Import JMAG COM Server
    % % app = actxserver('JMAG.DesignAutomation');
    % 
    % % 현재 스터디 가져오기
    % study=app.GetModel(0).GetStudy(0);
    % 
    % % study = app.GetCurrentStudy();
    % 
    % if study.GetWinding(0).IsValid()
    %     study.GetWinding(0).RemoveAllCoils();
    % 
    %     % CSV 파일에서 코일 정보 읽어오기
    %     ncoil = convertJMAGWindingCSV2Array(fname);
    % 
    %     for i = 1:length(ncoil)
    %         coilName = sprintf('Coil_%d', i);
    % 
    %         % 코일 생성 및 설정
    %         study.GetWinding(0).CreateCoil(coilName);
    %         coil = study.GetWinding(0).GetCoil(i - 1);
    %         coil.SetPhaseIndex(i - 1);
    %         coil.SetSerialGroupIndex(0);
    %         coil.SetTable(ncoil(i));
    %     end
    % end
    % 
    % % JMAG COM Server 종료
    % % app.Quit();
end
