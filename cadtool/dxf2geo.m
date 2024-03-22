function geoFileFullPath=dxf2geo(dxfPath)
    addpathGmsh
    %%
    [~,FileName,dxfext]=fileparts(dxfPath);
    filePath=[FileName,dxfext];
    geoFileDir=fullfile(pwd,'geoFile');
    newFilePath=fullfile(geoFileDir,filePath);
    copyfile(dxfPath,newFilePath);
    % dxf 2 geo in matlab
    %%
    dxfFile = newFilePath;  % 변환할 DXF 파일 경로와 파일 이름
    tolerance = 0.001;     % 허용 오차 값
    rotation = 0;          % 회전 각도 (선택)
    xOffset = 0;           % X 축 이동 (선택)
    yOffset = 0;           % Y 축 이동 (선택)
    %% move2 cadtool Path
    
    %% dxf2geo.exe 실행 명령 생성
    command = sprintf('dxf2geo.exe %s %f %d %f %f', newFilePath, tolerance, rotation, xOffset, yOffset);
    % 외부 명령 실`행
    system(command);
    if isfile(newFilePath)
    geoFilePath     =[FileName,'.geo'];
    geoFileFullPath =fullfile(geoFileDir,geoFilePath);
    else
        disp('생성되지 않았습니다.')
    end
end
