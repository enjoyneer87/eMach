slot=72;
p=12;
drawModelGeomAngle=360/gcd(12,72)
drawModelSlotQuant=72/gcd(12,72)
angleOneSlot=drawModelGeomAngle/drawModelSlotQuant;

startAngle=drawModelGeomAngle/drawModelSlotQuant/2


%% 
slotType = 1;
% Parallel Tooth
% Parallel Tooth Sqb
% Parallel Slot
% Slotless
% Form Wound
% Tapered Slot
statorDuct
p_Stator_Slots 

%% Absoulute Input (left table)

p_Pole_Pair    
p_Stator_Slots 
i_Slot_Corner_Radius
p_Tooth_Tip_Depth
p_Tooth_Tip_Angle
%% Rotor Parameter
%  Layer 1 - insider

L1_Magnet_Thickness  
L1_Bridge_Thickness  
L1_Pole_V_angle      
L1_Magnet_Post       
L1_Magnet_Separation 
L1_Magnet_Segments   
%     # L1 Mag Gap Inner
%     # L1 Mag Gap Outer
% Layer 2


%% Ratio - ParallelTooth
if slotType==1
    i_Stator_OD=400
    i_Split_Ratio                       =0.70  % constraints i_Stator_OD
    statorBore=i_Stator_OD*i_Split_Ratio;
    Ratio_SlotDepth_ParallelTooth=1;
    Ratio_ToothWidth=0.6
    Ratio_SlotOpening_ParallelTooth
    slotDepth=(statorBore-statorThick)
    i_YtoT                              =2.5                 %ratio user defined YtoT 
    
    
    38.72/20.27
    p_Airgap_Mecha
    
    % scaled


%%
jv='210'
app = actxserver(strcat('designer.Application.',jv));
app.View().SetCurrentCase(1)

app.GetModel("HDEV_201019_LdLq_0").RestoreCadLink(1)

% geoApp=jmag.CreateGeometryEditor(1).GetDocument()

HDEV=JmagData(12)
app = designer.GetApplication()

geomApp = app.CreateGeometryEditor(1)

geomApp.GetDocument().GetSelection().Paste()
geomApp.GetDocument().GetAssembly().GetItem("so_009:so_009").OpenSketch()
geomApp.GetDocument().GetAssembly().GetItem("so_009:so_009").GetItem("Region Circler Pattern.2").SetProperty("Angle", angleOneSlot)
geomApp.GetDocument().GetAssembly().GetItem("so_009:so_009").GetItem("Region Circler Pattern").SetProperty("Angle", angleOneSlot)
geomApp.GetDocument().GetAssembly().GetItem("so_009:so_009").GetItem("Half of the Center Angle").SetProperty("Angle", startAngle)
%% Jmag Stator
geomApp.GetDocument().GetAssembly().GetItem("so_009:so_009").GetItem("SD1: Outside Diameter").SetProperty("Diameter", i_Stator_OD)
geomApp.GetDocument().GetAssembly().GetItem("so_009:so_009").GetItem("SD2: Inside Diameter").SetProperty("Diameter", 280)

