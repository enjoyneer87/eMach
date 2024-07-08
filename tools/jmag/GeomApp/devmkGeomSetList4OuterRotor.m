function [SolidGeomSetList,FaceGeomSetList]=devmkGeomSetList4OuterRotor(PartName)
%% Outer Rotor SPMSM Case[Wind Turbine]
             % ST Core & Coil & Rotor Core & Rotor Magnet
    % elseif strcmp(runnerType,'Outer')
    %     % PartName    
    %     [PartName]
    %     [PartName,' Front']
    %     [PartName,' Middle']
    %     [PartName,' Back']
    % 
    %     %% Face
    %     [PartName,' Gap Face']
    %     [PartName,' Side Face']
    %     [PartName,' Front Face']
    %     [PartName,' Back Face']
    % 
    %     % Coil
    %     [PartName,' Front Face']
    %     [PartName,' Back Face']
    % 
    %     % Magnet
    %     [PartName,' Magnet-Core Face']
    %     % Rotor Face
    %     [PartName,' Gap Face']
    %     [PartName,' Front Face']
    %     [PartName,' Back Face']
    %     [PartName,' Core-Shaft Face']
    
         if strcmp(PartName,'Rotor') ||strcmp(PartName,'Stator')   
         % Part ST Core & Coil & Rotor Core & Rotor Magnet
            % [PartName]
            % [PartName,'Front']
            % [PartName,'Middle']
            % [PartName,'Back']
            SolidGeomSetList={[PartName,' Core'] ...
            [PartName,' Core Front']...
            [PartName,' Core Middle']...
            [PartName,' Core Back']...    %% Face
            };
        else 
            SolidGeomSetList={PartName}; ...
        end
    %% FaceGeomSetList  
        if  strcmp(PartName,'Stator') 
            FaceGeomSetList = {...
            [PartName,' Gap Face']...
            [PartName,' Core Front Face']...
            [PartName,' Core Back Face']...
            [PartName,' Core-Shaft Face']...
             'Coil-Stator Core Face'
            };
        elseif strcmp(PartName,'Rotor') 
            FaceGeomSetList={...
            [PartName,' Gap Face']...
            [PartName,' Front Face']...
            [PartName,' Back Face']...
            [PartName,' Core Side Face']...
            };
        elseif strcmp(PartName,'Coil') 
            FaceGeomSetList={...
            [PartName,' End Front Face']...
            [PartName,' End Back Face']...
            };
       elseif contains(PartName,'Conductor') 
            FaceGeomSetList={...
            'Coil End Front Face'...
            'Coil End Back Face'...
            };
        elseif contains(PartName,'Magnet') 
            FaceGeomSetList={...
            [PartName,'-Core Face']
            };
        else
            FaceGeomSetList={...
            [PartName,'-Face']
            };
        end
    
    

end