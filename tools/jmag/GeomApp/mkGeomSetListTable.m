function GeomSetListTable = mkGeomSetListTable(PartName,runnerType)

%% Template Parameter Set
    if strcmp(PartName,'RotorCore')
        PartName='Rotor';        
    elseif  strcmp(PartName,'StatorCore')
        PartName='Stator';
    elseif strcmp(PartName,'Coil')
        PartName='Coil';
    elseif strcmp(PartName,'Conductor')
        PartName='Coil';
    elseif contains(PartName,'Magnet','IgnoreCase',true)
        PartName='Rotor Magnet';
    else
        PartName=PartName;
    end

%% Inner Rotor Case[JFT 160]
    if contains(runnerType,'Inner','IgnoreCase',true)
        [SolidGeomSetList,FaceGeomSetList]     =mkGeomSetList4InnerRotor(PartName);
    % RotorAssemRegionTable
%% Outer Rotor SPMSM Case[Wind Turbine]
    elseif  strcmp(runnerType,'OuterRotor')||contains(runnerType,'Outer') ||contains(runnerType,'outer') 
        [SolidGeomSetList,FaceGeomSetList]     =devmkGeomSetList4OuterRotor(PartName);
    end

%% GeomSetList Table 
    GeomSetList    =[SolidGeomSetList'; FaceGeomSetList'];
    GeomSetType    =[repmat({'Solid'},length(SolidGeomSetList),1);repmat({'Face'},length(FaceGeomSetList),1)];
    GeomSetListTable    =cell2table([GeomSetList GeomSetType],"VariableNames",{'GeomSetName','GeomSetType'});
end