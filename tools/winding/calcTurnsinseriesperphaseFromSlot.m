function SeriesTurns=calcTurnsinseriesperphaseFromSlot(NumOfSlots,MagTurnsConductorinSlot,ParallelPath,varargin)
    % NumOfSlots=72
    % NumOfPolePairs=6
    % NumOfPolePairs
    if nargin>3
    NumberPhase=varargin;
    else
    NumberPhase=3;
    end

    % ParallelPath=4

    %% MotorCAD
    % MagTurnsConductorinSlot
    % ArmatureTurnsPerPhase  -TurnPerCoil Eomys
    % ArmatureTurnsPerCoil   
    % Ntsp

    TotalMagTurnsinAllSlot=MagTurnsConductorinSlot*NumOfSlots;
    %  ArmatureTurnsPerCoil
    % Ncps

    %% 상당직렬턴수
    % Ncspc
    SeriesTurnsPerPhase=TotalMagTurnsinAllSlot/2/ParallelPath  % 상당 직렬턴수?
    % TurnsInSeries=TurnsInSeriesPerPhase*3

    SeriesTurns=SeriesTurnsPerPhase;   
    %% [syre] SlotConductor? - 진짜 Conductor네
    % SlotConductorParallel
    % SlotConductorNumber=TurnsInSeries/NumOfPolePairs/NumOfSlots; % syre
    % SlotConductorNumber =   TotalMagTurnsinAllSlot/72  ???
%     dataSet.SlotConductorNumber = eval(app.ConductorNumberEdit.Value);
    % if dataSet.SlotConductorNumber<0
%     dataSet.SlotConductorNumber=dataSet.TurnsInSeries/dataSet.NumOfPolePairs/(dataSet.NumOfSlots);
    % end
    % TurnsInSeries=SlotConductorNumber*(NumOfPolePairs*2);


    %% [TB]Eomys
    % comp_Ntsp(self, Zs=None):
    % Npcp :number of parallel circuits  per phase
    self=struct()
    self.Zs=54
    self.p=6  % Pole
    % self.qs=self.Zs/self.p/NumberPhase
    self.qs=calcWindingQs(self.Zs,self.p,NumberPhase)
    self.Npcp=1  %% parallelpath
    % Ntsp :number of turns in series per phase
    % Ntspc_eff=abs(self.get_connection_mat(Zs).sum(axis=(0, 1))).sum(axis=0) / self.Npcp / 2
     self.Ntsp=135;

    % Ncspc:number of coils in series per parallel circuit
        % Ncspc = Zs * Nrad * Ntan / (2.0 * self.qs * self.Npcp)
    self.Ncspc=9;   
    Ncspc=self.Zs* 1 * 1 /(2*self.qs*self.Npcp);
    % Ncps :number of conductors per slot
    % Ncps=15
    % Ncps_ = abs(self.get_connection_mat().sum(axis=(0, 1))).sum(axis=1)
    % Ncps_
    % Winding Matrix (1, 1, Zs, qs)

    % Nwpc = Nrad * Ntan Number of wire per coil?
     % total number of wires / strands in parallel per coil
    %Nrad :     Number of radial layer
    %Ntan :     Number of tangential layer

    %
%     Rear motor of the Tesla model 3 (2017), defined from
% A. J. P. Ortega et M. B. Kouhshahi, « High-Fidelity Analysis with Multiphysics Simulation for Performance Evaluation of Electric Motors Used in Traction Applications », p. 8. 
% and
% A. Krings et C. Monissen, « Review and Trends in Electric Traction Motors for Battery Electric and Hybrid Vehicles », in 2020 International Conference on Electrical Machines (ICEM), août 2020, vol. 1, p. 1807‑1813. doi: 10.1109/ICEM49940.2020.9270946. 
% The geometry is defined, but there was no information about the materials unsed for the magnets and the winding configuration.
end