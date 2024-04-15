function [idm_rms_opt, iqm_rms_opt, id_rms, iq_rms, eeclutdq_out] = findOptimalCurrentsWithConstraints(target_Tload, Vlim, eeclutdq, MCADLinkTable)
     % Calculate Id, Iq from peak current and angle data
    [Idm_pk, Iqm_pk] = arrayfun(@(x) pkgamma2dq(MCADLinkTable.Is(x), MCADLinkTable.('Current Angle')(x)), 1:height(MCADLinkTable));

    % Convert peak currents to RMS
    Idm_rms = Idm_pk / sqrt(2);
    Iqm_rms = Iqm_pk / sqrt(2);

    % Calculate electromagnetic torque using RMS current values
    Torque = arrayfun(@(idx) calcDQFluxTorque(Idm_rms(idx), Iqm_rms(idx), eeclutdq.PoleNumber, MCADLinkTable.('Flux Linkage D')(idx), MCADLinkTable.('Flux Linkage Q')(idx)), 1:length(Idm_rms));
    
    % Find index of current closest to target torque
    [~, idx] = min(abs(Torque - target_Tload));
    initial_guess_rms = [Idm_rms(idx), Iqm_rms(idx)]; % Optimal initial guess based on RMS currents
  

    maxIs_rms = max(MCADLinkTable.Is) / sqrt(2);


    function [c, ceq] = nestedEvaluateMotorConstraints(Im_rms)
        [c, ceq, eeclutdq] = evaluateMotorConstraints(eeclutdq, Im_rms, target_Tload, Vlim);
    end


    options = optimoptions('fmincon', 'Display', 'iter', 'Algorithm', 'sqp', ...
                       'MaxFunctionEvaluations', 5000, ...
                       'ConstraintTolerance', 1e-8);
    [Im_opt_rms, ~] = fmincon(@(Im_rms) eeclutdq.compMTPA(Im_rms), initial_guess_rms, [], [], [], [], ...
                             [-maxIs_rms, 0], [0,maxIs_rms], @nestedEvaluateMotorConstraints, options);

    idm_rms_opt = Im_opt_rms(1);
    iqm_rms_opt = Im_opt_rms(2);
    id_rms = idm_rms_opt + eeclutdq.lastElecLossData.idsRMS;
    iq_rms = iqm_rms_opt + eeclutdq.lastElecLossData.iqsRMS;

    eeclutdq_out = eeclutdq;  % Updated EECLUTdq object
end
