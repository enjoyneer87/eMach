function savePartIDToMat(partID, jplot_file_path)
    % savePartIDToMat - partID 목록을 .mat 파일로 저장하는 함수
    %
    % partIDs: partID들의 배열 또는 목록
    % jplot_file_path: jplot 파일 경로 (확장자를 .mat으로 변경해 동일한 이름의 mat 파일로 저장)
    
    % jplot_file_path에서 .mat 파일 이름으로 변경
    [folder, name, ~] = fileparts(jplot_file_path);  % 확장자 제외한 경로 및 파일명 추출
    mat_file_path = fullfile(folder, [name, '.mat']); % .mat 파일 경로 생성
    
    % partIDs 변수를 .mat 파일로 저장
    try
        save(mat_file_path, 'partID');  % partIDs라는 이름으로 .mat 파일에 저장
        fprintf('Part IDs successfully saved to %s\n', mat_file_path);
    catch ME
        fprintf('Error saving part IDs to .mat file: %s\n', ME.message);
    end
end