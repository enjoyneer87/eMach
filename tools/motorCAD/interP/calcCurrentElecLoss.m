function data = calcCurrentElecLoss(lambdaD, lambdaQ, inputLossW, dragTorqueNm, omegaE)
% Balanced three-phase, amplitude-invariant dq: P = 3/2 * e_pk' * i_pk.
% This branch represents ONLY explicitly allocated input-side loss [W].
% dragTorqueNm is an independent mechanical allocation, never inferred here.
validateattributes([lambdaD,lambdaQ,omegaE,dragTorqueNm],{'numeric'}, ...
    {'real','finite','vector','numel',4});
validateattributes(inputLossW,{'numeric'},{'real','finite','scalar','nonnegative'});
e = omegaE*[-lambdaQ,lambdaD];
e2 = dot(e,e);
if inputLossW == 0
    i_pk = [0,0]; resistance = Inf; % open circuit, including zero speed/flux
elseif e2 == 0
    error('MotorControl:LossAtZeroEMF', ...
        'Positive shunt loss cannot be represented at zero induced voltage.');
else
    i_pk = (2/3)*inputLossW/e2*e;
    resistance = 1.5*e2/inputLossW;
end
data = struct('ispk',hypot(i_pk(1),i_pk(2)), ...
    'idsRMS',i_pk(1)/sqrt(2),'iqsRMS',i_pk(2)/sqrt(2), ...
    'RelecLoss',resistance,'omegaE',omegaE, ...
    'PelecLossWODCLoss',inputLossW,'TorqueElecLossWODCLoss',dragTorqueNm, ...
    'absorbedPowerW',1.5*dot(e,i_pk));
end
