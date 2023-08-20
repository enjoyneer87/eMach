function PlaidMotorDimension=GeometrydataSet4ppt(fileDir,fileName,Rating,mcad)
% mcad=actxserver('motorcad.appautomation');
%% 
filePath=fullfile(fileDir,fileName)

mcad.LoadFromFile(filePath);

PlaidMotorDimension=struct();
kwPower=Rating.maxkW;  % kW
%고정자
[~,PlaidMotorDimension.Stator.StatorDia]             =mcad.GetVariable('Stator_Lam_Dia')         
[~,PlaidMotorDimension.Stator.StatorBore]            =mcad.GetVariable('Stator_Bore')                
[~,PlaidMotorDimension.Stator.Slot_Depth]           =mcad.GetVariable('Slot_Depth') 
[~,PlaidMotorDimension.Stator.Slot_Opening]                                =mcad.GetVariable('Slot_Opening')
[~,PlaidMotorDimension.Stator.Ratio_SlotOpening_ParallelTooth]           =mcad.GetVariable('Ratio_SlotOpening_ParallelTooth')
[~,PlaidMotorDimension.Stator.Tooth_Width]           =mcad.GetVariable('Tooth_Width')   

% 엔드권선
[~,PlaidMotorDimension.Stator.Winding.ArmatureEWdgMLT_Calculated]                         =mcad.GetVariable('ArmatureEWdgMLT_Calculated') %권선        
[~,PlaidMotorDimension.Stator.Winding.EWdg_Overhang_FrontUsed]                            =mcad.GetVariable('EWdg_Overhang_[F]_Used')    
[~,PlaidMotorDimension.Stator.Winding.EWdg_Overhang_RearUsed]                             =mcad.GetVariable('EWdg_Overhang_[R]_Used')    

% 회전자            
[~,PlaidMotorDimension.Rotor.RotorDiameter]               =mcad.GetVariable('RotorDiameter')      %회전자   
[~,PlaidMotorDimension.Rotor.RotorBore]                   =mcad.GetVariable('Shaft_Dia')         
            
[~,PlaidMotorDimension.Rotor.MagnetThickness_Array]       =mcad.GetVariable('MagnetThickness_Array')      %공극   
[~,PlaidMotorDimension.Rotor.MagnetBarWidth_Array]        =mcad.GetVariable('MagnetBarWidth_Array')      %공극   

%% Misl
[~,PlaidMotorDimension.Banding_Thickness]                         =mcad.GetVariable('Banding_Thickness')         
[~,PlaidMotorDimension.AirGap]                         =mcad.GetVariable('AirGap')         
PlaidMotorDimension.ActiveAirGap    =  PlaidMotorDimension.Banding_Thickness- PlaidMotorDimension.AirGap         

%% Length
[~,PlaidMotorDimension.Rotor_Lam_Length]                  =mcad.GetVariable('Shaft_Dia')      %적층   
[~,PlaidMotorDimension.Stator_Lam_Length]                 =mcad.GetVariable('Stator_Lam_Length')      %적층   

% Volume
[~,PlaidMotorDimension.ActiveVolume]           =mcad.GetVariable('ActiveVolume')  %mm^3 
PlaidMotorDimension.ActiveVolume=PlaidMotorDimension.ActiveVolume %m^3

% Volume Density
kwPower/PlaidMotorDimension.ActiveVolume

% Weight
Weight=getMCADWeight(mcad)
% 파트별 무게

[~,PlaidMotorDimension.Weight.WeightStatorCore]             =mcad.GetVariable('Weight_Total_Stator_Lam')   
[~,PlaidMotorDimension.Weight.RotorCoreWeight]              =mcad.GetVariable('Weight_Total_Rotor_Lam')         
[~,PlaidMotorDimension.Weight_Total_Magnet]          =mcad.GetVariable('Weight_Total_Magnet')         
[~,PlaidMotorDimension.Weight.Weight_Total_Banding]  =mcad.GetVariable('Weight_Total_Banding')      % carbon sleeve   



PlaidMotorDimension.Weight.StatorAssembly       = Weight.o_Weight_Stat_Core + Weight.o_Weight_Wdg
PlaidMotorDimension.Weight.RotorAssembly        = Weight.o_Weight_Mag+Weight.o_Weight_Rot_Core+Weight.Weight_Shaft+PlaidMotorDimension.Weight.Weight_Total_Banding

% Assembly Mass
PlaidMotorDimension.Weight.Total_Assembly=      PlaidMotorDimension.Weight.StatorAssembly +PlaidMotorDimension.Weight.RotorAssembly  
PlaidMotorDimension.Weight=PlaidMotorDimension.Weight,Weight


% Ratio of Total Assembly

PlaidMotorDimension.Weight.WeightStatorCore/PlaidMotorDimension.Weight.Total_Assembly
PlaidMotorDimension.Weight.StatorAssembly/PlaidMotorDimension.Weight.Total_Assembly
PlaidMotorDimension.Weight.RotorCoreWeight/PlaidMotorDimension.Weight.Total_Assembly
PlaidMotorDimension.Weight.RotorAssembly/PlaidMotorDimension.Weight.Total_Assembly
PlaidMotorDimension.Weight_Total_Magnet/PlaidMotorDimension.Weight.Total_Assembly

% Mass Density

kw2hp(kwPower)/(23.8+16.3)  % Active Mass
kw2hp(kwPower)/(134) % Mass Density with Large Unit
kw2hp(kwPower)/(92)  % Mass Density with Small Unit
% Comp
670/73      % Lucid


% 
screens = {'Radial','StatorWinding'};
for j = 1:numel(screens)
    screenname = screens{j};
    fileName = [fileDir, '\Pic_', screenname, '.png'];
    mcad.SaveScreenToFile(screenname, fileName);
end