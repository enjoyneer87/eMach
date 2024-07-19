function devdetCoreMagnetRegion(RotorGeomAssembleTable,geoApp)

    DistanceFromCenter=RotorAssemRegionTable.distanceRFromCenter;
    if strcmp(runnerType,"OuterRotor")
            % Max Radius 이면서 면적도 Max인게 나을듯
            %% RotorCore Selection & SetName
            MaxRadiusofRegionList                                           =max(DistanceFromCenter);
            MaxRadiusofRegionListIndex                                      =find(ismember(DistanceFromCenter,MaxRadiusofRegionList))
            RotorCoreRef                                        =RotorAssemRegionTable.ReferenceObj(MaxRadiusofRegionListIndex)
            sel.AddReferenceObject(RotorCoreRef)                ;
            RotorCore=sel.Item(0)                               ;
            if max(RotorAssemRegionTable.Area)-RotorAssemRegionTable.Area(RadiusMaxIndex)<1e-5
            RotorAssemRegionTable.Name{RadiusMaxIndex}          ='RotorCore'
            RotorCore.SetName('RotorCore')                      ;
            HasHousing = 0
            else
            disp('최외각에 존재하지만 면적은 Rotor Region 중에 최대가 아니므로 Housing일수 있으니 메뉴얼하게 이름을 셋팅하세요')
            HasHousing = 1
            
            end
            sel.Clear;
    
            %% Magnet Selection & Magnet SetName
            RotorGeomArcTable    = sortrows(RotorGeomArcTable,          "Radius","descend");   
            RadiusListofRotorGeomArcTable=RotorGeomArcTable.Radius
            RadiusListofRotorGeomArcTable=uniquetol(RadiusListofRotorGeomArcTable,1e-6)
            RadiusListofRotorGeomArcTable=sortrows(RadiusListofRotorGeomArcTable,"descend")
            RadiusListofRotorGeomArcTable(2) %  because 1 is the MaxRadius of RotorCore
            RadiusListofRotorGeomArcTable(3) %  because 1 is the MaxRadius of RotorCore
            CenterRadius =(RadiusListofRotorGeomArcTable(3)+RadiusListofRotorGeomArcTable(2))/2
            CenterAngle  = RotorGeomArcTable.Angle(2)
            [MagPosX,MagPosY]=pol2cart(deg2rad(CenterAngle),CenterRadius)
            geomApp.View().SelectWorldPos(MagPosX, MagPosY,0, 0)
    
            Magnet=sel.Item(0)         
            Magnet.SetName('Magnet')                      ;
             
            MagnetRef=geomDocu.CreateReferenceFromItem(Magnet)
            MagnetId=MagnetRef.GetId;
     
            MagnetIndexInRegionTable=ismember(RotorAssemRegionTable.Id,MagnetId)
            RotorAssemRegionTable.Name{MagnetIndexInRegionTable}='Magnet'
    
         %% [NF] changeRegionNameinGeomNMatTable   
           % Check Has Same Area with Magnet in RegionItemTable
             SimiliarList=difftol(RotorAssemRegionTable.Area,RotorAssemRegionTable.Area(MagnetIndexInRegionTable))         
             SimiliarListIndexList=find(SimiliarList)
             if length(SimiliarListIndexList)>1
                 for similiarRegionIndex=1:length(SimiliarListIndexList)
                    RotorAssemRegionTable.Name{SimiliarListIndexList(similiarRegionIndex)}='Magnet';
                    sel.AddReferenceObject(RotorAssemRegionTable.ReferenceObj(SimiliarListIndexList(similiarRegionIndex)))
                    selItem=sel.Item(0)         
                    selItem.SetName('Magnet')                      ;
                    sel.Clear
                 end
             end
    
           % Air Region
             SimiliarList=difftol(RotorAssemRegionTable.Area,RotorAssemRegionTable.Area(MagnetIndexInRegionTable))         
             SimiliarListIndexList=find(SimiliarList)
             if length(SimiliarListIndexList)>1
                 for similiarRegionIndex=1:length(SimiliarListIndexList)
                    % Matlab Table
                    RotorAssemRegionTable.Name{SimiliarListIndexList(similiarRegionIndex)}='AirRegion';
                    % Geom
                    sel.AddReferenceObject(RotorAssemRegionTable.ReferenceObj(SimiliarListIndexList(similiarRegionIndex)))
                    selItem=sel.Item(0)         
                    selItem.SetName('AirRegion')                      ;
                    sel.Clear
                 end
             end
    
        % for RotorRegionIndex=1:height(RotorAssemRegionTable)
        %     if  ~strcmp(RotorAssemRegionTable.Name(RotorRegionIndex),'RotorCore') 
    
            if  ~strcmp(RotorAssemRegionTable.Name(RotorRegionIndex),'RotorCore') &&abs(RotorAssemRegionTable(partIndex).CentroidTheta-OnePoleAngle/2)<tolerance
                 RotorCoreRef                                        =RotorAssemRegionTable.ReferenceObj(MaxRadiusofRegionListIndex)
                 sel.AddReferenceObject(RotorCoreRef)                ;
                 % Geom
                 Magnet=sel.Item(1);        
                 sel.Count
       
                 Magnet.ItemCheck
                 Magnet.SetName('Magnet')                      ;
                 % Matlab Table
                 RotorAssemRegionTable.Name{RadiusMaxIndex}          ='Magnet'
    
                 sel.Clear
            end
            %
    elseif  contains(runnerType,"InnerRotor")
             setGetGeomRotorNameNTableInnerRotor
    else 
        disp('check Runner Type Inner or Outer')
    end

end