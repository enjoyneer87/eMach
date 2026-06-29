%[text] 
%[text:tableOfContents]{"heading":"목차"}
%[text] 주어진 이름 목록
%[text] Bertotti 빈 cell 배열로 초기화
function updatedTable = reNameLabTable2LabLink(inputTable)
% [inputTable.('Is'),inputTable.('Current Angle')]=dq2pkBeta(inputTable.Id_Peak,inputTable.Iq_Peak);
% CurrentAngle=unique(inputTable.("Current Angle"));
% extractedValues = extractNonNegative(CurrentAngle);
% inputTable = replaceGammaWithNonNegativeValues(inputTable);
%[text] %[text:anchor:H_E6149E97] ## nameTable
%[text] %[text:anchor:H_812B7E0E] #### pkbeta current
LabTableCurrentNameCell={
'SatModel_Is_Lab'
'SatModel_Gamma_Lab'
};
labLinkCurrentNameCell={
    'Is'
    'Current Angle'
    };

% inputTable.Properties.VariableNames=strrep(inputTable.Properties.VariableNames,'SatModel_Is_Lab','Is');
% inputTable.Properties.VariableNames=strrep(inputTable.Properties.VariableNames,'SatModel_Gamma_Lab','Current Angle');
nameTable = table(LabTableCurrentNameCell, labLinkCurrentNameCell, 'VariableNames', {'LabTableCell', 'LabLinkCell'});
%[text] %[text:anchor:H_F1A1574A] ### Psi LabTable Foramt
fluxNameCell={
'PsiDModel_Lab'
'PsiQModel_Lab'
'Ld_MotorLAB'
'Lq_MotorLAB'
};
% LabLink Format
labLinkfluxNameCell={
'Flux Linkage D'
'Flux Linkage Q'
'Ld'
'Lq'
};
newRows = table(fluxNameCell,labLinkfluxNameCell, 'VariableNames', nameTable.Properties.VariableNames);
nameTable = [nameTable; newRows];
%[text] %[text:anchor:H_10CD21B1] ### Iron Loss
% % LabTable Foramt
TotalIronLossCell={
'FeEddyLossArray_MotorLAB'            D:\KangDH\EveryMotor\eMach\+mcad\fromFitResult.m   %  'Hysteresis Iron Loss' 
'FeHysLossArray_MotorLAB'                %  'Eddy Iron Loss'
};
% newRows = table(TotalIronLossCell, TotalIronLossCell, 'VariableNames', nameTable.Properties.VariableNames);
% nameTable = [nameTable; newRows];
%[text] %[text:anchor:H_D2E2E7CB] #### \[TB\]Steinmetz (default)
%[text] exccess Loss 'Hysteresis Iron Loss (Stator)' 'Eddy Iron Loss (Stator)' 
LossParameter_MotorLAbCell={
     'FeHysLossArray_MotorLAB'   
     % 'FeHysLossArray_Stator_Lab' 
     % 'FeHysLossArray_Rotor_Lab'  
     'FeEddyLossArray_MotorLAB'  
     % % 'FeEddyLossArray_Stator_Lab'
     % 'FeEddyLossArray_Rotor_Lab' 
     'FeLossRotorEd_MotorLAB'    
     'FeLossBackIronEd_MotorLAB' 
     'FeLossToothEd_MotorLAB'    
     'FeLossRotorHy_MotorLAB'    
     'FeLossBackIronHy_MotorLAB' 
     'FeLossToothHy_MotorLAB'    
     'FeLossRotorPoleHy_MotorLAB'
     'FeLossRotorPoleEd_MotorLAB'
     };
%[text] %[text:anchor:H_FC317AA9] ####  LabLink Format
labLinkFeLossCell={
 'Hysteresis Iron Loss'
  % 'Hysteresis Iron Loss (Stator)'
  % 'Hysteresis Iron Loss (Rotor)'
 'Eddy Iron Loss'
 % 'Eddy Iron Loss (Stator)'
 % 'Eddy Iron Loss (Rotor)'
 'Eddy Iron Loss (Rotor Back Iron)'
 'Eddy Iron Loss (Stator Back Iron)'
 'Eddy Iron Loss (Stator Tooth)'
 'Hysteresis Iron Loss (Rotor Back Iron)'
 'Hysteresis Iron Loss (Stator Back Iron)'  
 'Hysteresis Iron Loss (Stator Tooth)'    
 'Hysteresis Iron Loss (Rotor Pole)'
 'Eddy Iron Loss (Rotor Pole)'
 };
newRows = table(LossParameter_MotorLAbCell, labLinkFeLossCell, 'VariableNames', nameTable.Properties.VariableNames);
nameTable = [nameTable; newRows];
%[text] %[text:anchor:H_3D4B6824] ### otherLoss
% LabTable Foramt
otherLossNameCell={
'MagLossArray_MotorLAB'
'LossModel_Sleeve_Lab'
'LossModel_Banding_Lab'
};
% LabLink Format
labLinkOtherLossNameCell={
'Magnet Loss'
'Sleeve Loss'  
'Banding Loss'
};
newRows = table(otherLossNameCell, labLinkOtherLossNameCell, 'VariableNames', nameTable.Properties.VariableNames);
nameTable = [nameTable; newRows];
%[text] %[text:anchor:H_04C4523F] ### dq Current
currentNameCell={
'Id_Peak'
'Iq_Peak'};
newRows = table(currentNameCell, currentNameCell, 'VariableNames', nameTable.Properties.VariableNames);
nameTable = [nameTable; newRows];

%[text] %[text:anchor:H_21275613] ### AC Loss
currentVariableNames = inputTable.Properties.VariableNames;
ACLossIndex=findMatchingIndex(currentVariableNames,'AC Copper');
ACLossCell=currentVariableNames(ACLossIndex)';
newRows = table(ACLossCell, ACLossCell, 'VariableNames', nameTable.Properties.VariableNames);
nameTable = [nameTable; newRows];
%[text] %[text:anchor:H_BD0F615D] ### other
totalACLossCell={'Stator_Copper_Loss_AC'};
newRows = table(totalACLossCell,totalACLossCell, 'VariableNames', nameTable.Properties.VariableNames);
nameTable = [nameTable; newRows];
%[text] %[text:anchor:H_B10A7390] ## inputTable과 이름 테이블 동기화


pkGammCurrentNameCell={
'LossModel_Is_Lab'
'LossModel_Gamma_Lab'};
updatedTable=filterOutTablewithString(inputTable,[pkGammCurrentNameCell;TotalIronLossCell;totalACLossCell;currentNameCell]);


matchingRows2Table = filterMCADTableWithAnyInfo(nameTable, TotalIronLossCell,'LabTableCell',1);
matchingRows2Table = filterMCADTableWithAnyInfo(matchingRows2Table, totalACLossCell,'LabTableCell',1);
matchingRows2Table = filterMCADTableWithAnyInfo(matchingRows2Table, currentNameCell,'LabTableCell',1);

updatedNameTable = removeUnmatchedRows(matchingRows2Table, updatedTable);

updatedNameTable.LabLinkCell=replaceUnderscoresWithSpace(updatedNameTable.LabLinkCell);
%[text] %[text:anchor:H_DB9C908C] ## 
%[text] %[text:anchor:H_B7208559] ## 변경된 이름을 테이블에 적용
updatedTable.Properties.VariableNames = updatedNameTable.LabLinkCell;

updatedTable=sortrows(updatedTable,'Is','ascend');
end

%[appendix]{"version":"1.0"}
%---
