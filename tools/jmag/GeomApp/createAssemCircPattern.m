function createAssemCircPattern(PartName,PartObj,MachineData,geomApp)

% 
% PartName=AssemTable.AssemItemName{2}
% PartObj =AssemTable.AssemItem(2)

geomDocu=geomApp.GetDocument;
aRefObj=geomDocu.CreateReferenceFromItem(PartObj);
BodyName=aRefObj.GetIdentifier;


%%
    % {'Conductor_'   }
    % {'RotorAir'     }
    % {'Insulation'   }
    % {'StatorCore'   }
    % {'otherSlotArea'}
    % {'RotorCore'    }
    % {'RotorMagnet'  }
%%
%%
if contains(PartName,'Stator','IgnoreCase',true)||contains(PartName,'Coil','IgnoreCase',true)||contains(PartName,'Slot','IgnoreCase',true) ||contains(PartName,'Insulation','IgnoreCase',true)||contains(PartName,'Conductor_','IgnoreCase',true)
        CircAngle = MachineData.StatorOneSlotAngle;
    NumberInstance= MachineData.slots;

elseif contains(PartName,'Magnet','IgnoreCase',true)|| contains(PartName,'Rotor','IgnoreCase',true)
      CircAngle = 360/MachineData.Poles;
    NumberInstance= MachineData.Poles;
   
end

%%
AssemCirObj=geomDocu.GetAssembly().CreateAssemblyCircularPattern();
AssemCirObj.SetProperty('AxisType', int32(4))
AssemCirObj.SetProperty('Target', BodyName)
AssemCirObj.SetProperty('Angle', CircAngle)
AssemCirObj.SetProperty('Instance', int32(NumberInstance))

end