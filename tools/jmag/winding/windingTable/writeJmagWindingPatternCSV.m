function outputPath=writeJmagWindingPatternCSV(CoilTable, outputPath)
    % coilStruct: Coil 구조체 배열
    % readPropertiesTable: 원래 읽어들인 테이블
    % outputPath: 새로 생성할 CSV 파일의 경로 및 이름
    % readPropertiesTable;
    % outputPath='Z:\01_Codes_Projects\git_fork_emach\tools\jmag\testJmagPattern02.csv'

    % 테이블을 CSV 파일로 저장
    writetable(CoilTable, outputPath, 'Delimiter', ',', 'WriteVariableNames', false);
end