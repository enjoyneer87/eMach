app=callJmag('231');
app.Show
ProbeType   ="MagneticFluxDensity" ;                 
ProbeName   ='ProbeB'              ;    
ProjectDirName ='JEET'
%% MQS Ref
clear ProbeNameNPoint
ProbeNameNPoint{1}         ={"63.030692799",     "53.7999768547",   "0", "R4_"};
ProbeNameNPoint{end+1}     ={"61.5631904602051", "55.4568901062012","0", "L4_"};
ProbeNameNPoint{end+1}     ={"64.5096282958984", "55.0635147094727","0", "R3_"};
ProbeNameNPoint{end+1}     ={"63.0255012512207", "56.7243804931641","0", "L3_"};
ProbeNameNPoint{end+1}     ={"65.9719390869141", "56.3747138977051","0", "R2_"};
ProbeNameNPoint{end+1}     ={"64.5314636230469", "58.013729095459" ,"0", "L2_"};
ProbeDataByModel{1}=ProbeNameNPoint;
%% MQS SC
clear ProbeNameNPoint
ProbeNameNPoint{1}         ={"2*63.030692799",     "2*53.7999768547",   "0", "R4_"};
ProbeNameNPoint{end+1}     ={"2*61.5631904602051", "2*55.4568901062012","0", "L4_"};
ProbeNameNPoint{end+1}     ={"2*64.5096282958984", "2*55.0635147094727","0", "R3_"};
ProbeNameNPoint{end+1}     ={"2*63.0255012512207", "2*56.7243804931641","0", "L3_"};
ProbeNameNPoint{end+1}     ={"2*65.9719390869141", "2*56.3747138977051","0", "R2_"};
ProbeNameNPoint{end+1}     ={"2*64.5314636230469", "2*58.013729095459" ,"0", "L2_"};
ProbeDataByModel{2}=ProbeNameNPoint;

%% 반복
NumModels=app.NumModels;
for ModelIndex=1:NumModels
    curModelObj=app.GetModel(ModelIndex-1);
    ModelName=curModelObj.GetName;
    mkJMAGProbeGraphObj(app,ModelName,ProbeDataByModel{ModelIndex},ProbeType,ProbeName)
    SlotBCSVPath{ModelIndex}=exportJMAGProbeValueTable(app,ProbeName,ProjectDirName);
end