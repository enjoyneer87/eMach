function Pcoil_AC_scaledTable = scaleSpeedACLossFromMcadLinkTable(MCADLinkTable, MachineData, nTarget,zeta)

% MachineData=refLABBuildData;
% MCADLinkTable=originLabLinkTable;

nBuild=MachineData.LabBuildData.n2ac_MotorLAB;
% contains(MCADLinkTable.Properties.VariableNames,'AC')


ACLossTable=filterTablewithString(MCADLinkTable,'AC Copper');

% 결과를 저장할 테이블 초기화 (ACLossTable과 같은 구조)
Pcoil_AC_scaledTable = ACLossTable;

% ACLossTable의 모든 변수(열)에 대해 반복
for varName = ACLossTable.Properties.VariableNames
    % 각 변수에 대한 AC 손실 값 추출
    AC_Loss_Ref = ACLossTable.(varName{1});
    
    % scaleSpeedCoilACLoss 함수를 호출하여 손실 값을 스케일링
    Pcoil_AC_scaled = scaleSpeedCoilACLoss(AC_Loss_Ref, nBuild, nTarget);
    
    % 결과를 새 테이블에 저장
    Pcoil_AC_scaledTable.(varName{1}) = Pcoil_AC_scaled;
end