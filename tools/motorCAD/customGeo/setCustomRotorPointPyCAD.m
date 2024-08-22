function setCustomRotorPointPyCAD(mcad)
    % mcad.InitiateGeometryFromScript()
    mcad.initiate_geometry_from_script
    mcad.set_variable('UseCustomFEARegions_Magnetic',1)
    VMagnet_Layers=mcad.get_variable('VMagnet_Layers').double;
    BandingThickness   =mcad.get_variable('Banding_Thickness');
    mcad.reset_regions
    TotalString4Default     = mcad.get_variable('CustomFEARegions_Magnetic').string;
    magnetTable                 = extractMagnetPositions(TotalString4Default,'Magnet');
    PocketTable                 = extractMagnetPositions(TotalString4Default,'Rotor Pocket');
    

    %% Magnet Table
    % scatter(magnetTable.XPos,magnetTable.YPos)
    % hold on
    
    targetRows = contains(magnetTable.TargetString, 'L1');    
    if any(targetRows)
        % Extract XPos and YPos values for the selected rows
        selectedXPos = magnetTable.XPos(targetRows);
        selectedYPos = magnetTable.YPos(targetRows);        
        % Calculate the mean XPos and YPos values
        L1magXmean = mean(selectedXPos);
        L1magYmean = mean(selectedYPos);
    end
    % scatter(L1magXmean,L1magYmean,'filled','black')   
        
    %% PocketTable Plot
    % Assuming you have the PocketTable generated from previous steps
    xPositions = PocketTable.XPos;
    yPositions = PocketTable.YPos;
    
    % Convert cartesian coordinates to polar coordinates
    [~, rho] = cart2pol(xPositions, yPositions);
    
    % Sort the data by rho values
    [~, sortedIndices] = sort(rho);
    
    % Find the second point (index 2) after sorting
    secondInnerRow = sortedIndices(2);
    % scatter(PocketTable.XPos,PocketTable.YPos)
    % scatter(xPositions(secondInnerRow),yPositions(secondInnerRow),'filled','black')
       
    [~,L1magCenterRho]=cart2pol(L1magXmean,L1magYmean);
    [~,RotorPocketRho]=cart2pol(xPositions(secondInnerRow),yPositions(secondInnerRow));
    
    if  L1magCenterRho<RotorPocketRho
        centerRegionXPoint =L1magXmean;
        centerRegionYPoint =L1magYmean;
    end

    %% Define Custom Rotor Position 
    AddRotorName1='CustomLaminated1';   % shaft 
    AddRotorName2='CustomLaminated2';  % 중간
    AddRotorName3='CustomLaminated3';  % 최외곽

    %% shaft쪽
     numPoles = mcad.get_variable("Pole_Number").double;
    Shaft_Dia=mcad.get_variable('Shaft_Dia');


    [ShaftXposition,ShaftYposition]=pol2cart(deg2rad(360/numPoles/2),Shaft_Dia/2+0.1);
    MatName=mcad.get_variable('Material_Stator_Lam_Back_Iron').string;
    InnerMost=['Type',':4$Name:',AddRotorName1,'$XPos:',num2str(ShaftXposition),'$YPos:',num2str(ShaftYposition),'$MatName:',MatName,'$Colour:8421376$MatType:0$UserAdded:-1'];

    %% 최외곽
    RotorDiameter=mcad.get_variable('RotorDiameter');
    ActualRotor=RotorDiameter-BandingThickness-0.005;
    [OutMostXposition,OutMostYposition]=pol2cart(deg2rad(360/numPoles/2),ActualRotor/2-0.05);
    OutMost=['Type',':4$Name:',AddRotorName3,'$XPos:',num2str(OutMostXposition),'$YPos:',num2str(OutMostYposition),'$MatName:',MatName,'$Colour:8421376$MatType:0$UserAdded:-1'];
    
    %% 합치기
    InnerMost=strjoin(InnerMost);
    OutMost=strjoin(OutMost);
    TotalString4CustomFEA=strcat(InnerMost,';',OutMost);
    % if strcmp(Type,'V')
    if VMagnet_Layers==1
        TotalString4CustomFEA=py.str(TotalString4CustomFEA);
        mcad.set_variable('CustomFEARegions_Magnetic',TotalString4CustomFEA);    
        % mcad.show_mechanical_context()
        % mcad.show_magnetic_context()
        % mcad.display_screen('E-Magnetics;FEA Editor')
    
    % elseif strcmp(Type,'VV')
    elseif VMagnet_Layers==2 
        L2PoleVangle=mcad.get_array_variable('PoleVAngle_Array',int32(1));
        if L2PoleVangle<180
            AddRotorName2='CustomLaminated2';
            CenterLayer=['Type',':4$Name:',AddRotorName2,'$XPos:',num2str(centerRegionXPoint),'$YPos:',num2str(centerRegionYPoint),'$MatName:',MatName,'$Colour:8421376$MatType:0$UserAdded:-1' ] ;      
            CenterLayer=strjoin(CenterLayer);
            TotalString4CustomFEA=strcat(TotalString4CustomFEA,';',CenterLayer);
            TotalString4CustomFEA=py.str(TotalString4CustomFEA);
            mcad.set_variable('CustomFEARegions_Magnetic',TotalString4CustomFEA);
             % mcad.show_mechanical_context()
             % mcad.show_magnetic_context()
             % mcad.display_screen('E-Magnetics;FEA Editor')
        else
            CenterLayer=['Type',':4$Name:',AddRotorName2,'$XPos:',num2str(L1magXmean),'$YPos:',num2str(L1magYmean),'$MatName:',MatName,'$Colour:8421376$MatType:0$UserAdded:-1']  ;      
            CenterLayer=strjoin(CenterLayer);
            TotalString4CustomFEA=strcat(TotalString4CustomFEA,';',CenterLayer);
            TotalString4CustomFEA=py.str(TotalString4CustomFEA);
            mcad.set_variable('CustomFEARegions_Magnetic',TotalString4CustomFEA);
             % mcad.show_mechanical_context()
             % mcad.show_magnetic_context()
             % mcad.display_screen('E-Magnetics;FEA Editor')
        end
    end

end


