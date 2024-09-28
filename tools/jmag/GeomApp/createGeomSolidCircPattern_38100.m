function createGeomSolidCircPattern(PartName,SolidObj,MachineData,geomApp)

% 
% PartName=AssemTable.AssemItemName{2}
% PartObj =AssemTable.AssemItem(2)

geomDocu=geomApp.GetDocument;
% aRefObj=geomDocu.CreateReferenceFromItem(PartObj);
% BodyName=aRefObj.GetIdentifier;


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
geomApp.GetDocument().GetAssembly().OpenAssembly()
geomApp.GetDocument().GetAssembly().GetItem(PartName).OpenPart()
SolidCircObj=geomApp.GetDocument().GetAssembly().GetItem(PartName).CreateCircularPattern()
    if SolidCircObj.IsValid
    
    % SolidCircObj.SetProperty("Merge", 1)
    SolidCircObj.SetProperty('AxisType', int32(4))
    % SolidCircObj.SetProperty('Solid', [SolidObj{1},SolidObj{2}])
    % if length(SolidObj)>1
    %     for SolidObjIndex=2:length(SolidObj)
    %     SolidCircObj.addproperty('Solid',SolidObj{SolidObjIndex})
    %     end
    % end
    geomSel=geomDocu.GetSelection    
    for IdIndex=1:height(SolidObj)
    refObj=geomDocu.CreateReferenceFromIdentifier(SolidObj{IdIndex})
    geomSel.AddReferenceObject(refObj)
    end
    SolidCircObj.SetProperty('Solid',SolidObj{1})
    SolidCircObj.SetProperty('Solid',SolidObj{1})

    SolidCircObj.SetProperty('Angle', CircAngle)
    SolidCircObj.SetProperty('Instance', int32(NumberInstance))
    % SolidCircObj.SetProperty('Instance', int32(2))
    
    end
end