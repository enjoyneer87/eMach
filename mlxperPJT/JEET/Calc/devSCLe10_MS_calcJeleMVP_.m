%% 

%% MS 
% eq magnetizing Current Density 
% armature Current Density  - diffused
%% get Jeddy 2 Wire Struct 
% Noload (Field)
DataStruct=case1DataNoLoadFP;
WireStruct=calcJeddyFPMethod(DataStruct,WireStruct,endtime);

for SlotIndex=1:length(WireStruct)
WireStruct(SlotIndex).JeddyTotal      =WireStruct(SlotIndex).JeleTimeTable;
WireStruct(SlotIndex).EddyLossByMVP   =WireStruct(SlotIndex).JeddyTotal.^2.*WireStruct(SlotIndex).elementCentersTable.area'.*mm2m(Lactive);
end


%% Plot No Load
%% Plot - MVP
ColorList=colormap("jet");

SlotList=[ones(1,4), 4*ones(1,4), 100*ones(1,4),120*ones(1,4),230*ones(1,4),236*ones(1,4)]
for TimeIndex=1:20:120
    for SlotIndex=1:length(WireStruct)
        MVPTimeTable=WireStruct(SlotIndex).MVPTimeTable;    
        MVP         =MVPTimeTable.Variables;
        NodePos   =[(WireStruct(SlotIndex).NodeTable.nodeCoords(:,1)) (WireStruct(SlotIndex).NodeTable.nodeCoords(:,2))];
        scatter3(NodePos(:,1),NodePos(:,2),(MVP(TimeIndex,:)),'MarkerFaceColor',ColorList(2*TimeIndex,:),'MarkerEdgeColor','k');
        hold on
        % end
    end
end

%% Scatter N Contour J


for timeIndex=1:30:240
    for SlotIndex=1:length(WireStruct)
        EddyLossByMVP=WireStruct(SlotIndex).EddyLossByMVP;
        EddyLoss     =EddyLossByMVP.ElementID;
        elementPos   =[m2mm(WireStruct(SlotIndex).elementCentersTable.x) m2mm(WireStruct(SlotIndex).elementCentersTable.y)];
        figure(timeIndex)
        scatter3(elementPos(:,1),elementPos(:,2),EddyLoss(timeIndex,:))
        plotCurrentDensityContour(elementPos, EddyLoss(timeIndex,:))
        hold on
    end
end
pdemesh(model)

% eddy curent density 
% i conductor 
% j element
% actual current dnesity - diffsued 




% Np parallel circuit 
% s is area of element
% Ne is number of elements
