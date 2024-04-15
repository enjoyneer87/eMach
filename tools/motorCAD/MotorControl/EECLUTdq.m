classdef EECLUTdq
    properties
        LambdaDFit           % Fit function for d-axis flux linkage
        LambdaQFit           % Fit function for q-axis flux linkage
        LdFitResult          % Fit result for d-axis inductance
        LqFitResult          % Fit result for q-axis inductance
        PMFitResult          % Fit result for permanent magnet flux linkage
        ScaledLossFitResult  % Fit result for scaled losses
        omegaE               % Electrical angular frequency
        SpeedScaledInfo      %
        PoleNumber           % Number of poles in the motor
        TShaft
        Vs_pk
        %% Last data
        lastImRMS            % Last motor currents [idm_rms, iqm_rms] without losses
        lastIRMS                % Last total motor currents [id_total, iq_total] including losses
        lastElecLossData     % Last calculated electrical losses data
    end
    
    methods
        function obj = EECLUTdq(LambdaDFit, LambdaQFit, LdFitResult, LqFitResult, PMFitResult, ScaledLossFitResult, omegaE,SpeedScaledInfo, PoleNumber)
            obj.LambdaDFit = LambdaDFit;
            obj.LambdaQFit = LambdaQFit;
            obj.LdFitResult = LdFitResult;
            obj.LqFitResult = LqFitResult;
            obj.PMFitResult = PMFitResult;
            obj.ScaledLossFitResult = ScaledLossFitResult;
            obj.omegaE = omegaE;
            obj.SpeedScaledInfo =SpeedScaledInfo;
            obj.PoleNumber = PoleNumber;
            obj.lastIRMS = [0, 0];  % 초기값 설정
            obj.lastImRMS =[0,0]  ;         % Last motor currents [idm_rms, iqm_rms] without losses
            obj.lastElecLossData.ispk           =0;
            obj.lastElecLossData.idsRMS         =0;
            obj.lastElecLossData.iqsRMS         =0;
            obj.lastElecLossData.RelecLoss      =0;
            obj.lastElecLossData.omegaE         =0;
            obj.lastElecLossData.PelecLoss      =0;
            obj.lastElecLossData.TorqueElecLoss=0;
            obj.TShaft  =0;
            obj.Vs_pk   =0;
        end
        
        function totalCurrent = compMTPA(obj, Im_rms)
            if isempty(obj.lastIRMS)  % lastI가 비어 있으면 안전한 값 반환
                totalCurrent = 0;
            else
                totalCurrent = sqrt(obj.lastIRMS(1).^2 + obj.lastIRMS(2).^2);
            end
            % obj=obj.updateElecLossData(Im_rms);
        end
        
        function [c, ceq,newObj] = evaluateMotorConstraints(obj, Im_rms, target_Tload, Vlim)
            obj=obj.updateElecLossData(Im_rms);
            id_rms = obj.lastIRMS(1);
            iq_rms = obj.lastIRMS(2);
            idm_rms = obj.lastImRMS(1);
            iqm_rms = obj.lastImRMS(2);
            ids_rms = obj.lastElecLossData.idsRMS;
            iqs_rms = obj.lastElecLossData.iqsRMS;
            %% 
            idm_pk=rms2pk(idm_rms);
            iqm_pk=rms2pk(iqm_rms);
            psi_pm = obj.PMFitResult(idm_pk, iqm_pk);
            Ld = obj.LdFitResult(idm_pk, iqm_pk);
            Lq = obj.LqFitResult(idm_pk, iqm_pk);
            TorqueElecLoss= obj.lastElecLossData.TorqueElecLossWODCLoss;
            % id_rms, iq_rms로 RelecLoss를 표현한  Vd, Vq 계산 (식 26번) 
            % Vd_pk = obj.lastElecLossData.RelecLoss * rms2pk(id_rms) + obj.omegaE^2 * Lq * Ld / obj.lastElecLossData.RelecLoss * rms2pk(id_rms)- ...
            %     obj.omegaE * Lq * rms2pk(iq_rms) + (obj.omegaE^2 * Lq * psi_pm) / obj.lastElecLossData.RelecLoss;
            % Vq_pk = obj.lastElecLossData.RelecLoss * rms2pk(iq_rms) + obj.omegaE^2 * Lq * Ld / obj.lastElecLossData.RelecLoss *rms2pk(iq_rms) + ...
            %     obj.omegaE * Ld * rms2pk(id_rms) + obj.omegaE * psi_pm;
            Vd_pk =  obj.omegaE^2 * Lq * Ld / obj.lastElecLossData.RelecLoss * rms2pk(id_rms)- ...
                obj.omegaE * Lq * rms2pk(iq_rms) + (obj.omegaE^2 * Lq * psi_pm) / obj.lastElecLossData.RelecLoss;
            Vq_pk =  obj.omegaE^2 * Lq * Ld / obj.lastElecLossData.RelecLoss *rms2pk(iq_rms) + ...
                obj.omegaE * Ld * rms2pk(id_rms) + obj.omegaE * psi_pm;
            Vs_pk = sqrt(Vd_pk.^2 + Vq_pk.^2);

            lambdaD = obj.LambdaDFit(idm_pk, iqm_pk);
            lambdaQ = obj.LambdaQFit(idm_pk, iqm_pk);
            TorqueDQ =calcDQFluxTorque(id_rms, iq_rms, lambdaD,lambdaQ,obj.PoleNumber)
            % TorqueDQ = calcDQLTorque(id_rms, iq_rms, obj.PoleNumber,psi_pm, Ld, Lq);
            obj.TShaft=TorqueDQ-TorqueElecLoss;
            obj.Vs_pk=Vs_pk;
            ceq = obj.TShaft - target_Tload;
            c = Vlim - Vs_pk;

            newObj = obj;  % 업데이트된 객체 반환

        end

        function obj=updateElecLossData(obj, Im_rms)
            idm_rms = Im_rms(1);
            iqm_rms = Im_rms(2);
            idm_pk=rms2pk(idm_rms);
            iqm_pk=rms2pk(iqm_rms);
            lambdaD = obj.LambdaDFit(idm_pk, iqm_pk);
            lambdaQ = obj.LambdaQFit(idm_pk, iqm_pk);
            %% Calculate the electrical losses & Currents
            [Power_PostLoss, Torque_PostLoss] = calcTotalElecLossFromInterP(idm_rms, iqm_rms, obj.ScaledLossFitResult, obj.SpeedScaledInfo);
            obj.lastElecLossData             = calcCurrentElecLoss(lambdaD, lambdaQ, Power_PostLoss, Torque_PostLoss, obj.omegaE);

            %% 
            % idm_rms=idm_rms                         ;
            % iqm_rms=iqm_rms                         ;
            ids_RMS=obj.lastElecLossData.idsRMS         ;                
            iqs_RMS=obj.lastElecLossData.iqsRMS         ;                
            id_rms=idm_rms+ids_RMS                  ;        
            iq_rms=iqm_rms+iqs_RMS                  ;        

            %% Update the last data 

            % obj.lastElecLossData = lastElecLossData;
            obj.lastImRMS = [idm_rms, iqm_rms];
            obj.lastIRMS = [obj.lastImRMS(1) + obj.lastElecLossData.idsRMS, obj.lastImRMS(2) + obj.lastElecLossData.iqsRMS];
        end
    end
end
