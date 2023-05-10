classdef ResultMotorcadLabData < ResultMotorcadData
    properties
        % Thermal
        postArmatureConductor_Temperature
        postMagnet_Temperature
        postShaft_Temperature
        postBearing_Temperature_R
        postBearing_Temperature_F
        postAirgap_Temperature
        
        % ModelParameters_MotorLAB
        postModelParameters_MotorLAB
        
        % Temp Coefficient
        tempCoeffiBrAlpha
        tempCoeffiHcBeta
        psiDTempRatio
        psiQTempRatio
    end
    
    methods
        % 생성자 메서드
        function obj = ResultMotorcadLabData(motorcadDataObj)
            % ResultMotorcadLabData의 생성자
            % ResultMotorcadData 객체의 속성 전체를 상속받아 obj의 속성으로 설정
            obj = obj@ResultMotorcadData(motorcadDataObj);
            
            % 추가로 상속받을 속성들을 정의하고 초기화
            obj.postArmatureConductor_Temperature = [];
            obj.postMagnet_Temperature = [];
            obj.postShaft_Temperature = [];
            obj.postBearing_Temperature_R = [];
            obj.postBearing_Temperature_F = [];
            obj.postAirgap_Temperature = [];
            obj.postModelParameters_MotorLAB = [];
            obj.tempCoeffiBrAlpha = [];
            obj.tempCoeffiHcBeta = [];
            obj.psiDTempRatio = [];
            obj.psiQTempRatio = [];
        end
        function obj = tempCorrectedModelParameters_MotorLAB(obj, tempCoeffiBrAlpha)
            % 온도 보정 계수 할당
            obj.tempCoeffiBrAlpha = tempCoeffiBrAlpha;
    %         obj.tempCoeffiHcBeta = tempCoeffiHcBeta;
        
            % 기존 ModelParameters_MotorLAB에서 변환한 값을 저장할 새로운 변수 생성
            % 새로운 온도에서 PsiDModel_Lab 및 PsiQModel_Lab 계산
            obj.postModelParameters_MotorLAB = obj.ModelParameters_MotorLAB;

            %%무부하만  ratio 를 사용하고
            obj.postModelParameters_MotorLAB.PsiDModel_Lab(1,:) = obj.ModelParameters_MotorLAB.PsiDModel_Lab(1,:) .* (1 + obj.tempCoeffiBrAlpha/100 .* (obj.postMagnet_Temperature - obj.Magnet_Temperature));
            obj.postModelParameters_MotorLAB.PsiQModel_Lab(1,:) = obj.ModelParameters_MotorLAB.PsiQModel_Lab(1,:) .* (1 + obj.tempCoeffiBrAlpha/100 .* (obj.postMagnet_Temperature - obj.Magnet_Temperature));
    %         obj.postModelParameters_MotorLAB.PsiQModel_Lab = obj.ModelParameters_MotorLAB.PsiQModel_Lab.* (1 - obj.tempCoeffiBrAlpha/100 .* (obj.postMagnet_Temperature - obj.Magnet_Temperature));
    
            %% 부하상태는 두개의 해석으로부터 scailing 
            %         obj.postModelParameters_MotorLAB.PsiDModel_Lab(2:end,:) = obj.ModelParameters_MotorLAB.PsiDModel_Lab(2:end,:) .* (1 + obj.psiDTempRatio(2:end,:) .* (obj.postMagnet_Temperature - obj.Magnet_Temperature));
    %         obj.postModelParameters_MotorLAB.PsiQModel_Lab(2:end,:)  = obj.ModelParameters_MotorLAB.PsiQModel_Lab(2:end,:) .* (1 + obj.psiQTempRatio(2:end,:) .* (obj.postMagnet_Temperature - obj.Magnet_Temperature));
            obj.postModelParameters_MotorLAB.PsiDModel_Lab(2:end,:) = obj.ModelParameters_MotorLAB.PsiDModel_Lab(2:end,:)*1 + obj.psiDTempRatio(2:end,:)/100* (obj.postMagnet_Temperature - obj.Magnet_Temperature);
            obj.postModelParameters_MotorLAB.PsiQModel_Lab(2:end,:)  = obj.ModelParameters_MotorLAB.PsiQModel_Lab(2:end,:)*1 %+ obj.psiQTempRatio(2:end,:)/100* (obj.postMagnet_Temperature - obj.Magnet_Temperature);
             
            %         obj.postModelParameters_MotorLAB.PsiDModel_Lab=obj.ModelParameters_MotorLAB.PsiDModel_Lab.*obj.psiDTempRatio*(obj.postMagnet_Temperature-obj.Magnet_Temperature);
    %         obj.postModelParameters_MotorLAB.PsiQModel_Lab=obj.ModelParameters_MotorLAB.PsiQModel_Lab.*obj.psiQTempRatio*(obj.postMagnet_Temperature-obj.Magnet_Temperature);
    %         refTempMotorcadPost.psiQTempRatio=(refTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab/refTempMotorcad.ModelParameters_MotorLAB.PsiQModel_Lab-1)/(Temp1-Tempref)
    %         obj.postModelParameters_MotorLAB.PsiDModel_Lab=(obj.psiDTempRatio*(obj.postMagnet_Temperature-obj.Magnet_Temperature)+1).*obj.ModelParameters_MotorLAB.PsiDModel_Lab;
    %         obj.postModelParameters_MotorLAB.PsiQModel_Lab=(obj.psiQTempRatio*(obj.postMagnet_Temperature-obj.Magnet_Temperature)+1).*obj.ModelParameters_MotorLAB.PsiQModel_Lab;
    
        end
    end
end