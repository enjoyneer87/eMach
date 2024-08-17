function PartStruct=changeJMAGDesignerPartName(PartStruct,app,MachineData)
%% devfuncchangeJMAGDesignerPartName.mlx
  runnerType         = MachineData.runnerType          ;
    if strcmp(runnerType,'InnerRotor')
     PartStruct=changeJMAGDesignerPartName4InnerRotor(PartStruct,app);
    elseif     strcmp(runnerType,'OuterRotor')
     PartStruct=changeJMAGDesignerPartName4OuterRotor(PartStruct,app,MachineData);
    end
end