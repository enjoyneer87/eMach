function PartGeomTable=devmkGeomSetTargetTableByAllocate(PartGeomTable,geomApp)
%% Per Solid & Face
for PartIndex=1:height(PartGeomTable)
    %% 전체 Solid
    CurPartTable                    =PartGeomTable(PartIndex,:);
    CurPartRef_IdentifierName       =CurPartTable.RefObjListTable{:}.IdentifierName;
    BoolLump                        =contains(CurPartRef_IdentifierName,'lump','IgnoreCase',true);
    LumpSolidIds                    =CurPartRef_IdentifierName(BoolLump);
    %% Non FaceExtrude (Middle)
    BoolFaceExtrude                    =contains(LumpSolidIds,'FaceExtrude','IgnoreCase',true);
    LumpMiddleSolid_Ids                =LumpSolidIds(~BoolFaceExtrude);
    %% FaceExtruded Solid (Upside or DownSide) (Front, Back) > Ge
    FaceExtrude_PartIdRef              =LumpSolidIds(BoolFaceExtrude);
    % Back FaceExtruded
    BackfacesCell                      =CurPartTable.FaceExtrudeCells.BackfacesCell;
    BoolFaceExtrude                    =contains(BackfacesCell,'FaceExtrude','IgnoreCase',true);
    BackfacesCell                      =BackfacesCell(BoolFaceExtrude);
    % Front FaceExtruded
    FrontfaceCell                      =CurPartTable.FaceExtrudeCells.FrontfaceCell;
    BoolFaceExtrude                    =contains(FrontfaceCell,'FaceExtrude','IgnoreCase',true);
    FrontfaceCell                      =FrontfaceCell(BoolFaceExtrude);
    %% Back FaceExtrudeSolidCells
    splitedBackfaceCell                 = cellfun(@(x) strsplit(x, '+'), BackfacesCell, 'UniformOutput', false);
    FaceExtrudeSolidCells               = extractSplitedFirstCells(splitedBackfaceCell);
    FaceExtrudeSolidCells               = unique(FaceExtrudeSolidCells);
    if isscalar(FaceExtrudeSolidCells)
    % FaceExtrude는 하나
    BacktSolid_Id                       = FaceExtrudeSolidCells{:};
    BacktSolid_Id                       = strsplit(BacktSolid_Id,'(');
    BacktSolid_Id                       = BacktSolid_Id{end};   
    %% Lump Face Extrude Id (FaceExtrude는 하나고 여기에 여러개의 Face라서 Lump 여러개)
    Bool_LumpBackSolid_Ids              = contains(LumpSolidIds,BacktSolid_Id,"IgnoreCase",true);
    LumpBackSolid_Ids                   = LumpSolidIds(Bool_LumpBackSolid_Ids)                 ;
    else 
    disp('down FaceExtrude가 여러개입니다. FaceExtrude는 하나고 여기에 여러개의 Face가 포함되어있어야합니다')
    end
    %% Front FaceExtrudeSolidCells
    splitedFrontfaceCell                = cellfun(@(x) strsplit(x, '+'), FrontfaceCell, 'UniformOutput', false);
    FaceExtrudeSolidCells               = extractSplitedFirstCells(splitedFrontfaceCell);
    % FaceExtrude는 하나
    BoolBackSolid                       = contains(FaceExtrudeSolidCells,BacktSolid_Id,"IgnoreCase",true);
    FaceExtrudeSolidCells               = FaceExtrudeSolidCells(~BoolBackSolid);
    FaceExtrudeSolidCells               = unique(FaceExtrudeSolidCells);
    if isscalar(FaceExtrudeSolidCells)
    % FaceExtrude는 하나
    FrontSolid_Id                       = FaceExtrudeSolidCells{:};
    FrontSolid_Id                       = strsplit(FrontSolid_Id,'(');
    FrontSolid_Id                       = FrontSolid_Id{end};
    %% Lump Face Extrude Id (FaceExtrude는 하나고 여기에 여러개의 Face라서 Lump 여러개)
    Bool_LumpFrontSolid_Ids             = contains(LumpSolidIds,FrontSolid_Id,"IgnoreCase",true);
    LumpFrontSolid_Ids                  = LumpSolidIds(Bool_LumpFrontSolid_Ids)                 ;
    else 
    disp('upside FaceExtrude가 여러개입니다. FaceExtrude는 하나고 여기에 여러개의 Face가 포함되어있어야합니다')
    end
    %% [WIP]Face
    % Whole Face (Periodic)
    % ['Stator,' Gap Face']...
    PartIndex=3
    CurPartTable                    =PartGeomTable(PartIndex,:);
    CurPartTable.RefObjListTable
        % 
    % 'Coil-Stator Core Face'
        % Intersect
    % ['Rotor,' Gap Face']...
    % ['Rotor',' Core-Shaft Face']...
    % ['Magnet','-Core Face']

    % % single Face
    % [PartName,' Core Side Face']...
    % [PartName,' Core Front Face']...
    % [PartName,' Core Back Face']...
    % rotor
    %     [PartName,' Front Face']...
    % [PartName,' Back Face']...
    % Coil
    % [PartName,' End Front Face']...
    % [PartName,' End Back Face']...


    % Single Face
%% 2 TargetStruct
    SolidTargetStruct                            =struct();
    SolidTargetStruct.LumpSolidIds               =LumpSolidIds            ; 
    SolidTargetStruct.LumpMiddleSolid_Ids        =LumpMiddleSolid_Ids     ;     
    SolidTargetStruct.LumpFrontSolid_Ids         =LumpFrontSolid_Ids      ;         
    SolidTargetStruct.LumpBackSolid_Ids          =LumpBackSolid_Ids       ;         
%% 2 Table
    PartGeomTable.SolidTargetStruct(PartIndex)   =SolidTargetStruct;
end



%% Allocate SolidGeom
    % Get Solid Per PartName
for PartIndex=1:height(PartGeomTable)
    SolidTargetStruct       = PartGeomTable.SolidTargetStruct(PartIndex);
    GeomSetListTable        = PartGeomTable.GeomSetListTable{PartIndex};
    BoolSolid               =  contains(GeomSetListTable.GeomSetType,'Solid','IgnoreCase',true)    ; 
    BoolFrontIndex          =  contains(GeomSetListTable.GeomSetName,'front','IgnoreCase',true)    ;     
    BoolBackIndex           =  contains(GeomSetListTable.GeomSetName,'back','IgnoreCase',true)     ;     
    BoolMiddleIndex         =  contains(GeomSetListTable.GeomSetName,'middle','IgnoreCase',true)   ;         
    %% Solid Target Allocation
    BoolWholePart               = ~BoolBackIndex & ~BoolFrontIndex & ~BoolMiddleIndex & BoolSolid;
    GeomSetListTable.Target(BoolWholePart)                        = {SolidTargetStruct.LumpSolidIds}           ; 
    GeomSetListTable.Target(BoolFrontIndex&BoolSolid)             = {SolidTargetStruct.LumpBackSolid_Ids   }   ;     
    GeomSetListTable.Target(BoolBackIndex&BoolSolid)              = {SolidTargetStruct.LumpFrontSolid_Ids  }   ;     
    GeomSetListTable.Target(BoolMiddleIndex&BoolSolid)            = {SolidTargetStruct.LumpMiddleSolid_Ids }   ;
    %% [TB]Face Target Allocation
    PartGeomTable.GeomSetListTable{PartIndex} = GeomSetListTable       ;
end
    % Upside - refObj or Extrude Obj? or Item

%% Allocate FaceGeom
    % Get Face Per PartName

        %% 
    % FaceExtrude (Upside or DownSide) (Front, Back)
    FaceExtrudeSolidRef_IdName          =CurPartRef_IdentifierName(BoolFaceExtrude);
    BoolRadialPattern                   =contains(FaceExtrudeSolidRef_IdName,'RadialPattern','IgnoreCase',true);
    FaceExtrude_OriginSolidRef_IdName   =FaceExtrudeSolidRef_IdName(~BoolRadialPattern);
    %% FaceExtrude 할때 Face위치를 분류 해놓을것 PartGeomTable에다가, 아님 IdName에 할것
    splitedIdName           =strsplit(FaceExtrude_OriginSolidRef_IdName{1},'+');
    ExtrudedFace            =[splitedIdName{3},')']; 
    length(FaceExtrude_OriginSolidRef_IdName)
    refObj                  =geomDocu.CreateReferenceFromIdentifier(ExtrudedFace);
    geomMeasure             =geomDocu.GetMeasureManager
    geomMeasure.MeasureDistanceFrom(0,0,0,refObj)
    %% 개별 객체는(Solid)는 인식안되고 FaceExtrude 객체를 선택해야됨 sel
    curRefObjTalbe=PartGeomTable.AssemRefObTable{CurPartIndex}(find(contains(CurPartRef_IdentifierName,FaceExtrude_OriginSolidRef_IdName{2})),:);
    % sel=mkSelectionObj(geomApp)
    geomApp.Show
    % sel.AddReferenceObject(curRefObjTalbe.ReferenceObj)
    % sel.CountReferenceObject
end