function mkDesignerTPSetName(AssemTable)

% Template Parameter Set
for PartIndex=1:height(AssemTable)
    PartName=AssemTable.AssemItemName{PartIndex};
    if strcmp(PartName,'RotorCore')
        PartName='Rotor';
    elseif  strcmp(PartName,'StatorCore')
        PartName='Stator Core';
    elseif strcmp(PartName,'Coil')
        PartName='Coil End';
    elseif strcmp(PartName,'RotorMagnet')
        PartName='Rotor Magnet';
    end
end


%TParameterSetName=% Stator Core , Rotor, Coil End
TParameterSetName=[PartName,' Front Face']                        
TParameterSetName=[PartName,' Back Face']     

% Coil
TParameterSetName=['Coil-Stator Core Face']   
% TParameterSetName=%PartName Stator Core
TParameterSetName=['Stator Gap Face']                          
% TParameterSetName=%PartName Stator Core
TParameterSetName=[PartName,' Side Face']                         
% TParameterSetName=%PartName Rotor
TParameterSetName=[PartName,' Core-Shaft Face']   
            
% Rotor Magnet
TParameterSetName=[PartName,'-Core Face']                   



end