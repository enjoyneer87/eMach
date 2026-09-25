function report = validate_pc2_lab_exports(output_dir,source_dir)
% Replay four frozen exports, never launch/rebuild Motor-CAD.
% Compare two EXPLICIT diagnostic allocations, neither a validated loss law
% nor a replacement for Motor-CAD's load-dependent AC series resistance.
if nargin<2, source_dir='D:/KangDH/Thesis/e10/work_lab_pc1/drive'; end
here=fileparts(mfilename('fullpath')); root=fileparts(fileparts(fileparts(here)));
oldpath=path; cleanup=onCleanup(@() path(oldpath)); %#ok<NASGU>
addpath(here,fullfile(root,'tools'),fullfile(root,'tools','unit'), ...
    fullfile(root,'tools','motorCAD','interP'),fullfile(root,'tools','motorCAD','MCADLinkTable'));
if ~exist(output_dir,'dir'), mkdir(output_dir); end
speeds=[2000,4000,8000,16000];
expected={'60054e324cc5ae7beb70d40f0d81a28dc2d71fd498c120f6b1dacf8889d07e83', ...
    '1f1a74d389f5fd26e33d1754ecf1d41ab2562a5001cf268700c50bcde0896bf6', ...
    'b4901e35bf10ced540e66ff3a0874c1e201349462f5b93fff7d76b4576d11aaa', ...
    '67261ef93d2a7cfb8e190e250306904dd8ff588b038e43248ad9b38eb09fcf1b'};
rows=struct([]); sources=struct('file',{},'sha256',{},'rpm',{},'shape',{});
poles=8; rdc=.0786; vlim=720*.97/sqrt(3);
for s=1:numel(speeds)
    n=speeds(s); filename=fullfile(source_dir,sprintf('e10_satloss_%d.mat',n));
    digest=sha256(filename); assert(strcmp(digest,expected{s}),'Frozen export hash changed.');
    S=load(filename); d=S.Id_Peak(:,1); q=S.Iq_Peak(1,:).';
    assert(isequal(size(S.Id_Peak),[51,51]) && all(diff(d)>0) && all(diff(q)>0));
    assert(all(S.Id_Peak==repmat(d,1,51),'all') && all(S.Iq_Peak==repmat(q.',51,1),'all'));
    fd=griddedInterpolant({d,q},S.Flux_Linkage_D,'linear','none');
    fq=griddedInterpolant({d,q},S.Flux_Linkage_Q,'linear','none');
    power=S.Stator_Copper_Loss_AC+S.Iron_Loss+S.Magnet_Loss;
    assert(all(isfinite(power),'all') && all(power>=0,'all'));
    pf=griddedInterpolant({d,q},power,'linear','none');
    % Map arrays are M(id,iq), not M(iq,id). Limit lies within both axes.
    max_im=min(abs(d(1)),q(end))/sqrt(2);
    pk=hypot(S.Id_Peak(:),S.Iq_Peak(:)); ga=atan2d(-S.Id_Peak(:),S.Iq_Peak(:));
    valid=pk<=max_im*sqrt(2) & pk>0;
    tab=table(pk(valid),ga(valid),S.Flux_Linkage_D(valid),S.Flux_Linkage_Q(valid), ...
        'VariableNames',{'Is','Current Angle','Flux Linkage D','Flux Linkage Q'});
    omega=n*2*pi/60*(poles/2); sp=struct('nTarget',n);
    sources(s)=struct('file',filename,'sha256',digest,'rpm',n,'shape',[51,51]); %#ok<AGROW>
    for fraction=[0,1]
        name='all_non_dc_as_drag'; if fraction==1, name='all_non_dc_as_shunt'; end
        cfg=struct('Name',name,'PowerFcn',@(id,iq) allocate(pf,id,iq,fraction), ...
            'RdcOhm',rdc,'MaxMagnetizingRMS',max_im,'MaxTerminalRMS',460);
        obj=EECLUTdq(@(id,iq) fd(id,iq),@(id,iq) fq(id,iq),[],[],[],[],omega,sp,poles,cfg);
        for target=[20,60]
            [id,iq,itd,itq,out]=findOptimalCurrentsWithConstraints(target,vlim,obj,tab);
            [c,ceq,out]=out.evaluateMotorConstraints([id,iq],target,vlim);
            pb=out.lastPowerBalance;
            % Independent balance from source maps and returned currents.
            flux=[fd(sqrt(2)*id,sqrt(2)*iq),fq(sqrt(2)*id,sqrt(2)*iq)];
            v=rdc*sqrt(2)*[itd,itq]+omega*[-flux(2),flux(1)];
            source_loss=pf(sqrt(2)*id,sqrt(2)*iq);
            residual=1.5*dot(v,sqrt(2)*[itd,itq])-target*n*2*pi/60 ...
                -3*rdc*(itd^2+itq^2)-source_loss;
            assert(all(c<=1e-8) && abs(ceq)<1e-8 && abs(residual)<1e-5);
            assert(abs(pb.residualW)<1e-7);
            row=struct('rpm',n,'target_Nm',target,'allocation',name, ...
                'im_rms',[id,iq],'terminal_rms',[itd,itq],'total_current_A',hypot(itd,itq), ...
                'gamma_magnetizing_deg',atan2d(-id,iq),'phase_peak_V',out.Vs_pk, ...
                'non_dc_loss_W',source_loss,'independent_energy_residual_W',residual, ...
                'torque_residual_Nm',ceq,'power_balance',pb);
            if isempty(rows), rows=row; else, rows(end+1)=row; end %#ok<AGROW>
            fprintf('%5d rpm / %2g Nm / %-22s: %.3f A, %.3f deg, %.3f V\n', ...
                n,target,name,row.total_current_A,row.gamma_magnetizing_deg,row.phase_peak_V);
        end
    end
end
report=struct('passed',true,'scope','frozen Lab data numerical replay; diagnostic allocations only', ...
    'source_model_attribution','export_lab_satmap.py attributes exports to reference e10Turn6V261; no historical build hash', ...
    'source_type','existing interpolated Motor-CAD Lab exports, 2026-09-17; no new FEA or measurement', ...
    'sources',sources,'phase_peak_limit_V',vlim,'Rdc_Ohm',rdc, ...
    'shaft_boundary','magnetizing dq flux torque minus allocated DragW/omegaM; mechanical friction omitted', ...
    'limitations',{{'Neither allocation is selected as the physical convention.', ...
    'This shunt branch does not reproduce Motor-CAD Lab AC series-resistance voltage.', ...
    'Local constrained optima; global optimality of nonlinear maps not established.', ...
    'Original 15000 rpm / 438.2 Nm case remains unpinned.'}},'cases',rows);
fid=fopen(fullfile(output_dir,'lab_replay.json'),'w','n','UTF-8'); assert(fid>=0);
fc=onCleanup(@() fclose(fid)); %#ok<NASGU>
fprintf(fid,'%s\n',jsonencode(report,PrettyPrint=true));
end

function loss=allocate(pf,d,q,fraction)
p=pf(d,q); loss=struct('InputW',fraction*p,'DragW',(1-fraction)*p);
end

function hash=sha256(filename)
fid=fopen(filename,'rb'); assert(fid>=0); cleanup=onCleanup(@() fclose(fid)); %#ok<NASGU>
bytes=fread(fid,Inf,'*uint8'); md=java.security.MessageDigest.getInstance('SHA-256');
md.update(bytes); hash=lower(reshape(dec2hex(typecast(md.digest(),'uint8'),2).',1,[]));
end
