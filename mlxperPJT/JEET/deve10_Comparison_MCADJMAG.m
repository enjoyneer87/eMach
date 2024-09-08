

%% load V24
load('MatBy_e10_MCAD_refACLoss_v24_Irms460ang43.mat')
SpeedList=[1000:2000:15000];

plot(SpeedList,[Hybrid.DCConductorLoss_Armature_A{:}],"DisplayName",'DCLoss_{ActivePart}')
hold on
plot(SpeedList,[FullFEA.ACLossFullFEAEmagMCAD_Total{:}],'DisplayName','Diffusion')
xline(TransitionSpeed)
plot(SpeedList,[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid')
plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
% plot(SpeedList,3*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend

%%
load('MatBy_e10_MCAD_refACLoss_Irms460ang43.mat')
SpeedList=[1000:1000:15000];

plot(SpeedList,[Hybrid.DCConductorLoss_Armature_A{:}],"DisplayName",'DCLoss_{ActivePart}')
hold on
plot(SpeedList,[FullFEA.ACLossFullFEAEmagMCAD_Total{:}],'DisplayName','Diffusion')
% xline(TransitionSpeed);
plot(SpeedList,2.5*[Hybrid.ACConductorLoss_MagneticMethod_Total{:}],'DisplayName','Hybrid');
% plot(SpeedList,[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','OPLab')
% plot(SpeedList,3*[OPLAB.LabOpPoint_StatorCopperLoss_AC{:}],'DisplayName','3*OPLab')
legend

%% JMAG 

% Hybrid N Diffusion
% Z:\01_Codes_Projects\git_fork_emach\mlxperPJT\deve10MQSplotAC.m

SpeedList=1000:1000:15000
ACLossJmag=...
[4355.6484417,
4496.78895445,
4702.58204942,
4985.34386333,
5333.31533767,
5734.53722212,
6158.92559051,
6620.03412326,
7132.27719291,
7681.37978144,
8240.95234081,
8805.84863344,
9404.4190626,
10026.804339,
10661.2973648];
Rph=0.007;
plot(SpeedList,ACLossJmag)

plot(SpeedList,ACLossJmag-3*Rph*460.^2)
hold on
%% 

%% get All ResultTable Obj
app                 =callJmag;
Model               =app.GetCurrentModel;
ResultTableFromCSV  =readJMAGWholeResultTables(app);
%% Plot
    % DC Loss  [W]
    % total Current
    uList=contains(currentDataStruct(1).dataTable.Properties.VariableNames,'u','IgnoreCase',true)
    uITable=currentDataStruct(1).dataTable(:,uList);
    uIVar=currentDataStruct(1).dataTable(:,uList).Variables;
    
    % single Conductor - U1C1
    u1C1List=contains(currentDataStruct(1).dataTable.Properties.VariableNames,'U1C1','IgnoreCase',true)
    u1C1Table=currentDataStruct(1).dataTable(:,u1C1List);
    u1C1Var=currentDataStruct(1).dataTable(:,u1C1List).Variables;
    SingleRphaseMCAD = resitivity2Resistance(mm2m(150*2), SingleCoilAreaInSqm, resitivitityMCAD)
    DCLossWaveu1C1Var= 4*SingleRphaseMCAD*u1C1Var(:,1).^2
    plot(u1C1Var(361:1:481,:))
    hold on
    plot(DCLossWaveu1C1Var(361:1:481,:))
    
    % single Conductor - U2C5
    u2C5List=contains(currentDataStruct(1).dataTable.Properties.VariableNames,'U2C5','IgnoreCase',true)
    u2C5Table=currentDataStruct(1).dataTable(:,u2C5List);
    u2C5Var=currentDataStruct(1).dataTable(:,u2C5List).Variables;
    SingleRphaseMCAD = resitivity2Resistance(mm2m(150*2), SingleCoilAreaInSqm, resitivitityMCAD)
    DCLossWaveu2C5Var=4*SingleRphaseMCAD*u2C5Var(:,1).^2
    plot(u2C5Var(361:1:481,:))
    hold on
    plot(DCLossWaveu2C5Var(361:1:481,:))
    % single Conductor - U2C19
    u2C19List=contains(currentDataStruct(1).dataTable.Properties.VariableNames,'U2C19','IgnoreCase',true)
    u2C19Table=currentDataStruct(1).dataTable(:,u2C19List);
    u2C19Var=currentDataStruct(1).dataTable(:,u2C19List).Variables;
    SingleRphaseMCAD = resitivity2Resistance(mm2m(150*2), SingleCoilAreaInSqm, resitivitityMCAD)
    DCLossWaveu2C19Var=4*SingleRphaseMCAD*u2C19Var(:,1).^2
    plot(u2C19Var(361:1:481,:))
    hold on
    plot(DCLossWaveu2C19Var(361:1:481,:))
    
    % Current * Resistance
    activePhaseResistance=MachineData.ResistanceActivePart
    6.8-3*Rph*460.5.^2/1000
    DCLossWaveU1=activePhaseResistance*uIVar(:,1:4).^2
    DCLossWaveU2=activePhaseResistance*uIVar(:,5:8).^2
    
    plot([DCLossWaveU1,DCLossWaveU2])
    % conductor
    Conductor=contains(jouleLosslist,'Conductor','IgnoreCase',true)
    ConductorList=jouleDataStruct(1).dataTable.Properties.VariableNames(Conductor)
    ConductorLoss=jouleDataStruct(1).dataTable(:,ConductorList)
    plot(ConductorLoss.Variables)
    % select conductor name
    jouleLosslist=jouleDataStruct(1).dataTable.Properties.VariableNames
    Slot1List=contains(jouleLosslist,'Slot1','IgnoreCase',true)
    Conductor1=contains(jouleLosslist,'Conductor_1','IgnoreCase',true)
    Conductor3=contains(jouleLosslist,'Conductor_3','IgnoreCase',true)
    Conductor2=contains(jouleLosslist,'Conductor_2','IgnoreCase',true)
    Conductor4=contains(jouleLosslist,'Conductor_4','IgnoreCase',true)    
    Slot2List=contains(jouleLosslist,'Slot2','IgnoreCase',true)
    Conductor1=contains(jouleLosslist,'Conductor_1','IgnoreCase',true)
    Conductor3=contains(jouleLosslist,'Conductor_3','IgnoreCase',true)
    Conductor2=contains(jouleLosslist,'Conductor_2','IgnoreCase',true)
    Conductor4=contains(jouleLosslist,'Conductor_4','IgnoreCase',true)   
    % U1C1
    U1C1List=jouleDataStruct(1).dataTable.Properties.VariableNames(Slot1List&(Conductor1))
    LossU1C1Var=jouleDataStruct(1).dataTable(:,U1C1List).Variables
    ACLossOnlyU1=LossU1C1Var(361:1:481,:)-DCLossWaveU1(361:1:481,:)
    % U2C5
    U2C5List=jouleDataStruct(1).dataTable.Properties.VariableNames(Slot1List&(Conductor4))
    LossU2C5Var=jouleDataStruct(1).dataTable(:,U2C5List).Variables
    ACLossOnlyU2C5=LossU2C5Var(361:1:481,:)-DCLossWaveu2C5Var(361:1:481,:)
    plot(ACLossOnlyU2C5)
    mean(ACLossOnlyU2C5)
    % U2C19
    U2C19List=jouleDataStruct(1).dataTable.Properties.VariableNames(Slot2List&(Conductor4))
    LossU2C19Var=jouleDataStruct(1).dataTable(:,U2C19List).Variables
    ACLossOnlyU2C19=LossU2C19Var(361:1:481,:)-DCLossWaveu2C19Var(361:1:481,:)
    plot(ACLossOnlyU2C19)
    mean(ACLossOnlyU2C19) 
    % 4 total AC Loss
    Slot1U1List=jouleDataStruct(1).dataTable.Properties.VariableNames(Slot1List&(Conductor1|Conductor3))
    Slot1U2List=jouleDataStruct(1).dataTable.Properties.VariableNames(Slot1List&(Conductor2|Conductor4))
    
    Slot2U1List=jouleDataStruct(1).dataTable.Properties.VariableNames(Slot2List&(Conductor1|Conductor3))
    Slot2U2List=jouleDataStruct(1).dataTable.Properties.VariableNames(Slot2List&(Conductor2|Conductor4))  
    %
    LossU1Var=jouleDataStruct(1).dataTable(:,Slot1U1List).Variables+jouleDataStruct(1).dataTable(:,Slot2U1List).Variables
    SumLossU1Var=LossU1Var(:,1)+LossU1Var(:,2)
    LossU2Var=jouleDataStruct(1).dataTable(:,Slot1U2List).Variables+jouleDataStruct(1).dataTable(:,Slot2U2List).Variables
    SumLossU2Var=LossU2Var(:,1)+LossU2Var(:,2)
    
    ACLossJMAG=P_rect1DData
    ACLossJMAG.DisplayName='ACLoss'
    ACLossOnlyU1=SumLossU1Var(361:1:481,:)-DCLossWaveU1(361:1:481,:)
    ACLossOnlyU2=SumLossU2Var(361:1:481,:)-DCLossWaveU2(361:1:481,:)  
    % plotXYarray([0:3:360]',LossU1Var(361:1:481,:),ACLossJMAG)
    % 
    % plotXYarray([0:3:360]',LossU2Var(361:1:481,:),ACLossJMAG)
    plotXYarray([0:3:360],shifted_signal2DJMAGG2,P_rect1DData);
    plotXYarray([0:3:360],1000*48*P_rec2DJMAGG2,P_rect1DData);
    hold on
    plotXYarray([0:3:360]',(ACLossOnlyU1+ACLossOnlyU2)/2,ACLossJMAG)   
    plotXYarray([0:3:360]',ACLossOnlyU1,ACLossJMAG)
    hold on
    plotXYarray([0:3:360]',ACLossOnlyU2,ACLossJMAG)
    
    length(ACLossVar(361:1:481,1))
    length([0:3:360])
%     end
% end

% Result
Model.CheckForNewResults
% Result Plot
% Z:\01_Codes_Projects\git_fork_emach\tools\loss\VeriCalcHybridACLossModelwithSlotB.mlx

ResultTableObj=curStudyObj.GetResultTable
ResultDataStruct = getJMagResultDatas(ResultTableObj,'voltage')
ResultTable=filterTablewithString(ResultDataStruct.dataTable,'');

ResultDataStruct.EndTime=EndTime;
ResultDataStruct.StepDivision=StepDivision;
ResultTable=struct2table(ResultDataStruct)
plotTransientTable(ResultTable,StepData)

plotJMAGResultDataStruct(ResultTable,StepData)
%% SC - 1-2 turn
ResultTableObj=curStudyObj.GetResultTable
ResultDataStruct       = getJMagResultDatas(ResultTableObj,'voltage')

%% SC - 1-3 turn