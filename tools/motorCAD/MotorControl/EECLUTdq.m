classdef EECLUTdq
    % Steady dq value model. Map inputs are magnetizing PEAK currents;
    % public optimizer inputs/outputs are RMS and Vlim is phase PEAK.
    % LossContract.PowerFcn(d_pk,q_pk) returns InputW and DragW separately.
    % This accounting choice must be explicit; it is not a material law.
    properties
        LambdaDFit
        LambdaQFit
        LdFitResult % retained for callers; voltage uses the flux maps directly
        LqFitResult
        PMFitResult
        ScaledLossFitResult % legacy fits; not silently assigned to a branch
        omegaE
        SpeedScaledInfo
        PoleNumber
        LossContract
        TShaft = 0
        Vs_pk = 0
        lastImRMS = [0,0]
        lastIRMS = [0,0]
        lastElecLossData = struct()
        lastPowerBalance = struct()
    end
    methods
        function obj = EECLUTdq(fd,fq,ld,lq,pm,loss,omega,speed,poles,contract)
            if nargin == 0, return; end
            if nargin < 10
                error('MotorControl:MissingLossContract', ...
                    'Supply an explicit InputW/DragW loss contract; see validate_pc2_optimizer.');
            end
            required = {'Name','PowerFcn','RdcOhm','MaxMagnetizingRMS','MaxTerminalRMS'};
            assert(isstruct(contract) && all(isfield(contract,required)), ...
                'MotorControl:InvalidLossContract','Incomplete loss contract.');
            assert(isa(contract.PowerFcn,'function_handle'), ...
                'MotorControl:InvalidLossContract','PowerFcn must be a function handle.');
            validateattributes(contract.RdcOhm,{'numeric'},{'scalar','real','finite','nonnegative'});
            validateattributes([contract.MaxMagnetizingRMS,contract.MaxTerminalRMS], ...
                {'numeric'},{'vector','numel',2,'real','finite','positive'});
            validateattributes(poles,{'numeric'},{'scalar','finite','positive','even','integer'});
            validateattributes(omega,{'numeric'},{'scalar','real','finite'});
            assert(isfield(speed,'nTarget'),'MotorControl:MissingMechanicalSpeed', ...
                'nTarget [mechanical rpm] is required.');
            validateattributes(speed.nTarget,{'numeric'},{'scalar','real','finite'});
            assert(abs(speed.nTarget*2*pi/60*(poles/2)-omega) <= 1e-9*max(1,abs(omega)), ...
                'MotorControl:SpeedMismatch','Electrical and mechanical speeds disagree.');
            obj.LambdaDFit=fd; obj.LambdaQFit=fq;
            obj.LdFitResult=ld; obj.LqFitResult=lq; obj.PMFitResult=pm;
            obj.ScaledLossFitResult=loss; obj.omegaE=omega;
            obj.SpeedScaledInfo=speed; obj.PoleNumber=poles;
            obj.LossContract=contract;
        end

        function totalCurrent = compMTPA(obj, Im_rms)
            obj = obj.updateElecLossData(Im_rms);
            totalCurrent = hypot(obj.lastIRMS(1),obj.lastIRMS(2));
        end

        function [c,ceq,obj] = evaluateMotorConstraints(obj,Im_rms,target_Tload,Vlim)
            validateattributes(Vlim,{'numeric'},{'scalar','finite','positive'});
            obj = obj.updateElecLossData(Im_rms);
            d = sqrt(2)*obj.lastImRMS(1); q = sqrt(2)*obj.lastImRMS(2);
            flux = [obj.LambdaDFit(d,q),obj.LambdaQFit(d,q)];
            e = obj.omegaE*[-flux(2),flux(1)];
            i_pk = sqrt(2)*obj.lastIRMS;
            v_pk = e + obj.LossContract.RdcOhm*i_pk;
            tm = calcDQFluxTorque(Im_rms(1),Im_rms(2),flux(1),flux(2),obj.PoleNumber);
            obj.TShaft = tm-obj.lastElecLossData.TorqueElecLossWODCLoss;
            obj.Vs_pk = hypot(v_pk(1),v_pk(2));
            pm = obj.TShaft*obj.omegaE/(obj.PoleNumber/2);
            pdc = 3*obj.LossContract.RdcOhm*sum(obj.lastIRMS.^2);
            pin = 1.5*dot(v_pk,i_pk);
            loss = obj.lastElecLossData;
            obj.lastPowerBalance = struct('terminalW',pin,'shaftW',pm,'dcCopperW',pdc, ...
                'inputLossW',loss.PelecLossWODCLoss,'dragLossW',loss.DragW, ...
                'residualW',pin-pm-pdc-loss.PelecLossWODCLoss-loss.DragW, ...
                'magnetizingTorqueNm',tm,'vdPeakV',v_pk(1),'vqPeakV',v_pk(2));
            % All constraints are <= 0. Current circles prevent using the
            % corners of a rectangular map as an unqualified current rating.
            c = [obj.Vs_pk-Vlim; hypot(Im_rms(1),Im_rms(2))-obj.LossContract.MaxMagnetizingRMS; ...
                hypot(obj.lastIRMS(1),obj.lastIRMS(2))-obj.LossContract.MaxTerminalRMS];
            ceq = obj.TShaft-target_Tload;
        end

        function obj = updateElecLossData(obj,Im_rms)
            validateattributes(Im_rms,{'numeric'},{'real','finite','vector','numel',2});
            Im_rms=reshape(Im_rms,1,2);
            d=sqrt(2)*Im_rms(1); q=sqrt(2)*Im_rms(2);
            flux=[obj.LambdaDFit(d,q),obj.LambdaQFit(d,q)];
            validateattributes(flux,{'numeric'},{'real','finite','vector','numel',2});
            loss=obj.LossContract.PowerFcn(d,q);
            assert(isstruct(loss) && all(isfield(loss,{'InputW','DragW'})), ...
                'MotorControl:InvalidLossAllocation','PowerFcn must return InputW and DragW.');
            validateattributes([loss.InputW,loss.DragW],{'numeric'}, ...
                {'real','finite','nonnegative','vector','numel',2});
            omegaM=obj.omegaE/(obj.PoleNumber/2);
            dragTorque=0;
            if loss.DragW ~= 0
                if omegaM == 0
                    error('MotorControl:LossAtZeroSpeed','Nonzero DragW / zero speed is undefined.');
                end
                dragTorque=loss.DragW/omegaM;
            end
            obj.lastElecLossData=calcCurrentElecLoss(flux(1),flux(2),loss.InputW,dragTorque,obj.omegaE);
            obj.lastElecLossData.DragW=loss.DragW;
            obj.lastImRMS=Im_rms;
            obj.lastIRMS=Im_rms+[obj.lastElecLossData.idsRMS,obj.lastElecLossData.iqsRMS];
        end
    end
end
