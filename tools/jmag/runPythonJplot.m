function runPythonJplot(jplot_file_path, totalSteps)
    % Python 코드가 있는 폴더 경로 설정
    pythonFolder = 'C:\Program Files\JMAG-Designer23.1\Tools\JPlotReader\samples\Python';  % Python 파일 경로
    % Python 모듈을 찾기 위한 경로 추가
    pyrun("import sys; sys.path.append('C:/Program Files/JMAG-Designer23.1/Tools/JPlotReader/samples/Python')");
    
    % Python 모듈에서 main 함수를 불러오기
    pyrun("from mainJplotReader import main");  % mainJplotReader.py의 main 함수 가져오기

    % Python의 main 함수 실행
    pyrun("main(jplot_file_path, totalSteps)", ...
          "jplot_file_path", jplot_file_path, ...
          "totalSteps", totalSteps);

    disp('Python code executed and .mat file saved.');
end