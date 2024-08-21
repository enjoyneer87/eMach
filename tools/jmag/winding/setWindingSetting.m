function CoilWindingInfo=setWindingSetting(Study,CoilWindingInfo,fileName)

    % Study=app.GetModel(0).GetStudy(0);
    % WindingDefinition Obj
    GetWinding=Study.CreateWinding("ThreePhase", "WaveWinding");
    %% Get Circuit Info
    Circuit=Study.GetCircuit();
    NumComponents=Circuit.NumComponents();
    NumInstances=Circuit.NumInstances();
    for InstanceIndex=1:NumComponents
    Component=Circuit.GetComponent(InstanceIndex-1);
        if Component.IsValid==1
        ComponentStrName{InstanceIndex}=Component.GetName;
        end
    end    
    %% Get Component List regardless Type
    CoilIndex=contains(ComponentStrName,'Coil');
    CoilComponent=ComponentStrName(CoilIndex);
    ConductorIndex=contains(ComponentStrName,'Conductor');
    ConductorComponent=ComponentStrName(ConductorIndex);

    %% Check Validity of ComponentList -  Circuit 상 Component종류에 따른 InputType 설정
    if isempty(CoilComponent)
    Study.GetWinding("WaveWinding").SetInputType(5)
    Study.GetWinding("WaveWinding").SetComponent("Winding Three Phase Conductor1")
    elseif ~isempty(CoilComponent)
    Study.GetWinding("WaveWinding").SetInputType(1)
    Study.GetWinding("WaveWinding").SetComponent(CoilComponent{:})
    % Study.GetWinding("WaveWinding").SetSlotFillFactor(37)
    end

    %% WindingDefinition Obj
    GetWinding=Study.GetWinding("WaveWinding");
    Resistance=GetWinding.ActualResistance;
    CoilWindingInfo.PhaseResistance=Resistance;
    %% 3D
    % Import CSV 
    % if Study.GetWinding("WaveWinding").IsValid==0
    % Study.GetWinding("WaveWinding").ImportCoilSetting(testExportCSVPath)
    % exportFilePath=strcat(fileparts(testExportCSVPath),'\export.csv');
    % GetWinding.ExportCoilSetting(exportFilePath)
    % end
    %% 2D
    % importJMAGCoilsFromCSV(fname,app);
    importJMAGCoilsFromCSV(fileName)

    %%
    if nargin<3
        disp('코일설정이 필요합니다')
    else
        Study.GetWinding("WaveWinding").SetSlotFillFactor(CoilWindingInfo.FillFactor)
        Study.GetWinding("WaveWinding").SetCoilPitch(CoilWindingInfo.Pitch)
        Study.GetWinding("WaveWinding").SetTurns(CoilWindingInfo.NumberofTurn)
    end


    %%
end
