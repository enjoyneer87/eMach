function dxf = filterEntitiesByAngle(entitiesStruct, max_angle)
    %% Test
    % entitiesStruct=entitiesRotorStruct
    % max_angle=22.5
    % Initialize the filtered entities array
    filtered_entities = struct('name', {}, 'layer', {}, 'linetype', {}, 'color', {}, 'arc', {}, 'line', {});


    %% global Min &Max Arc
    entitiesStruct=entitiesStruct';
    entitiesTable=struct2table(entitiesStruct);
    
    % Filter rows where the arc field is not empty
    arcEntities = entitiesTable.arc(~cellfun(@isempty, entitiesTable.arc), :);
    thirdValues = cellfun(@(x) x(3), arcEntities);
    minRadius=min(thirdValues);
    maxRadius=max(thirdValues);
    
    %% add edge Line
    if contains(entitiesTable.layer{1},'Stator','IgnoreCase',true)
    LayerName='Stator';
    NewTable = entitiesTable([], :);
    NewTable.name(end+1)={'LINE'};
    NewTable.layer(end)={LayerName};
    NewTable.line(end)={[minRadius 0 maxRadius 0]};

    NewTable.name(end+1)={'LINE'};
    NewTable.layer(end)={LayerName};
    [BoundxMin,BoundyMin]=pol2cart(deg2rad(max_angle),minRadius);
    [BoundxMax,BoundyMax]=pol2cart(deg2rad(max_angle),maxRadius);

    NewTable.line(end)={[BoundxMin BoundyMin BoundxMax BoundyMax]};
    else % rotor
    LayerName=   entitiesTable.layer(1); 
    NewTable = entitiesTable([], :);
    NewTable.name(end+1)={'LINE'};
    NewTable.layer(end)={LayerName};
    NewTable.line(end)={[0 0 maxRadius 0]};

    NewTable.name(end+1)={'LINE'};
    NewTable.layer(end)={LayerName};
    [BoundxMin,BoundyMin]=pol2cart(deg2rad(max_angle),0);
    [BoundxMax,BoundyMax]=pol2cart(deg2rad(max_angle),maxRadius);

    NewTable.line(end)={[BoundxMin BoundyMin BoundxMax BoundyMax]};

    end


    %%  Filter Arc & Line
    % Filter rows where the arc field is not empty
    arcTable = entitiesTable(~cellfun(@isempty, entitiesTable.arc), :);

    %% Rotor 일때 절반   
    if contains(entitiesTable.layer{1},'Rotor','IgnoreCase',true)
        % 원점이 (0,0)인 행들을 찾는 코드
        origin_x = 0;
        origin_y = 0;
        % 주기성을 계산합니다.
        % LCMMotor=lcm(8,48);
        % periodicitySlots = LCMMotor / poles;
        % PeriodicAngle=360/LCMMotor*periodicitySlots;
        PeriodicAngle=max_angle*2;
        % 논리형 배열을 생성하여 원점이 (0,0)인 행들을 찾기
        is_ShapeArc  = cellfun(@(arc) arc(1) == origin_x && arc(2) == origin_y && arc(5) ==PeriodicAngle , arcTable.arc);
        
        new_angle = PeriodicAngle / 2;
        for i = 1:height(arcTable)
            if is_ShapeArc(i)
                arc = arcTable.arc{i};
                arc(5) = new_angle;
                arcTable.arc{i} = arc;
            end
        end
    end
    %% Filter rows where the line field is not empty
    lineTable = entitiesTable(~cellfun(@isempty, entitiesTable.line), :);


    %% Filter the lineTable to keep only the lines within the angle range
    for i = 1:height(lineTable)
        % Get the line coordinates
        Xi = lineTable.line{i}(1);
        Yi = lineTable.line{i}(2);
        Xj = lineTable.line{i}(3);
        Yj = lineTable.line{i}(4);

        % Convert the line coordinates to radial and theta
        [angle1, ~] = cart2pol(Xi, Yi);
        [angle2, ~] = cart2pol(Xj, Yj);

        % Convert angles from radians to degrees
        angle1 = rad2deg(angle1);
        angle2 = rad2deg(angle2);

        % Check if both angles are within the allowed range
        if (angle1 >= 0 && angle1 <= max_angle) && (angle2 >= 0 && angle2 <= max_angle)
            is_within_angle(i) = true;
        end
    end

    filtered_lineTable = lineTable(is_within_angle, :);
    
    %% Filter the arcTable to keep only the arcs within the angle range

    is_within_angle = false(height(arcTable), 1);

    for i = 1:height(arcTable)
        % Get the arc angles
        [PosX,PosY]=PosArc(arcTable.arc{i});
        [theta,rho]=cart2pol(PosX,PosY);
        angle=rad2deg(theta);
        angle1 = arcTable.arc{i}(4);
        angle2 = arcTable.arc{i}(5);
        if arcTable.arc{i}(1)==0 && arcTable.arc{i}(2)==0
            % Check if both angles are within the allowed range
            if (angle1 >= 0 && angle1 <= max_angle) && (angle2 >= 0 && angle2 <= max_angle)
                is_within_angle(i) = true;
            end
        else
            if all(angle>=0) && all(angle <=max_angle)
                is_within_angle(i) = true;
            end
        end
    end
    filtered_arcTable = arcTable(is_within_angle, :);

    %% Stator Arc
    if contains(entitiesTable.layer{1},'Stator','IgnoreCase',true)
    radii = cellfun(@(x) x(3), filtered_arcTable.arc);
    to_keep = ~(radii == minRadius);
    filtered_arcTable = filtered_arcTable(to_keep, :);
    radii = cellfun(@(x) x(3), filtered_arcTable.arc);
    to_keep = ~(radii == maxRadius);
    filtered_arcTable = filtered_arcTable(to_keep, :);

    NewArcTable = arcTable([], :);

    NewArcTable.name(end+1)={'ARC'};
    NewArcTable.layer(end)={'Stator'};
    NewArcTable.arc(end)={[0 0 minRadius 0 45]};

    NewArcTable.name(end+1)={'ARC'};
    NewArcTable.layer(end)={'Stator'};
    NewArcTable.arc(end)={[0 0 maxRadius 0 45]};
    entitiesTable=[filtered_arcTable;filtered_lineTable;NewArcTable;NewTable];
    else % rotor
    entitiesTable=[filtered_arcTable;filtered_lineTable;NewTable];
    end
    %% 
    filtered_entities=table2struct(entitiesTable);

    dxf.divisions=50;
    dxf.entities=filtered_entities;
end
