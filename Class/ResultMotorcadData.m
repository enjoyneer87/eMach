classdef (Abstract) ResultMotorcadData < ResultData & MotorcadData
    methods
        % 생성자 메서드
        function obj = ResultMotorcadData(motorcadDataObj)
            % ResultMotorcadData의 생성자
            % MotorcadData 객체의 속성 전체를 상속받아 obj의 속성으로 설정
            obj = obj@MotorcadData(motorcadDataObj.p);
            obj.motorcadMotPath = motorcadDataObj.motorcadMotPath;
            obj.matfileFindList = motorcadDataObj.matfileFindList;
            obj.I1 = motorcadDataObj.I1;
            obj.I2 = motorcadDataObj.I2;
            obj.I3 = motorcadDataObj.I3;
            obj.Iabc = motorcadDataObj.Iabc;
            obj.FFT_Iabc = motorcadDataObj.FFT_Iabc;
            obj.u1 = motorcadDataObj.u1;
            obj.u2 = motorcadDataObj.u2;
            obj.u3 = motorcadDataObj.u3;
            obj.FFT_uabc = motorcadDataObj.FFT_uabc;
            obj.fluxlink_1 = motorcadDataObj.fluxlink_1;
            obj.fluxlink_2 = motorcadDataObj.fluxlink_2;
            obj.fluxlink_3 = motorcadDataObj.fluxlink_3;
            obj.FFT_fluxlinkabc = motorcadDataObj.FFT_fluxlinkabc;
            obj.elec_torque = motorcadDataObj.elec_torque;
            obj.shaft_torque = motorcadDataObj.shaft_torque;
            %
            obj.ModelParameters_MotorLAB = motorcadDataObj.ModelParameters_MotorLAB;
            obj.LossParameters_MotorLAB = motorcadDataObj.LossParameters_MotorLAB;
            %
            obj.phasorDiagram = motorcadDataObj.phasorDiagram;
            %
            obj.ArmatureConductor_Temperature=motorcadDataObj.ArmatureConductor_Temperature;
            obj.Magnet_Temperature=motorcadDataObj.Magnet_Temperature;
            %
            obj.file_name=motorcadDataObj.file_name;
            obj.refFile=motorcadDataObj.refFile;
        end
    end
end