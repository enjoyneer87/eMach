function [result] = calibrationMotorcadAnalysis(obj, x)
    % mc_input 구조체 내의 calibration 객체에서 multiplier 추출
    motorcadFilename=obj.file_name
    
    % 최적화 결과를 사용하여 multiplier 값을 조정
    adjusted_multiplier = x .* multiplier;
    
    % 새로운 calibration 구조체 생성
    new_calibration = Calibration(adjusted_multiplier);
    
    % 새로운 mc_input 구조체 생성
    new_mc_input = MotorCadInput(obj.mc_input.data_csv_path, new_calibration);
    
    % 새로운 mc_input 구조체를 사용하여 모터 캐드 해석 실행
    mcad = actxserver('MotorCAD.AppAutomation');
    
    result = new_mc_sim.execute(fmin, fmax);
end