function setCustomRotorPoint(mcad)
    mcad.InitiateGeometryFromScript()
    mcad.SetVariable('UseCustomFEARegions_Magnetic',1)
    [~,VMagnet_Layers]=mcad.GetVariable('VMagnet_Layers');
    [~,BandingThickness]   =mcad.GetVariable('Banding_Thickness');
    mcad.ResetRegions();
    
    [~,TotalString4Default]     =mcad.GetVariable('CustomFEARegions_Magnetic');
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
    [~, numPoles] = mcad.GetVariable("Pole_Number");
    numPoles=double(numPoles);
    [~,Shaft_Dia]=mcad.GetVariable('Shaft_Dia');


    [ShaftXposition,ShaftYposition]=pol2cart(deg2rad(360/numPoles/2),Shaft_Dia/2+0.1);
    [~,MatName]=mcad.GetVariable('Material_Stator_Lam_Back_Iron');
    InnerMost=['Type',':4$Name:',AddRotorName1,'$XPos:',num2str(ShaftXposition),'$YPos:',num2str(ShaftYposition),'$MatName:',MatName,'$Colour:8421376$MatType:0$UserAdded:-1'];

    %% 최외곽
    [~,RotorDiameter]=mcad.GetVariable('RotorDiameter');
    ActualRotor=RotorDiameter-BandingThickness-0.005;
    [OutMostXposition,OutMostYposition]=pol2cart(deg2rad(360/numPoles/2),ActualRotor/2-0.05);
    OutMost=['Type',':4$Name:',AddRotorName3,'$XPos:',num2str(OutMostXposition),'$YPos:',num2str(OutMostYposition),'$MatName:',MatName,'$Colour:8421376$MatType:0$UserAdded:-1'];
    
    %% 합치기
    TotalString4CustomFEA=strcat(InnerMost,';',OutMost);
    % if strcmp(Type,'V')
    if VMagnet_Layers==1
        mcad.SetVariable('CustomFEARegions_Magnetic',TotalString4CustomFEA);    
        mcad.ShowMechanicalContext()
        mcad.ShowMagneticContext()
        mcad.DisplayScreen('E-Magnetics;FEA Editor')
    
    % elseif strcmp(Type,'VV')
    elseif VMagnet_Layers==2 
        [~,L2PoleVangle]=mcad.GetArrayVariable('PoleVAngle_Array',1);
        if L2PoleVangle<180
            AddRotorName2='CustomLaminated2';
            CenterLayer=['Type',':4$Name:',AddRotorName2,'$XPos:',num2str(centerRegionXPoint),'$YPos:',num2str(centerRegionYPoint),'$MatName:',MatName,'$Colour:8421376$MatType:0$UserAdded:-1']  ;      
            TotalString4CustomFEA=strcat(TotalString4CustomFEA,';',CenterLayer);
            mcad.SetVariable('CustomFEARegions_Magnetic',TotalString4CustomFEA);
            mcad.ShowMechanicalContext();
            mcad.ShowMagneticContext();
            mcad.DisplayScreen('E-Magnetics;FEA Editor')
        else

            CenterLayer=['Type',':4$Name:',AddRotorName2,'$XPos:',num2str(L1magXmean),'$YPos:',num2str(L1magYmean),'$MatName:',MatName,'$Colour:8421376$MatType:0$UserAdded:-1']  ;      
            TotalString4CustomFEA=strcat(TotalString4CustomFEA,';',CenterLayer);
            mcad.SetVariable('CustomFEARegions_Magnetic',TotalString4CustomFEA);
            mcad.ShowMechanicalContext();
            mcad.ShowMagneticContext();
            mcad.DisplayScreen('E-Magnetics;FEA Editor')
        end
    end

end


