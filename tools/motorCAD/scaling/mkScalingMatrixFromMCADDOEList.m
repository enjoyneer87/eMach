function kRadialMatrix= mkScalingMatrixFromMCADDOEList(ListTable2Build)

%% MachineDta 가져오기 
% [SLScaledMachineData, SLLabTable, refTable] = scaleTable4LabTable(scaleFactor, filteredTable, BuildingData);
% BuildList(MotFileIndex).SLScaledMachineData = SLScaledMachineData;
% BuildList(MotFileIndex).SLLabTable = SLLabTable;

%% ST Dia Table 가져오기
num_designs=height(ListTable2Build);
for i = 1:num_designs
    for j = 1:num_designs
        if i ~= j
            kRadialMatrix(i, j) = (ListTable2Build.BuildingData(i).MotorCADGeo.Stator_Lam_Dia / ListTable2Build.BuildingData(j).MotorCADGeo.Stator_Lam_Dia) ;
        end
    end
end
% 
% for i=1:num_designs
% 
%     dias(i,1)=ListTable2Build.BuildingData(i).MotorCADGeo.Stator_Lam_Dia
% 
% end

end