function report = validate_pc2_optimizer(output_dir)
% Independent analytic regression, energy accounting and boundary tests.
here=fileparts(mfilename('fullpath'));
root=fileparts(fileparts(fileparts(here)));
oldpath=path; cleanup=onCleanup(@() path(oldpath)); %#ok<NASGU>
addpath(here,fullfile(root,'tools'),fullfile(root,'tools','unit'), ...
    fullfile(root,'tools','motorCAD','interP'),fullfile(root,'tools','motorCAD','MCADLinkTable'));
if ~exist(output_dir,'dir'), mkdir(output_dir); end
ld=.12; lq=.025; omega=400; poles=8; power=40; drag=10;
speed=struct('freqEOp',omega/(2*pi),'freqEBuild',omega/(2*pi), ...
    'nTarget',omega/(poles/2)*60/(2*pi));
loss.AC_Copper.fitResult=@(d,q) power+0*d+0*q;
contract=struct('Name','synthetic 40 W input + 10 W drag', ...
    'PowerFcn',@(d,q) struct('InputW',power,'DragW',drag), ...
    'RdcOhm',0,'MaxMagnetizingRMS',200,'MaxTerminalRMS',200);
fd=@(d,q) ld+0*d+0*q; fq=@(d,q) lq+0*d+0*q; zero=@(d,q) 0*d+0*q;
obj=EECLUTdq(fd,fq,zero,zero,fd,loss,omega,speed,poles,contract);
expect_error(@() EECLUTdq(fd,fq,zero,zero,fd,loss,omega,speed,poles), ...
    'MotorControl:MissingLossContract');
a=[-5,30]; b=[-15,45];
fa=obj.compMTPA(a); fb=obj.compMTPA(b);
assert(abs(fa-fb)>1);
poison=obj; poison.lastIRMS=[1e6,-1e6];
assert(abs(poison.compMTPA(a)-fa)<1e-12 && isequal(obj.lastIRMS,[0,0]));
[cu,~,state]=obj.evaluateMotorConstraints(a,20,60);
[co,~,~]=obj.evaluateMotorConstraints(a,20,40);
assert(cu(1)<0 && co(1)>0);
[cc,~,~]=obj.evaluateMotorConstraints([-180,180],20,60);
assert(cc(2)>0 && cc(3)>0,'Circular current constraints not enforced.');
tab=table([20;60;120;280],[10;30;50;70],repmat(ld,4,1),repmat(lq,4,1), ...
    'VariableNames',{'Is','Current Angle','Flux Linkage D','Flux Linkage Q'});
target=20; normal=1.5*(poles/2)*sqrt(2)*[-lq,ld];
% Tshaft = normal*Im - DragW/wm; loss current is parallel to normal.
im_exact=normal*(target+drag/(omega/(poles/2)))/sum(normal.^2);
loss_current=[state.lastElecLossData.idsRMS,state.lastElecLossData.iqsRMS];
total_exact=im_exact+loss_current;
[id,iq,itd,itq,out]=findOptimalCurrentsWithConstraints(target,60,obj,tab);
assert(norm([id,iq]-im_exact)<2e-4 && norm([itd,itq]-total_exact)<2e-4);
assert(isequal(out.lastImRMS,[id,iq]) && isequal(out.lastIRMS,[itd,itq]));
assert(abs(out.TShaft-target)<1e-8 && out.Vs_pk<=60+1e-8);
[id2,iq2]=findOptimalCurrentsWithConstraints(target,60,poison,flipud(tab));
assert(norm([id2,iq2]-im_exact)<2e-4);
expect_error(@() findOptimalCurrentsWithConstraints(target,40,obj,tab), ...
    'MotorControl:NoFeasibleOptimum');

% Check both speed signs, each axis, and arbitrary flux/current directions.
branch_errors=[]; energy_errors=[];
for w=[-400,400]
    for flux=[.12,.025; .12,0; 0,.025; -.12,.025; -.12,-.025].'
        z=calcCurrentElecLoss(flux(1),flux(2),power,0,w);
        branch_errors(end+1)=abs(z.absorbedPowerW-power); %#ok<AGROW>
        assert(z.RelecLoss>0 && all(isfinite([z.idsRMS,z.iqsRMS])));
    end
    for fraction=[0,.25,1]
        cfg=contract; cfg.RdcOhm=.1;
        cfg.PowerFcn=@(d,q) struct('InputW',fraction*power,'DragW',(1-fraction)*power);
        sp=speed; sp.nTarget=w/(poles/2)*60/(2*pi);
        trial=EECLUTdq(fd,fq,zero,zero,fd,loss,w,sp,poles,cfg);
        [~,~,trial]=trial.evaluateMotorConstraints(a,20,60);
        energy_errors(end+1)=abs(trial.lastPowerBalance.residualW); %#ok<AGROW>
        % Independent total-current torque expression must give same shaft torque.
        tt=calcDQFluxTorque(trial.lastIRMS(1),trial.lastIRMS(2),ld,lq,poles);
        assert(abs(tt-power/(w/(poles/2))-trial.TShaft)<1e-12);
    end
end
assert(max(branch_errors)<1e-10 && max(energy_errors)<1e-9);
z=calcCurrentElecLoss(0,0,0,0,0);
assert(isinf(z.RelecLoss) && z.ispk==0 && z.absorbedPowerW==0);
expect_error(@() calcCurrentElecLoss(ld,lq,1,0,0),'MotorControl:LossAtZeroEMF');
expect_error(@() calcCurrentElecLoss(0,0,1,0,omega),'MotorControl:LossAtZeroEMF');
[p,tau]=calcTotalElecLossFromInterP(a(1),a(2),loss,speed);
assert(p==power && abs(tau-.4)<1e-12);
sp=speed; sp.nTarget=0;
expect_error(@() calcTotalElecLossFromInterP(a(1),a(2),loss,sp),'MotorControl:LossAtZeroSpeed');
loss0.AC_Copper.fitResult=zero;
[p0,t0]=calcTotalElecLossFromInterP(0,0,loss0,sp);
assert(p0==0 && t0==0);
expect_error(@() calcTotalElecLossFromInterP(0,0,loss,rmfield(speed,'nTarget')), ...
    'MotorControl:MissingMechanicalSpeed');

report=struct('scope','analytic and numerical consistency; physical loss allocation not validated', ...
    'matlab_version',version,'passed',true,'objective_at_a',fa,'objective_at_b',fb, ...
    'analytic_im_rms',im_exact,'optimizer_im_rms',[id,iq], ...
    'analytic_error_A',norm([id,iq]-im_exact), ...
    'voltage_residual_under_V',cu(1),'voltage_residual_over_V',co(1), ...
    'final_torque_residual_Nm',out.TShaft-target,'infeasible_rejected',true, ...
    'audit',struct('requested_loss_W',power,'branch_absorbed_power_W',state.lastElecLossData.absorbedPowerW, ...
    'corrected_loss_equivalent_torque_Nm',tau,'zero_loss_open_circuit',isinf(z.RelecLoss), ...
    'max_branch_power_error_W',max(branch_errors),'max_energy_residual_W',max(energy_errors), ...
    'signed_speed_and_axis_cases',numel(branch_errors),'allocation_energy_cases',numel(energy_errors), ...
    'circular_current_constraint_checked',true,'physical_loss_allocation_validated',false), ...
    'original_438p2_case','not run: original motor/table and voltage convention not pinned');
fid=fopen(fullfile(output_dir,'regression.json'),'w','n','UTF-8'); assert(fid>=0);
fc=onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));
disp(report);
end

function expect_error(f,identifier)
try
    f();
catch exception
    assert(strcmp(exception.identifier,identifier),'Unexpected error: %s',exception.identifier);
    return
end
error('Expected error was not raised: %s',identifier);
end
