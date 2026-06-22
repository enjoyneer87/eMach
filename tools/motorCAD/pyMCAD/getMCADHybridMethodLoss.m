function [ACLossTable,HybridConductorSkinDepth,Conductor_DCLossEmagMCAD,DCConductorLoss_Armature_A]=getMCADHybridMethodLoss(mcad)
    % ActiveXStr=load('mcadActiveXparameterList.mat');
    ActiveXParameters = readMcadActiveX2Table("D:\KangDH\Thesis\e10\refModel\ActiveXParameters_ACLoss.txt");
    ACLossTable=getMcadTableVariable(ActiveXParameters,mcad);
    ACLossWattTable = filterMCADTableWithAnyInfo(ACLossTable, 'Watts','Units');
    [~,HybridConductorSkinDepth]                  =mcad.GetVariable('ConductorSkinDepth');
    % [~,ACConductorLoss_MagneticMethod_Total       =mcad.GetVariable('ACConductorLoss_MagneticMethod_Total');
    [~,Conductor_DCLossEmagMCAD]                  =mcad.GetVariable('ConductorLoss');
    [~,DCConductorLoss_Armature_A]                 =mcad.GetVariable('DCConductorLoss_Armature_A');
    % [~,ACLossHighFrequencyScaling_Method] =
    % [~,HybridACLossMethod]
    % [~,HairpinConductors_FEA]
end

%[appendix]{"version":"1.0"}
%---
