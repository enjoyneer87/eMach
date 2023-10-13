function DOEScaledBuild = devExportWeightFromMCAD4DOEStrct(motFileList,RefGearMass,HousingMass, mcad,varagin)

if nargin==6
    DOEScaledBuild=varagin;
else
    DOEScaledBuild=struct();
end

for i=1:length(motFileList)
    str = motFileList{i};
    startIndex = strfind(str, 'Design') + length('Design');
    if ~isempty(startIndex)
        startIndex=startIndex(end);
        endIndex = strfind(str, '.mot') - 1;
        numberStr = str(startIndex:endIndex);
        number = str2double(numberStr);
        % calc
        if ~isnan(number)
            % 빈 구조체 이름 생성
            structName = ['Design', num2str(number)];
            
            % 빈 구조체 생성 및 DOE 구조체에 추가

            % MotorCAd 호출 
                mcad.LoadFromFile(motFileList{i})
                DesignWeight=getMCADWeight(mcad);
                DOEScaledBuild.(structName).Weight=DesignWeight;
                % Gear Mass 무게 계산
                [~,N_d_MotorLAB]=mcad.GetVariable('N_d_MotorLAB');
                TeslaSPlaidDutyCycleTable=defMcadDutyCycleSetting;
                RefGearRatio = findMcadTableVariableFromAutomationName(TeslaSPlaidDutyCycleTable, 'N_d_MotorLAB');
                ModifiedGearWeight=calculateModifiedGearMass(7, N_d_MotorLAB,7, RefGearRatio,RefGearMass);
                ModifiedGearBoxMass=HousingMass+ModifiedGearWeight;
                DOEScaledBuild.(structName).Weight.TotalEDUWeight=ModifiedGearBoxMass+DesignWeight.o_Weight_Act;
        else
            disp(['Invalid number in string: ', str]);
        end
    end
end
end