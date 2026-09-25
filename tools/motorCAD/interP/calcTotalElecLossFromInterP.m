function [Power_PostLoss, Torque_PostLoss] = calcTotalElecLossFromInterP(idm_rms, iqm_rms, Ploss_dqh,SpeedScaledInfo)
   %% idm, iqm 입력은 rms
   idm_pk=rms2pk(idm_rms);
   iqm_pk=rms2pk(iqm_rms);

   % 각 속도에서의 손실 데이터 및 freqEOp 추출
   LossData = Ploss_dqh;
   % freqEOp = SpeedScaledInfo.freqEOp;
   % 각 종류별 손실 계산
   TotalHys = 0;
   TotalEddy = 0;
   TotalAC = 0;
   MagnetLoss = 0;

   
   % Hys 손실 계산
   if isfield(LossData, 'Hys')
       for j = 1:length(LossData.Hys)
           TotalHys = TotalHys + feval(LossData.Hys(j).fitResult, idm_pk, iqm_pk);
       end
   end

   % Eddy 손실 계산
   if isfield(LossData, 'Eddy')
       for j = 1:length(LossData.Eddy)
           TotalEddy = TotalEddy + feval(LossData.Eddy(j).fitResult, idm_pk, iqm_pk);
       end
   end

   % AC Copper 손실 계산
   if isfield(LossData, 'AC_Copper')
       for j = 1:length(LossData.AC_Copper)
           TotalAC = TotalAC + feval(LossData.AC_Copper(j).fitResult, idm_pk, iqm_pk);
       end
   end

   % Magnet 손실 계산
   if isfield(LossData, 'Magnet')
       for j = 1:length(LossData.Magnet)
           MagnetLoss = MagnetLoss + feval(LossData.Magnet(j).fitResult, idm_pk, iqm_pk);
       end
   end

   % 전력 손실 계산
   freqEBuild = SpeedScaledInfo.freqEBuild;
   Power_PostLoss = (TotalHys + TotalEddy) * 1.5 * freqEBuild + TotalAC + MagnetLoss;

   % Equivalent torque uses MECHANICAL rpm, never electrical Hz. Legacy fit
   % normalization is unchanged; this does not allocate losses to a branch.
   if ~isfield(SpeedScaledInfo,'nTarget')
       error('MotorControl:MissingMechanicalSpeed','nTarget [mechanical rpm] is required.');
   end
   validateattributes(SpeedScaledInfo.nTarget,{'numeric'},{'real','finite','scalar'});
   validateattributes(Power_PostLoss,{'numeric'},{'real','finite','scalar','nonnegative'});
   omegaM = SpeedScaledInfo.nTarget*2*pi/60;
   if omegaM == 0
       if Power_PostLoss ~= 0
           error('MotorControl:LossAtZeroSpeed','Positive loss / zero mechanical speed is undefined.');
       end
       Torque_PostLoss = 0;
   else
       Torque_PostLoss = Power_PostLoss / omegaM;
   end
end
