function getEdgeItemFromString(testString)

    
 testString= 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionItem305+TSketchLine303)))))'
 % 'edge(TFaceExtrudeSolid346+edge(TFaceExtrudeSolid346+edge(TExtrudeSolid344+edge(TExtrudeSolid344+edge(TRegionFillet340+++face(TRegionItem332))))))'
% 
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionFillet297+++face(TRegionItem305))))))'
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionFillet298+++face(TRegionItem305))))))'


% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionItem305+TSketchArc289)))))'
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionItem305+TSketchArc290)))))'
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionItem305+TSketchArc291)))))'
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionItem305+TSketchLine288)))))'
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionItem305+TSketchLine303)))))'


% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TSolidMirrorPattern307+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionFillet297+++face(TRegionItem305))))_2)))'
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TSolidMirrorPattern307+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionFillet298+++face(TRegionItem305))))_2)))'
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TSolidMirrorPattern307+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionItem305+TSketchArc291)))_2)))'
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TSolidMirrorPattern307+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionItem305+TSketchLine288)))_2)))'
% 'edge(TFaceExtrudeSolid308+edge(TFaceExtrudeSolid308+edge(TSolidMirrorPattern307+edge(TExtrudeSolid306+edge(TExtrudeSolid306+edge(TRegionItem305+TSketchLine303)))_2)))'



% geomApp.GetDocument().GetAssembly().GetItem(u"StatorCore").GetItem(u"Turn into 1 Period Model from Half Period Model").SetProperty(u"SymmetryType", 0)
% refarray = [0 for i in range(1)]
% refarray[0] = u"lump(TExtrudeSolid306+face(TExtrudeSolid306+face(TRegionItem305)))"
% geomApp.GetDocument().GetAssembly().GetItem(u"StatorCore").GetItem(u"Turn into 1 Period Model from Half Period Model").SetProperty(u"Solid", refarray)
geomApp.Show
SolidName='TFaceExtrudeSolid306'
RegionItemName='TRegionItem305'

testString = ['lump(',SolidName,'+','face(',SolidName,'+face(',RegionItemName,')))']


    delimiters = {'+', ')', '('};

    parts = strsplit(testString, delimiters)';
   refarray[0] = u"lump(TFaceExtrudeSolid308+lump(TExtrudeSolid306+face(TExtrudeSolid306+face(TRegionItem305))))"

refarray = "lump(TExtrudeSolid306+face(TExtrudeSolid306+face(TRegionItem305)))"

%% mk RefObj
    SolidOrigin=geomDocu.CreateReferenceFromIdentifier(testString)
%% mk GeomSelection 
    sel.AddReferenceObject(SolidOrigin)
    sel.CountReferenceObject
    a=sel.GetReferenceObject(0)
    
end

geomApp.GetDocument().GetAssembly().CreateSolidRegionSet()
refarray = [0 for i in range(1)]
refarray[0] = u"lump(TExtrudeSolid306+face(TExtrudeSolid306+face(TRegionItem305)))"
geomApp.GetDocument().GetAssembly().GetGeometrySet(u"Solid/Region Set.3").SetProperty(u"Targets", refarray)

%% Solid는 무조건
% face(TExtrudeSolid306+face(TRegionItem305)
% % face->edge -> 포함 edgeItem
% edge(TExtrudeSolid306+edge(TRegionItem305+TSketchArc289)))
% edge(TExtrudeSolid306+edge(TRegionItem305+TSketchArc290)))
% edge(TExtrudeSolid306+edge(TRegionItem305+TSketchArc291)))
% edge(TExtrudeSolid306+edge(TRegionItem305+TSketchLine288))
% edge(TExtrudeSolid306+edge(TRegionItem305+TSketchLine303))

geomApp