function fieldName=replaceMLABvar2MCADvar(fieldName)
            if contains(fieldName, 'Rear')
                fieldName = strrep(fieldName, 'Rear', '[R]');
            elseif contains(fieldName, 'Front')
                fieldName = strrep(fieldName, 'Front', '[F]');
            elseif contains(fieldName,'Wdg_Area')
                fieldName = strrep(fieldName, 'Wdg_Area', '(Wdg_Area)');
            elseif contains(fieldName,'Slot_Area')
                fieldName = strrep(fieldName, 'Slot_Area', '(Slot_Area)');
            elseif contains(fieldName,'Copper_Depth_percent')
                fieldName = strrep(fieldName, 'Copper_Depth_percent', 'Copper_Depth_[%]');
            else
                fieldName = fieldName;
            end
end