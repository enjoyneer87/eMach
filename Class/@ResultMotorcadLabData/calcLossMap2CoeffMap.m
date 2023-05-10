function [outputArg1,outputArg2] = calcLossMap2CoeffMap(inputobj)
%calcLossMap2CoeffMap Summary of this function goes here
%   ResultMotorcadLabData Method 
outputArg1 = inputArg1;
outputArg2 = inputArg2;
inputobj.LossParameters_MotorLAB.CoeffMap=[];
inputobj.LossParameters_MotorLAB.RawLossMap.FEALossMap_RefSpeed_Lab;
inputobj.LossParameters_MotorLAB.CoeffMap.CoeffUnit{1}='[W/Hz]'
inputobj.LossParameters_MotorLAB.CoeffMap.CoeffUnit{2}='[W/Hz^2]'



field_names = fieldnames(inputobj.LossParameters_MotorLAB.RawLossMap); % 필드 이름들 가져오기
data = cell(1, numel(field_names)); % 필드 데이터를 저장할 셀 배열 생성

for i = 1:numel(field_names)
    if contains(field_names{i}, 'Hy') % 필드 이름 검사
        data = inputobj.LossParameters_MotorLAB.RawLossMap.(field_names{i}); % 해당 필드 데이터 추출
        coeffFieldName = strcat('Coeffi_', field_names{i});
        f=(inputobj.p/2) * (inputobj.LossParameters_MotorLAB.RawLossMap.FEALossMap_RefSpeed_Lab)/60;
        coeffValues = inputobj.LossParameters_MotorLAB.RawLossMap.(field_names{i})./f;
        inputobj.LossParameters_MotorLAB.CoeffMap.(coeffFieldName) = coeffValues;
    end
end

for i = 1:numel(field_names)
    if contains(field_names{i}, 'Ed') % 필드 이름 검사
        data = inputobj.LossParameters_MotorLAB.RawLossMap.(field_names{i}); % 해당 필드 데이터 추출
        coeffFieldName = strcat('Coeffi_', field_names{i});
        f=(inputobj.p/2) * (inputobj.LossParameters_MotorLAB.RawLossMap.FEALossMap_RefSpeed_Lab)/60;
        coeffValues = inputobj.LossParameters_MotorLAB.RawLossMap.(field_names{i})./(f^2);
        inputobj.LossParameters_MotorLAB.CoeffMap.(coeffFieldName) = coeffValues;
    end
end


data = data(~cellfun('isempty', data)); % 빈 데이터 제거


end