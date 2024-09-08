%% 

%% MS 
% eq magnetizing Current Density 
% armature Current Density  - diffused

% eq 4 

%% JplotReader
% A
% Node
% print("Id: {:d}, x: {:f}, y: {:f}, z: {:f}".format(id.value, x.value, y.value, z.value))
% element
% print("Id: {:d}, Part Id: {:d}, Element type: {:d}, x: {:f}, y: {:f}, z: {:f}, area:
% {:f}".format(id.value, partId.value, eleType.value, x.value, y.value, z.value, area.value))
% nodal displacement
% print("Id: {:d}, dx: {:f}, dy: {:f}, dz: {:f}".format(id.value, dx.value, dy.value, dz.value))
% element displacement
% print("Id: {:d}, dx: {:f}, dy: {:f}, dz: {:f}".format(id.value, dx.value, dy.value, dz.value))
% component Data
% print("Id: {:d}, {:f}, {:f}, {:f}".format(id.value, values[0], values[1], values[2]))
%%
app=callJmag;


%% Total Mesh
MPToolCSVFilePath='Z:/Simulation/JEETACLossValid_e10_v24/refModel/ExportMPtools/MSField.csv'
keyword='11005'; % MVP
% keyword='16001'; % B
[model,pdeTriElements,pdeNodes,pdeQuadElements]  = nastran2PDEMesh(MPToolCSVFilePath);
%% WireStruct
PartStruct=getJMAGDesignerPartStruct(app);
Lactive=150
idx=findMatchingIndexInStruct(PartStruct,'Name','Stator/Region.');
WireStruct=PartStruct(idx);


outputMatPath='Z:\01_Codes_Projects\git_Pyleecan_fork\output_data.mat';
% case1DataNoLoadFP=load(outputMatPath)
case1DataLoadFP  =load(outputMatPath)
case1DataLoadFP  =load(outputMatPath)

save('MScase1_NoLoadFP.mat',"case1DataNoLoadFP")
load('MScase1_NoLoadFP')
save('MScase1_LoadFP.mat',"case1DataLoadFP")
load('MScase1_LoadFP')

endtime=1/rpm2freqE(1000,4);


%% Get Wire Element and Node ID
for SlotIndex=1:length(WireStruct)
    WireIndex=WireStruct(SlotIndex).partIndex;
    [WireStruct(SlotIndex).ElementId, WireStruct(SlotIndex).NodeID,WireStruct(SlotIndex).NodeTable] =getMeshData(app,WireIndex);
end




%% get Jeddy 2 Wire Struct 
% Noload (Field)
DataStruct=case1DataNoLoadFP;
WireStruct=calcJeddyFPMethod(DataStruct,WireStruct,endtime);

for SlotIndex=1:length(WireStruct)
 WireStruct(SlotIndex).MVP_NoLoadFP       =WireStruct(SlotIndex).MVPTimeTable;
 WireStruct(SlotIndex).JeField_NoLoadFP   =WireStruct(SlotIndex).JeleTimeTable;
end
WireStruct = rmfield(WireStruct, 'MVPTimeTable');
WireStruct = rmfield(WireStruct, 'JeleTimeTable');

% Load (Armature)
DataStruct=case1DataLoadFP;
WireStruct=calcJeddyFPMethod(DataStruct,WireStruct,endtime);
for SlotIndex=1:length(WireStruct)
 WireStruct(SlotIndex).MVP_LoadFP          =WireStruct(SlotIndex).MVPTimeTable;
 WireStruct(SlotIndex).JeArmature_LoadFP   =WireStruct(SlotIndex).JeleTimeTable;
end

for SlotIndex=1:length(WireStruct)
WireStruct(SlotIndex).JeddyTotal      =(WireStruct(SlotIndex).JeArmature_LoadFP+WireStruct(SlotIndex).JeField_NoLoadFP);
WireStruct(SlotIndex).EddyLossByMVP   =WireStruct(SlotIndex).JeddyTotal.^2.*WireStruct(SlotIndex).elementCentersTable.area'.*mm2m(Lactive);
end


%% Plot
for SlotIndex=1:length(WireStruct)
    JeleTimeTable=WireStruct(SlotIndex).JeddyTotal;
    Jele         =JeleTimeTable.ElementID;
    elementPos   =[m2mm(WireStruct(SlotIndex).elementCentersTable.x) m2mm(WireStruct(SlotIndex).elementCentersTable.y)];
    % Jele Per Element Pos
    % for DataIndex=10:10:NumTimeStep
    % col = color_code(DataIndex*2);
    scatter3(elementPos(:,1),elementPos(:,2),max(Jele(:,:).^2)/1e16)
    hold on
    % end
end


for SlotIndex=1:length(WireStruct)
    EddyLossByMVP=WireStruct(SlotIndex).EddyLossByMVP;
    EddyLoss     =EddyLossByMVP.ElementID;
    elementPos   =[m2mm(WireStruct(SlotIndex).elementCentersTable.x) m2mm(WireStruct(SlotIndex).elementCentersTable.y)];
    % Jele Per Element Pos
    % for DataIndex=10:10:NumTimeStep
    % col = color_code(DataIndex*2);
    % scatter3(elementPos(:,1),elementPos(:,2),max(EddyLoss(:,:))/1e8)
    hold on
    % end

    plotCurrentDensityContour(elementPos, EddyLoss)
    hold on
end

pdemesh(model)

% eddy curent density 
% i conductor 
% j element
% actual current dnesity - diffsued 




% Np parallel circuit 
% s is area of element
% Ne is number of elements
