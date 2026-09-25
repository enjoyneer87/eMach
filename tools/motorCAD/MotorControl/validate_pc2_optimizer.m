function report = validate_pc2_optimizer(output_dir)
% Numerical regression and loss-model audit, without opening Motor-CAD.
% The constant-flux fixture has a closed-form minimum-current solution.
% It tests optimizer plumbing, not the physical validity of EECLUTdq.
here = fileparts(mfilename('fullpath'));
root = fileparts(fileparts(fileparts(here)));
oldpath = path;
cleanup = onCleanup(@() path(oldpath)); %#ok<NASGU>
addpath(here, fullfile(root,'tools'), fullfile(root,'tools','unit'), fullfile(root,'tools','rpm'), ...
    fullfile(root,'tools','motorCAD','interP'), ...
    fullfile(root,'tools','motorCAD','MCADLinkTable'), ...
    fullfile(root,'SkkuEMLabProject'));
if ~exist(output_dir,'dir'), mkdir(output_dir); end

ld = 0.12; lq = 0.025; omega = 400; poles = 8; power = 40;
loss.AC_Copper.fitResult = @(d,q) power + 0*d + 0*q;
speed = struct('freqEOp',omega/(2*pi),'freqEBuild',omega/(2*pi), ...
               'nTarget',omega/(poles/2)*60/(2*pi));
obj = EECLUTdq(@(d,q) ld+0*d+0*q, @(d,q) lq+0*d+0*q, ...
    @(d,q) 0*d+0*q, @(d,q) 0*d+0*q, @(d,q) ld+0*d+0*q, ...
    loss,omega,speed,poles);

a = [-5,30]; b = [-15,45];
fa = obj.compMTPA(a); fb = obj.compMTPA(b);
assert(abs(fa-fb)>1, 'Objective still ignores trial current.');
poison = obj; poison.lastIRMS = [1e6,-1e6];
assert(abs(poison.compMTPA(a)-fa)<1e-12, 'Objective depends on cached state.');
assert(isequal(obj.lastIRMS,[0,0]), 'Value object was mutated.');
[c_under,~,state] = obj.evaluateMotorConstraints(a,20,60);
[c_over,~,~] = obj.evaluateMotorConstraints(a,20,40);
assert(c_under<0 && c_over>0, 'Voltage feasibility sign is reversed.');

tab = table([20;60;120;300],[10;30;50;70],repmat(ld,4,1), ...
    repmat(lq,4,1),'VariableNames', ...
    {'Is','Current Angle','Flux Linkage D','Flux Linkage Q'});
target = 20;
normal = 1.5*(poles/2)*sqrt(2)*[-lq,ld];
% Orthogonal projection onto a linear torque constraint gives the exact
% global minimum in total-current space; this point is inside box bounds.
effective = target + state.lastElecLossData.TorqueElecLossWODCLoss;
total_exact = normal * effective / sum(normal.^2);
loss_current = [state.lastElecLossData.idsRMS,state.lastElecLossData.iqsRMS];
im_exact = total_exact-loss_current;
[id,iq,itd,itq,out] = findOptimalCurrentsWithConstraints(target,60,obj,tab);
assert(norm([id,iq]-im_exact)<2e-4, 'Optimizer misses analytic minimum.');
assert(norm([itd,itq]-total_exact)<2e-4, 'Total-current optimum differs.');
assert(isequal(out.lastImRMS,[id,iq]), 'Output state is a stale trial.');
assert(isequal(out.lastIRMS,[itd,itq]), 'Returned currents and state disagree.');
assert(abs(out.TShaft-target)<1e-8 && out.Vs_pk<=60+1e-8);
[id2,iq2] = findOptimalCurrentsWithConstraints(target,60,poison,flipud(tab));
assert(norm([id2,iq2]-im_exact)<2e-4, 'Order/cache changes optimum.');
rejected = false;
try
    findOptimalCurrentsWithConstraints(target,40,obj,tab);
catch exception
    if ~strcmp(exception.identifier,'MotorControl:NoFeasibleOptimum')
        rethrow(exception);
    end
    rejected = true;
end
assert(rejected, 'Infeasible voltage was returned as an optimum.');

% Audit independent of optimizer success: induced dq voltage is omega*J*psi.
v_induced_pk = omega*[-lq,ld];
p_branch = 1.5*dot(v_induced_pk,sqrt(2)*loss_current);
tau_physical = power/(omega/(poles/2));
zero = calcCurrentElecLoss(ld,lq,0,0,omega);
report = struct('scope','synthetic numerical regression; not physical motor validation', ...
    'matlab_version',version,'passed',true,'objective_at_a',fa,'objective_at_b',fb, ...
    'analytic_im_rms',im_exact,'optimizer_im_rms',[id,iq], ...
    'analytic_error_A',norm([id,iq]-im_exact), ...
    'voltage_residual_under_V',c_under,'voltage_residual_over_V',c_over, ...
    'final_torque_residual_Nm',out.TShaft-target,'infeasible_rejected',rejected, ...
    'audit',struct('requested_loss_W',power,'branch_absorbed_power_W',p_branch, ...
      'legacy_loss_torque_Nm',state.lastElecLossData.TorqueElecLossWODCLoss, ...
      'loss_over_mechanical_speed_Nm',tau_physical, ...
      'zero_loss_resistance_finite',isfinite(zero.RelecLoss), ...
      'physical_loss_model_validated',false), ...
    'original_438p2_case','not run: original motor/table fixture and voltage convention not pinned');
fid = fopen(fullfile(output_dir,'regression.json'),'w','n','UTF-8');
assert(fid>=0); filecleanup = onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));
disp(report);
end
