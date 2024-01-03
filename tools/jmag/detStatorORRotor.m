function itemName=detStatorORRotor(uniqueRegionNameCell)

    if    any(contains(uniqueRegionNameCell,'Stator'))
       itemName='Stator';
    elseif any(contains(uniqueRegionNameCell,'Rotor'))
       itemName='Rotor';
    end
end