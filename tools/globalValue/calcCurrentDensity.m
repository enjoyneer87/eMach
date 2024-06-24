
%% check devcalcCurrentDensity.mlx
% J$$=\frac{\text { Phase current }}{\text { Parallel paths } \times \text { 
% no.of strands in hand } \times \text { Stator conductor CSA }}=A_{\text {rms 
% }} / \mathrm{mm}^2$$

function Jrms=calcCurrentDensity(Irms,ParallelPath,Nstrand,ArmatureConductorCSA)
   Jrms=Irms/(ParallelPath*Nstrand*ArmatureConductorCSA);
  
end