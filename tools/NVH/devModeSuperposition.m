 %
% m,n 
mcad = actxserver('MotorCAD.AppAutomation');

%%Spatial -m
[Success,ForceMaxOrder_Space_Stator_OC]=mcad.GetVariable('ForceMaxOrder_Space_Stator_OC')  
m=ForceMaxOrder_Space_Stator_OC
%%Temporal - n
[Success,ForceMaxOrder_Time_OL]=mcad.GetVariable('ForceMaxOrder_Time_OL')  
[Success,ForceMaxOrder_Time_OC]=mcad.GetVariable('ForceMaxOrder_Time_OC')
[Success,AreaMomentInertia_Stator]=mcad.GetVariable('AreaMomentInertia_Stator') %[mm^4]



diameter = 282;  % 원통의 지름 (mm)
height = 130;   % 원통의 높이 (mm)

radius = diameter / 2;  % 원통의 반지름 (mm)
radiusM= radius/1000    %  원통의 반지름 [m]
area = pi * radius^2;   % 원통의 밑면의 면적 (mm^2)
areaM = pi * radiusM^2;   % 원통의 밑면의 면적 (m^2)

disp('면적:');
disp(area);

ForceMaxOrder_Time_OL=double(ForceMaxOrder_Time_OL)
NumGraphPoints = double(m);
%% 
LumpK=zeros(NumGraphPoints,1)  % []
LumpM=zeros(NumGraphPoints,1)
NaturalFreq=zeros(NumGraphPoints,1)

%% Get MotorCAD Data

% setGraphName{dataIndex}
setGraphName={'NVH_LumpedStiffness','NVH_LumpedMass','NVH_NaturalFrequency'}
for loop = 0:NumGraphPoints
    [success,x,y1] = mcad.GetMagneticGraphPoint(setGraphName{1}, loop);    
    [success,x,y2] = mcad.GetMagneticGraphPoint(setGraphName{2}, loop);    
    [success,x,y3] = mcad.GetMagneticGraphPoint(setGraphName{3}, loop);    
    if success == 0
        ModeNumber(loop+1) = x;
        LumpK(loop+1) = y1;  %[MN/m]
        LumpM(loop+1) = y2;
        NaturalFreq(loop+1) = y3;
    end
end


%% Raw Force Data 

%% Radial Force 2D FFT Data  (2*m,2*n) due to 2D FFT for single Point

seriesName='Fr_Density_Stator_FFT_Amplitude_OL'
sliceNumber=1;
pointNumber=1;
timeStepNumber=1;


forceDensity=zeros(m,n);  %Force Density  - [N/m^2]
F_hat   = forceDensity*areaM;
% F_hat=zeros(2*m,2*n);  %Force  - [N]

% m_values = 0:8;
m_values= 0:360*2-1                                 ;
ForceTemporalOrder=0:ForceMaxOrder_Time_OL*2-1      ;

% Find roots for each combination of m and n
for i = 1:length(m_values)
    m = m_values(i);
    for j = 1:length(ForceTemporalOrder)
        [Success,x,y]=mcad.GetMagnetic3DGraphPoint(seriesName, 1, m, ForceTemporalOrder(j));
        % Solve the equation for Omega_mn
        forceDensity(i,j)=y
        % Store the solutions for the current combination of m and n

    end
end

%% AG Force or Br Bt


%% 2D FFT


forceDensity2DFFT

%% Calc Static Displacement [mm] -> dB
F_hat   = fr_i'*areaM;
Fsamp=F_hat(1:361,:);
x_ms=calcStaticDisplace(Fsamp,LumpK);
xdB=x_ms/10e-8;

figure(1)
axis equal

imagesc(xdB)
set(gca,'xgrid', 'on', 'ygrid', 'on', 'gridlinestyle', '-');
ax=gca;
ax.GridColor=[1, 1, 0.1];

c=colorbar;
% c.Label.String = unit;
caxis([min(xdB(:)), max(xdB(:))]); % Adjust the colorbar limits based on the data range
% 
% set(gca,'fontweight','bold','YTick',[1:size(xdB,1)],'YTickLabel',YTicklabel_flip, ...
%     'XTick',[1:size(xdB,2)],'XTickLabel',[0:p:l_magBr/(p*2)]);

xlabel('Mech Order')
ylabel('Wavenumber')

%%
% Reshape the xdB array into a column vector
xdB_vector = reshape(xdB, [], 1);

% Find the indices of the largest values
[~, sorted_indices] = sort(xdB_vector, 'descend');

% Get the indices of the top 10 largest values
top_10_indices = sorted_indices(1:10);

% Get the corresponding values from xdB array
top_10_values = xdB_vector(top_10_indices);

% Display the top 10 largest values
disp("Top 10 Largest Values in xdB:");
disp(top_10_values);


%% MagFactor


%% Dynamic Displacement 


%% Velocity


%% Acceleration



%% Spectrogram


%% Spatiogram



%% Sound

 