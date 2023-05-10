%% Input

P=12;
RPM=1000;

%% Show  

freq_e=RPM/60*(P/2); 
freq_mech=RPM/60;
One_mech_Endtime=1/freq_mech;
One_elec_Endtime=1/freq_e;

freq_mech


% omega
freq_mech*2*pi
legend({'Sensor torque_{IPMSM}','Sensor torque_{ASM}','IPMSM_torque','ASM_torque'},'Location','Best');
