# Python Script, API Version = V23
# Discovery Python script
# Created by Motor-CAD v2025.2.2 at 04/12/2025 ¿ÀÈÄ 9:41:16
# Motor-CAD file: E:\KDH\KJS\251114_C67_test_Moa.mot

class PartType:
   RADIAL = 1
   AXIAL_CIRCULAR = 2

# Geometry utility functions
def GetPoint(aX, aY):
   return Point2D.Create(MM(aX), MM(aY))

def AddCircle(aCentre_X, aCentre_Y, aRadius):
   origin = GetPoint(aCentre_X, aCentre_Y)
   result = SketchCircle.Create(origin, MM(aRadius))

# XY plane procedures
# Sketch Lines
def ClosePolyLine_Line_XY(startPoint, endPoint, ArcReplacement = False):
   global ArcReplacementCount, LineFailureCount
   result = SketchLine.Create(startPoint, endPoint)
   if result.Success == True:
      if ArcReplacement:
         # Failed Arc drawing has been successfully replace by a Line
         ArcReplacementCount = ArcReplacementCount + 1
      endPoint = result.CreatedCurves[0].Shape.EndPoint
      return GetPoint(endPoint.X * 1000, endPoint.Y * 1000)
   else:
      # Line drawing has failed. Return startPoint as endPoint
      if ArcReplacement == False:
         LineFailureCount = LineFailureCount + 1
      return startPoint

def AddPolyLine_Line_XY(startPoint, end_X, end_Y):
   end = GetPoint(end_X, end_Y)
   return ClosePolyLine_Line_XY(startPoint, end)

# Sketch Curves
def ClosePolyLine_Arc_XY(startPoint, mid_X, mid_Y, endPoint):
   global ArcFailureCount
   midPoint = GetPoint(mid_X, mid_Y)
   result = SketchArc.Create3PointArc(startPoint, endPoint, midPoint)
   if result.Success == True:
      endPoint = result.CreatedCurves[0].Shape.EndPoint
      return GetPoint(endPoint.X * 1000, endPoint.Y * 1000)
   else:
      # Arc drawing has failed. Attempt to replace with straight line
      ArcFailureCount = ArcFailureCount + 1
      return ClosePolyLine_Line_XY(startPoint, endPoint, True)

def AddPolyLine_Arc_XY(startPoint, mid_X, mid_Y, end_X, end_Y):
   end = GetPoint(end_X, end_Y)
   return  ClosePolyLine_Arc_XY(startPoint, mid_X, mid_Y, end)

# YZ plane procedures
# Sketch Lines
def ClosePolyLine_Line_YZ(startPoint, endPoint, ArcReplacement = False):
   global ArcReplacementCount, LineFailureCount
   result = SketchLine.Create(startPoint, endPoint)
   if result.Success == True:
      if ArcReplacement:
         # Failed Arc drawing has been successfully replace by a Line
         ArcReplacementCount = ArcReplacementCount + 1
      endPoint = result.CreatedCurves[0].Shape.EndPoint
      return GetPoint(endPoint.Y * 1000, endPoint.Z * 1000)
   else:
      # Line drawing has failed. Return startPoint as endPoint
      if ArcReplacement == False:
         LineFailureCount = LineFailureCount + 1
      return startPoint

def AddPolyLine_Line_YZ(startPoint, end_X, end_Y):
   end = GetPoint(end_X, end_Y)
   return ClosePolyLine_Line_YZ(startPoint, end)

# Sketch Curves
def ClosePolyLine_Arc_YZ(startPoint, mid_X, mid_Y, endPoint):
   global ArcFailureCount
   midPoint = GetPoint(mid_X, mid_Y)
   result = SketchArc.Create3PointArc(startPoint, endPoint, midPoint)
   if result.Success == True:
      endPoint = result.CreatedCurves[0].Shape.EndPoint
      return GetPoint(endPoint.Y * 1000, endPoint.Z * 1000)
   else:
      # Arc drawing has failed. Attempt to replace with straight line
      ArcFailureCount = ArcFailureCount + 1
      return ClosePolyLine_Line_YZ(startPoint, endPoint, True)

def AddPolyLine_Arc_YZ(startPoint, mid_X, mid_Y, end_X, end_Y):
   end = GetPoint(end_X, end_Y)
   return  ClosePolyLine_Arc_YZ(startPoint, mid_X, mid_Y, end)

# Create Component
def CreateNamedComponent(aName):
   selection = PartSelection.Create(GetRootPart())
   result = ComponentHelper.CreateNewComponent(selection, None)
   result.CreatedComponents[0].SetName(aName)
   return result.CreatedComponents[0]

def CreateNamedComponentWithColour_Radial(aName, aAxialPosition, aAxialLength, aR, aG, aB, aParentComponent = None):
   result = CreateNamedComponent(aName)
   compLookupList.append((result, aR, aG, aB, PartType.RADIAL, aAxialLength, aParentComponent))
   ViewHelper.SetSketchPlane(Plane.PlaneXY, None)
   ViewHelper.TransformSectionPlaneAlongAxis(HandleAxis.Z, MM(aAxialPosition))
   return result

def CreateNamedCylinderComponent(aName, aX, aY, aRadius_Outer, aRadius_Inner, \
                                 aAxialPosition, aAxialLength, aR, aG, aB, aParentComponent = None):
   result = CreateNamedComponentWithColour_Radial(aName, aAxialPosition, aAxialLength, aR, aG, aB, aParentComponent)
   AddCircle(aX, aY, aRadius_Outer)
   if aRadius_Inner > 0:
      AddCircle(aX, aY, aRadius_Inner)
   return result

def CreateNamedComponentWithColour_Axial(aName, aR, aG, aB, aParentComponent = None):
   result = CreateNamedComponent(aName)
   compLookupList.append((result, aR, aG, aB, PartType.AXIAL_CIRCULAR, 0, aParentComponent))
   ViewHelper.SetSketchPlane(Plane.PlaneYZ, None)
   return result


# Prepare and Move Component procedures
def PrepareSolidsAndContainers(aComponentGroup):
   delList = list(())
   for subComponent in aComponentGroup.Components:
      if subComponent.Content.Bodies.Count == 1:
         bodySelection = BodySelection.Create(subComponent.Content.Bodies[0])
         # rename the solid to its container name and move it to the root of the component group
         renameResult = RenameObject.Execute(bodySelection, subComponent.GetName())
         moveResult = ComponentHelper.MoveBodiesToComponent(bodySelection, aComponentGroup, False, None)

      # add  the old individual component container including any stray geometry
      # left over from solidification to the local delete list
      delList.append(subComponent)
   result = Delete.Execute(ComponentSelection.Create(delList))

def MoveComponent(aComponents, aNewParent):
   selections = ComponentSelection.Create(aComponents)
   parentSelection =  ComponentSelection.Create(aNewParent)
   result = ComponentHelper.MoveBodiesToComponent(selections, parentSelection, False, None)
   PrepareSolidsAndContainers(aNewParent)

# Counters for failed function calls
ArcReplacementCount = 0
ArcFailureCount = 0
LineFailureCount = 0
InitialStatusMessageCount = ApplicationHelper.StatusHistory.Count
# End of geometry utility functions

# Look up list for components
compLookupList = list(())

# Index constants for look up list tuples
kComponent = 0
kColour_R = 1
kColour_G = 2
kColour_B = 3
kPartType = 4
kAxialLength = 5
kGroup = 6

# Major Components
comp_Housing = CreateNamedComponent("Housing")
comp_Stator = CreateNamedComponent("Stator")
comp_Rotor = CreateNamedComponent("Rotor")

# Start of geometry section

# Create new component housing_active
newComp = CreateNamedComponentWithColour_Radial("housing_active", -54.5, -96, 0, 16, 240, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(-140, 0)
plNext = AddPolyLine_Arc_XY(plStart, -139.700249, -9.156438, -138.802281, -18.273667)
plNext = AddPolyLine_Arc_XY(plNext, -137.309939, -27.312645, -135.229616, -36.234666)
plNext = AddPolyLine_Arc_XY(plNext, -132.570218, -45.001525, -129.343135, -53.575681)
plNext = AddPolyLine_Arc_XY(plNext, -125.562184, -61.920417, -121.243557, -70)
plNext = AddPolyLine_Arc_XY(plNext, -116.405746, -77.779833, -111.069468, -85.2266)
plNext = AddPolyLine_Arc_XY(plNext, -105.257573, -92.308414, -98.994949, -98.994949)
plNext = AddPolyLine_Arc_XY(plNext, -92.308414, -105.257573, -85.2266, -111.069468)
plNext = AddPolyLine_Arc_XY(plNext, -77.779833, -116.405746, -70, -121.243557)
plNext = AddPolyLine_Arc_XY(plNext, -61.920417, -125.562184, -53.575681, -129.343135)
plNext = AddPolyLine_Arc_XY(plNext, -45.001525, -132.570218, -36.234666, -135.229616)
plNext = AddPolyLine_Arc_XY(plNext, -27.312645, -137.309939, -18.273667, -138.802281)
plNext = AddPolyLine_Arc_XY(plNext, -9.156438, -139.700249, 0, -140)
plNext = AddPolyLine_Arc_XY(plNext, 9.156438, -139.700249, 18.273667, -138.802281)
plNext = AddPolyLine_Arc_XY(plNext, 27.312645, -137.309939, 36.234666, -135.229616)
plNext = AddPolyLine_Arc_XY(plNext, 45.001525, -132.570218, 53.575681, -129.343135)
plNext = AddPolyLine_Arc_XY(plNext, 61.920417, -125.562184, 70, -121.243557)
plNext = AddPolyLine_Arc_XY(plNext, 77.779833, -116.405746, 85.2266, -111.069468)
plNext = AddPolyLine_Arc_XY(plNext, 92.308414, -105.257573, 98.994949, -98.994949)
plNext = AddPolyLine_Arc_XY(plNext, 105.257573, -92.308414, 111.069468, -85.2266)
plNext = AddPolyLine_Arc_XY(plNext, 116.405746, -77.779833, 121.243557, -70)
plNext = AddPolyLine_Arc_XY(plNext, 125.562184, -61.920417, 129.343135, -53.575681)
plNext = AddPolyLine_Arc_XY(plNext, 132.570218, -45.001525, 135.229616, -36.234666)
plNext = AddPolyLine_Arc_XY(plNext, 137.309939, -27.312645, 138.802281, -18.273667)
plNext = AddPolyLine_Arc_XY(plNext, 139.700249, -9.156438, 140, 0)
plNext = AddPolyLine_Arc_XY(plNext, 139.700249, 9.156438, 138.802281, 18.273667)
plNext = AddPolyLine_Arc_XY(plNext, 137.309939, 27.312645, 135.229616, 36.234666)
plNext = AddPolyLine_Arc_XY(plNext, 132.570218, 45.001525, 129.343135, 53.575681)
plNext = AddPolyLine_Arc_XY(plNext, 125.562184, 61.920417, 121.243557, 70)
plNext = AddPolyLine_Arc_XY(plNext, 116.405746, 77.779833, 111.069468, 85.2266)
plNext = AddPolyLine_Arc_XY(plNext, 105.257573, 92.308414, 98.994949, 98.994949)
plNext = AddPolyLine_Arc_XY(plNext, 92.308414, 105.257573, 85.2266, 111.069468)
plNext = AddPolyLine_Arc_XY(plNext, 77.779833, 116.405746, 70, 121.243557)
plNext = AddPolyLine_Arc_XY(plNext, 61.920417, 125.562184, 53.575681, 129.343135)
plNext = AddPolyLine_Arc_XY(plNext, 45.001525, 132.570218, 36.234666, 135.229616)
plNext = AddPolyLine_Arc_XY(plNext, 27.312645, 137.309939, 18.273667, 138.802281)
plNext = AddPolyLine_Arc_XY(plNext, 9.156438, 139.700249, 0, 140)
plNext = AddPolyLine_Arc_XY(plNext, -9.156438, 139.700249, -18.273667, 138.802281)
plNext = AddPolyLine_Arc_XY(plNext, -27.312645, 137.309939, -36.234666, 135.229616)
plNext = AddPolyLine_Arc_XY(plNext, -45.001525, 132.570218, -53.575681, 129.343135)
plNext = AddPolyLine_Arc_XY(plNext, -61.920417, 125.562184, -70, 121.243557)
plNext = AddPolyLine_Arc_XY(plNext, -77.779833, 116.405746, -85.2266, 111.069468)
plNext = AddPolyLine_Arc_XY(plNext, -92.308414, 105.257573, -98.994949, 98.994949)
plNext = AddPolyLine_Arc_XY(plNext, -105.257573, 92.308414, -111.069468, 85.2266)
plNext = AddPolyLine_Arc_XY(plNext, -116.405746, 77.779833, -121.243557, 70)
plNext = AddPolyLine_Arc_XY(plNext, -125.562184, 61.920417, -129.343135, 53.575681)
plNext = AddPolyLine_Arc_XY(plNext, -132.570218, 45.001525, -135.229616, 36.234666)
plNext = AddPolyLine_Arc_XY(plNext, -137.309939, 27.312645, -138.802281, 18.273667)
ClosePolyLine_Arc_XY(plNext, -139.700249, 9.156438, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(139, 0)
plNext = AddPolyLine_Arc_XY(plStart, 138.70239, 9.091035, 137.810836, 18.143141)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, 27.117555, 134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, 44.680086, 128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, 61.478128, 120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, 77.224262, 110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, 91.649068, 98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, 104.505733, 84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, 115.574276, 69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, 124.665311, 53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, 131.623288, 35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, 136.329154, 18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, 138.70239, 0, 139)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, 138.70239, -18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, 136.329154, -35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, 131.623288, -53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, 124.665311, -69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, 115.574276, -84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, 104.505733, -98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, 91.649068, -110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, 77.224262, -120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, 61.478128, -128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, 44.680086, -134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, 27.117555, -137.810836, 18.143141)
plNext = AddPolyLine_Arc_XY(plNext, -138.70239, 9.091035, -139, 0)
plNext = AddPolyLine_Arc_XY(plNext, -138.70239, -9.091035, -137.810836, -18.143141)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, -27.117555, -134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, -44.680086, -128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, -61.478128, -120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, -77.224262, -110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, -91.649068, -98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, -104.505733, -84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, -115.574276, -69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, -124.665311, -53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, -131.623288, -35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, -136.329154, -18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, -138.70239, 0, -139)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, -138.70239, 18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, -136.329154, 35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, -131.623288, 53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, -124.665311, 69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, -115.574276, 84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, -104.505733, 98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, -91.649068, 110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, -77.224262, 120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, -61.478128, 128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, -44.680086, 134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, -27.117555, 137.810836, -18.143141)
ClosePolyLine_Arc_XY(plNext, 138.70239, -9.091035, plStart)
# End of Outline 2 PolyLine

# End of component housing_active


# Create new component housing_front
newComp = CreateNamedComponentWithColour_Radial("housing_front", -26.5, -28, 0, 16, 240, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(-140, 0)
plNext = AddPolyLine_Arc_XY(plStart, -139.700249, -9.156438, -138.802281, -18.273667)
plNext = AddPolyLine_Arc_XY(plNext, -137.309939, -27.312645, -135.229616, -36.234666)
plNext = AddPolyLine_Arc_XY(plNext, -132.570218, -45.001525, -129.343135, -53.575681)
plNext = AddPolyLine_Arc_XY(plNext, -125.562184, -61.920417, -121.243557, -70)
plNext = AddPolyLine_Arc_XY(plNext, -116.405746, -77.779833, -111.069468, -85.2266)
plNext = AddPolyLine_Arc_XY(plNext, -105.257573, -92.308414, -98.994949, -98.994949)
plNext = AddPolyLine_Arc_XY(plNext, -92.308414, -105.257573, -85.2266, -111.069468)
plNext = AddPolyLine_Arc_XY(plNext, -77.779833, -116.405746, -70, -121.243557)
plNext = AddPolyLine_Arc_XY(plNext, -61.920417, -125.562184, -53.575681, -129.343135)
plNext = AddPolyLine_Arc_XY(plNext, -45.001525, -132.570218, -36.234666, -135.229616)
plNext = AddPolyLine_Arc_XY(plNext, -27.312645, -137.309939, -18.273667, -138.802281)
plNext = AddPolyLine_Arc_XY(plNext, -9.156438, -139.700249, 0, -140)
plNext = AddPolyLine_Arc_XY(plNext, 9.156438, -139.700249, 18.273667, -138.802281)
plNext = AddPolyLine_Arc_XY(plNext, 27.312645, -137.309939, 36.234666, -135.229616)
plNext = AddPolyLine_Arc_XY(plNext, 45.001525, -132.570218, 53.575681, -129.343135)
plNext = AddPolyLine_Arc_XY(plNext, 61.920417, -125.562184, 70, -121.243557)
plNext = AddPolyLine_Arc_XY(plNext, 77.779833, -116.405746, 85.2266, -111.069468)
plNext = AddPolyLine_Arc_XY(plNext, 92.308414, -105.257573, 98.994949, -98.994949)
plNext = AddPolyLine_Arc_XY(plNext, 105.257573, -92.308414, 111.069468, -85.2266)
plNext = AddPolyLine_Arc_XY(plNext, 116.405746, -77.779833, 121.243557, -70)
plNext = AddPolyLine_Arc_XY(plNext, 125.562184, -61.920417, 129.343135, -53.575681)
plNext = AddPolyLine_Arc_XY(plNext, 132.570218, -45.001525, 135.229616, -36.234666)
plNext = AddPolyLine_Arc_XY(plNext, 137.309939, -27.312645, 138.802281, -18.273667)
plNext = AddPolyLine_Arc_XY(plNext, 139.700249, -9.156438, 140, 0)
plNext = AddPolyLine_Arc_XY(plNext, 139.700249, 9.156438, 138.802281, 18.273667)
plNext = AddPolyLine_Arc_XY(plNext, 137.309939, 27.312645, 135.229616, 36.234666)
plNext = AddPolyLine_Arc_XY(plNext, 132.570218, 45.001525, 129.343135, 53.575681)
plNext = AddPolyLine_Arc_XY(plNext, 125.562184, 61.920417, 121.243557, 70)
plNext = AddPolyLine_Arc_XY(plNext, 116.405746, 77.779833, 111.069468, 85.2266)
plNext = AddPolyLine_Arc_XY(plNext, 105.257573, 92.308414, 98.994949, 98.994949)
plNext = AddPolyLine_Arc_XY(plNext, 92.308414, 105.257573, 85.2266, 111.069468)
plNext = AddPolyLine_Arc_XY(plNext, 77.779833, 116.405746, 70, 121.243557)
plNext = AddPolyLine_Arc_XY(plNext, 61.920417, 125.562184, 53.575681, 129.343135)
plNext = AddPolyLine_Arc_XY(plNext, 45.001525, 132.570218, 36.234666, 135.229616)
plNext = AddPolyLine_Arc_XY(plNext, 27.312645, 137.309939, 18.273667, 138.802281)
plNext = AddPolyLine_Arc_XY(plNext, 9.156438, 139.700249, 0, 140)
plNext = AddPolyLine_Arc_XY(plNext, -9.156438, 139.700249, -18.273667, 138.802281)
plNext = AddPolyLine_Arc_XY(plNext, -27.312645, 137.309939, -36.234666, 135.229616)
plNext = AddPolyLine_Arc_XY(plNext, -45.001525, 132.570218, -53.575681, 129.343135)
plNext = AddPolyLine_Arc_XY(plNext, -61.920417, 125.562184, -70, 121.243557)
plNext = AddPolyLine_Arc_XY(plNext, -77.779833, 116.405746, -85.2266, 111.069468)
plNext = AddPolyLine_Arc_XY(plNext, -92.308414, 105.257573, -98.994949, 98.994949)
plNext = AddPolyLine_Arc_XY(plNext, -105.257573, 92.308414, -111.069468, 85.2266)
plNext = AddPolyLine_Arc_XY(plNext, -116.405746, 77.779833, -121.243557, 70)
plNext = AddPolyLine_Arc_XY(plNext, -125.562184, 61.920417, -129.343135, 53.575681)
plNext = AddPolyLine_Arc_XY(plNext, -132.570218, 45.001525, -135.229616, 36.234666)
plNext = AddPolyLine_Arc_XY(plNext, -137.309939, 27.312645, -138.802281, 18.273667)
ClosePolyLine_Arc_XY(plNext, -139.700249, 9.156438, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(139, 0)
plNext = AddPolyLine_Arc_XY(plStart, 138.70239, 9.091035, 137.810836, 18.143141)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, 27.117555, 134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, 44.680086, 128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, 61.478128, 120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, 77.224262, 110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, 91.649068, 98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, 104.505733, 84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, 115.574276, 69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, 124.665311, 53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, 131.623288, 35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, 136.329154, 18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, 138.70239, 0, 139)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, 138.70239, -18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, 136.329154, -35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, 131.623288, -53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, 124.665311, -69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, 115.574276, -84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, 104.505733, -98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, 91.649068, -110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, 77.224262, -120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, 61.478128, -128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, 44.680086, -134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, 27.117555, -137.810836, 18.143141)
plNext = AddPolyLine_Arc_XY(plNext, -138.70239, 9.091035, -139, 0)
plNext = AddPolyLine_Arc_XY(plNext, -138.70239, -9.091035, -137.810836, -18.143141)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, -27.117555, -134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, -44.680086, -128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, -61.478128, -120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, -77.224262, -110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, -91.649068, -98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, -104.505733, -84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, -115.574276, -69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, -124.665311, -53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, -131.623288, -35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, -136.329154, -18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, -138.70239, 0, -139)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, -138.70239, 18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, -136.329154, 35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, -131.623288, 53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, -124.665311, 69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, -115.574276, 84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, -104.505733, 98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, -91.649068, 110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, -77.224262, 120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, -61.478128, 128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, -44.680086, 134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, -27.117555, 137.810836, -18.143141)
ClosePolyLine_Arc_XY(plNext, 138.70239, -9.091035, plStart)
# End of Outline 2 PolyLine

# End of component housing_front


# Create new component housing_rear
newComp = CreateNamedComponentWithColour_Radial("housing_rear", -150.5, -23, 0, 16, 240, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(-140, 0)
plNext = AddPolyLine_Arc_XY(plStart, -139.700249, -9.156438, -138.802281, -18.273667)
plNext = AddPolyLine_Arc_XY(plNext, -137.309939, -27.312645, -135.229616, -36.234666)
plNext = AddPolyLine_Arc_XY(plNext, -132.570218, -45.001525, -129.343135, -53.575681)
plNext = AddPolyLine_Arc_XY(plNext, -125.562184, -61.920417, -121.243557, -70)
plNext = AddPolyLine_Arc_XY(plNext, -116.405746, -77.779833, -111.069468, -85.2266)
plNext = AddPolyLine_Arc_XY(plNext, -105.257573, -92.308414, -98.994949, -98.994949)
plNext = AddPolyLine_Arc_XY(plNext, -92.308414, -105.257573, -85.2266, -111.069468)
plNext = AddPolyLine_Arc_XY(plNext, -77.779833, -116.405746, -70, -121.243557)
plNext = AddPolyLine_Arc_XY(plNext, -61.920417, -125.562184, -53.575681, -129.343135)
plNext = AddPolyLine_Arc_XY(plNext, -45.001525, -132.570218, -36.234666, -135.229616)
plNext = AddPolyLine_Arc_XY(plNext, -27.312645, -137.309939, -18.273667, -138.802281)
plNext = AddPolyLine_Arc_XY(plNext, -9.156438, -139.700249, 0, -140)
plNext = AddPolyLine_Arc_XY(plNext, 9.156438, -139.700249, 18.273667, -138.802281)
plNext = AddPolyLine_Arc_XY(plNext, 27.312645, -137.309939, 36.234666, -135.229616)
plNext = AddPolyLine_Arc_XY(plNext, 45.001525, -132.570218, 53.575681, -129.343135)
plNext = AddPolyLine_Arc_XY(plNext, 61.920417, -125.562184, 70, -121.243557)
plNext = AddPolyLine_Arc_XY(plNext, 77.779833, -116.405746, 85.2266, -111.069468)
plNext = AddPolyLine_Arc_XY(plNext, 92.308414, -105.257573, 98.994949, -98.994949)
plNext = AddPolyLine_Arc_XY(plNext, 105.257573, -92.308414, 111.069468, -85.2266)
plNext = AddPolyLine_Arc_XY(plNext, 116.405746, -77.779833, 121.243557, -70)
plNext = AddPolyLine_Arc_XY(plNext, 125.562184, -61.920417, 129.343135, -53.575681)
plNext = AddPolyLine_Arc_XY(plNext, 132.570218, -45.001525, 135.229616, -36.234666)
plNext = AddPolyLine_Arc_XY(plNext, 137.309939, -27.312645, 138.802281, -18.273667)
plNext = AddPolyLine_Arc_XY(plNext, 139.700249, -9.156438, 140, 0)
plNext = AddPolyLine_Arc_XY(plNext, 139.700249, 9.156438, 138.802281, 18.273667)
plNext = AddPolyLine_Arc_XY(plNext, 137.309939, 27.312645, 135.229616, 36.234666)
plNext = AddPolyLine_Arc_XY(plNext, 132.570218, 45.001525, 129.343135, 53.575681)
plNext = AddPolyLine_Arc_XY(plNext, 125.562184, 61.920417, 121.243557, 70)
plNext = AddPolyLine_Arc_XY(plNext, 116.405746, 77.779833, 111.069468, 85.2266)
plNext = AddPolyLine_Arc_XY(plNext, 105.257573, 92.308414, 98.994949, 98.994949)
plNext = AddPolyLine_Arc_XY(plNext, 92.308414, 105.257573, 85.2266, 111.069468)
plNext = AddPolyLine_Arc_XY(plNext, 77.779833, 116.405746, 70, 121.243557)
plNext = AddPolyLine_Arc_XY(plNext, 61.920417, 125.562184, 53.575681, 129.343135)
plNext = AddPolyLine_Arc_XY(plNext, 45.001525, 132.570218, 36.234666, 135.229616)
plNext = AddPolyLine_Arc_XY(plNext, 27.312645, 137.309939, 18.273667, 138.802281)
plNext = AddPolyLine_Arc_XY(plNext, 9.156438, 139.700249, 0, 140)
plNext = AddPolyLine_Arc_XY(plNext, -9.156438, 139.700249, -18.273667, 138.802281)
plNext = AddPolyLine_Arc_XY(plNext, -27.312645, 137.309939, -36.234666, 135.229616)
plNext = AddPolyLine_Arc_XY(plNext, -45.001525, 132.570218, -53.575681, 129.343135)
plNext = AddPolyLine_Arc_XY(plNext, -61.920417, 125.562184, -70, 121.243557)
plNext = AddPolyLine_Arc_XY(plNext, -77.779833, 116.405746, -85.2266, 111.069468)
plNext = AddPolyLine_Arc_XY(plNext, -92.308414, 105.257573, -98.994949, 98.994949)
plNext = AddPolyLine_Arc_XY(plNext, -105.257573, 92.308414, -111.069468, 85.2266)
plNext = AddPolyLine_Arc_XY(plNext, -116.405746, 77.779833, -121.243557, 70)
plNext = AddPolyLine_Arc_XY(plNext, -125.562184, 61.920417, -129.343135, 53.575681)
plNext = AddPolyLine_Arc_XY(plNext, -132.570218, 45.001525, -135.229616, 36.234666)
plNext = AddPolyLine_Arc_XY(plNext, -137.309939, 27.312645, -138.802281, 18.273667)
ClosePolyLine_Arc_XY(plNext, -139.700249, 9.156438, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(139, 0)
plNext = AddPolyLine_Arc_XY(plStart, 138.70239, 9.091035, 137.810836, 18.143141)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, 27.117555, 134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, 44.680086, 128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, 61.478128, 120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, 77.224262, 110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, 91.649068, 98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, 104.505733, 84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, 115.574276, 69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, 124.665311, 53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, 131.623288, 35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, 136.329154, 18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, 138.70239, 0, 139)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, 138.70239, -18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, 136.329154, -35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, 131.623288, -53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, 124.665311, -69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, 115.574276, -84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, 104.505733, -98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, 91.649068, -110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, 77.224262, -120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, 61.478128, -128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, 44.680086, -134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, 27.117555, -137.810836, 18.143141)
plNext = AddPolyLine_Arc_XY(plNext, -138.70239, 9.091035, -139, 0)
plNext = AddPolyLine_Arc_XY(plNext, -138.70239, -9.091035, -137.810836, -18.143141)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, -27.117555, -134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, -44.680086, -128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, -61.478128, -120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, -77.224262, -110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, -91.649068, -98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, -104.505733, -84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, -115.574276, -69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, -124.665311, -53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, -131.623288, -35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, -136.329154, -18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, -138.70239, 0, -139)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, -138.70239, 18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, -136.329154, 35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, -131.623288, 53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, -124.665311, 69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, -115.574276, 84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, -104.505733, 98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, -91.649068, 110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, -77.224262, 120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, -61.478128, 128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, -44.680086, 134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, -27.117555, 137.810836, -18.143141)
ClosePolyLine_Arc_XY(plNext, 138.70239, -9.091035, plStart)
# End of Outline 2 PolyLine

# End of component housing_rear


# Create new component housing_active_1
newComp = CreateNamedComponentWithColour_Radial("housing_active_1", -54.5, -96, 0, 16, 240, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(-139, 0)
plNext = AddPolyLine_Arc_XY(plStart, -138.70239, -9.091035, -137.810836, -18.143141)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, -27.117555, -134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, -44.680086, -128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, -61.478128, -120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, -77.224262, -110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, -91.649068, -98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, -104.505733, -84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, -115.574276, -69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, -124.665311, -53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, -131.623288, -35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, -136.329154, -18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, -138.70239, 0, -139)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, -138.70239, 18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, -136.329154, 35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, -131.623288, 53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, -124.665311, 69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, -115.574276, 84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, -104.505733, 98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, -91.649068, 110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, -77.224262, 120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, -61.478128, 128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, -44.680086, 134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, -27.117555, 137.810836, -18.143141)
plNext = AddPolyLine_Arc_XY(plNext, 138.70239, -9.091035, 139, 0)
plNext = AddPolyLine_Arc_XY(plNext, 138.70239, 9.091035, 137.810836, 18.143141)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, 27.117555, 134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, 44.680086, 128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, 61.478128, 120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, 77.224262, 110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, 91.649068, 98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, 104.505733, 84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, 115.574276, 69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, 124.665311, 53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, 131.623288, 35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, 136.329154, 18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, 138.70239, 0, 139)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, 138.70239, -18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, 136.329154, -35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, 131.623288, -53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, 124.665311, -69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, 115.574276, -84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, 104.505733, -98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, 91.649068, -110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, 77.224262, -120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, 61.478128, -128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, 44.680086, -134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, 27.117555, -137.810836, 18.143141)
ClosePolyLine_Arc_XY(plNext, -138.70239, 9.091035, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(128, 0)
plNext = AddPolyLine_Arc_XY(plStart, 127.725942, 8.371601, 126.904942, 16.707353)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, 24.971561, 123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, 41.144252, 118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, 56.612952, 110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, 71.11299, 101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, 84.396264, 90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, 96.235495, 77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, 106.42811, 64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, 114.799711, 48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, 121.207057, 33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, 125.540516, 16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, 127.725942, 0, 128)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, 127.725942, -16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, 125.540516, -33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, 121.207057, -48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, 114.799711, -64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, 106.42811, -77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, 96.235495, -90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, 84.396264, -101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, 71.11299, -110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, 56.612952, -118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, 41.144252, -123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, 24.971561, -126.904942, 16.707353)
plNext = AddPolyLine_Arc_XY(plNext, -127.725942, 8.371601, -128, 0)
plNext = AddPolyLine_Arc_XY(plNext, -127.725942, -8.371601, -126.904942, -16.707353)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, -24.971561, -123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, -41.144252, -118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, -56.612952, -110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, -71.11299, -101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, -84.396264, -90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, -96.235495, -77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, -106.42811, -64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, -114.799711, -48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, -121.207057, -33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, -125.540516, -16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, -127.725942, 0, -128)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, -127.725942, 16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, -125.540516, 33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, -121.207057, 48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, -114.799711, 64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, -106.42811, 77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, -96.235495, 90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, -84.396264, 101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, -71.11299, 110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, -56.612952, 118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, -41.144252, 123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, -24.971561, 126.904942, -16.707353)
ClosePolyLine_Arc_XY(plNext, 127.725942, -8.371601, plStart)
# End of Outline 2 PolyLine

# End of component housing_active_1


# Create new component housing_front_1
newComp = CreateNamedComponentWithColour_Radial("housing_front_1", -26.5, -28, 0, 16, 240, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(-139, 0)
plNext = AddPolyLine_Arc_XY(plStart, -138.70239, -9.091035, -137.810836, -18.143141)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, -27.117555, -134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, -44.680086, -128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, -61.478128, -120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, -77.224262, -110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, -91.649068, -98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, -104.505733, -84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, -115.574276, -69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, -124.665311, -53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, -131.623288, -35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, -136.329154, -18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, -138.70239, 0, -139)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, -138.70239, 18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, -136.329154, 35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, -131.623288, 53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, -124.665311, 69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, -115.574276, 84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, -104.505733, 98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, -91.649068, 110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, -77.224262, 120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, -61.478128, 128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, -44.680086, 134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, -27.117555, 137.810836, -18.143141)
plNext = AddPolyLine_Arc_XY(plNext, 138.70239, -9.091035, 139, 0)
plNext = AddPolyLine_Arc_XY(plNext, 138.70239, 9.091035, 137.810836, 18.143141)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, 27.117555, 134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, 44.680086, 128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, 61.478128, 120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, 77.224262, 110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, 91.649068, 98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, 104.505733, 84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, 115.574276, 69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, 124.665311, 53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, 131.623288, 35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, 136.329154, 18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, 138.70239, 0, 139)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, 138.70239, -18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, 136.329154, -35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, 131.623288, -53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, 124.665311, -69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, 115.574276, -84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, 104.505733, -98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, 91.649068, -110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, 77.224262, -120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, 61.478128, -128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, 44.680086, -134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, 27.117555, -137.810836, 18.143141)
ClosePolyLine_Arc_XY(plNext, -138.70239, 9.091035, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(128, 0)
plNext = AddPolyLine_Arc_XY(plStart, 127.725942, 8.371601, 126.904942, 16.707353)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, 24.971561, 123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, 41.144252, 118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, 56.612952, 110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, 71.11299, 101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, 84.396264, 90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, 96.235495, 77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, 106.42811, 64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, 114.799711, 48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, 121.207057, 33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, 125.540516, 16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, 127.725942, 0, 128)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, 127.725942, -16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, 125.540516, -33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, 121.207057, -48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, 114.799711, -64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, 106.42811, -77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, 96.235495, -90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, 84.396264, -101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, 71.11299, -110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, 56.612952, -118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, 41.144252, -123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, 24.971561, -126.904942, 16.707353)
plNext = AddPolyLine_Arc_XY(plNext, -127.725942, 8.371601, -128, 0)
plNext = AddPolyLine_Arc_XY(plNext, -127.725942, -8.371601, -126.904942, -16.707353)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, -24.971561, -123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, -41.144252, -118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, -56.612952, -110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, -71.11299, -101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, -84.396264, -90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, -96.235495, -77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, -106.42811, -64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, -114.799711, -48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, -121.207057, -33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, -125.540516, -16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, -127.725942, 0, -128)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, -127.725942, 16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, -125.540516, 33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, -121.207057, 48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, -114.799711, 64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, -106.42811, 77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, -96.235495, 90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, -84.396264, 101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, -71.11299, 110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, -56.612952, 118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, -41.144252, 123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, -24.971561, 126.904942, -16.707353)
ClosePolyLine_Arc_XY(plNext, 127.725942, -8.371601, plStart)
# End of Outline 2 PolyLine

# End of component housing_front_1


# Create new component housing_rear_1
newComp = CreateNamedComponentWithColour_Radial("housing_rear_1", -150.5, -23, 0, 16, 240, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(-139, 0)
plNext = AddPolyLine_Arc_XY(plStart, -138.70239, -9.091035, -137.810836, -18.143141)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, -27.117555, -134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, -44.680086, -128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, -61.478128, -120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, -77.224262, -110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, -91.649068, -98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, -104.505733, -84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, -115.574276, -69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, -124.665311, -53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, -131.623288, -35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, -136.329154, -18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, -138.70239, 0, -139)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, -138.70239, 18.143141, -137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, -136.329154, 35.975847, -134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, -131.623288, 53.192997, -128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, -124.665311, 69.5, -120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, -115.574276, 84.617839, -110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, -104.505733, 98.287843, -98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, -91.649068, 110.276114, -84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, -77.224262, 120.377531, -69.5)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, -61.478128, 128.419255, -53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, -44.680086, 134.26369, -35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, -27.117555, 137.810836, -18.143141)
plNext = AddPolyLine_Arc_XY(plNext, 138.70239, -9.091035, 139, 0)
plNext = AddPolyLine_Arc_XY(plNext, 138.70239, 9.091035, 137.810836, 18.143141)
plNext = AddPolyLine_Arc_XY(plNext, 136.329154, 27.117555, 134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, 131.623288, 44.680086, 128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, 124.665311, 61.478128, 120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, 115.574276, 77.224262, 110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, 104.505733, 91.649068, 98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, 91.649068, 104.505733, 84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, 77.224262, 115.574276, 69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, 61.478128, 124.665311, 53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, 44.680086, 131.623288, 35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, 27.117555, 136.329154, 18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, 9.091035, 138.70239, 0, 139)
plNext = AddPolyLine_Arc_XY(plNext, -9.091035, 138.70239, -18.143141, 137.810836)
plNext = AddPolyLine_Arc_XY(plNext, -27.117555, 136.329154, -35.975847, 134.26369)
plNext = AddPolyLine_Arc_XY(plNext, -44.680086, 131.623288, -53.192997, 128.419255)
plNext = AddPolyLine_Arc_XY(plNext, -61.478128, 124.665311, -69.5, 120.377531)
plNext = AddPolyLine_Arc_XY(plNext, -77.224262, 115.574276, -84.617839, 110.276114)
plNext = AddPolyLine_Arc_XY(plNext, -91.649068, 104.505733, -98.287843, 98.287843)
plNext = AddPolyLine_Arc_XY(plNext, -104.505733, 91.649068, -110.276114, 84.617839)
plNext = AddPolyLine_Arc_XY(plNext, -115.574276, 77.224262, -120.377531, 69.5)
plNext = AddPolyLine_Arc_XY(plNext, -124.665311, 61.478128, -128.419255, 53.192997)
plNext = AddPolyLine_Arc_XY(plNext, -131.623288, 44.680086, -134.26369, 35.975847)
plNext = AddPolyLine_Arc_XY(plNext, -136.329154, 27.117555, -137.810836, 18.143141)
ClosePolyLine_Arc_XY(plNext, -138.70239, 9.091035, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(128, 0)
plNext = AddPolyLine_Arc_XY(plStart, 127.725942, 8.371601, 126.904942, 16.707353)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, 24.971561, 123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, 41.144252, 118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, 56.612952, 110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, 71.11299, 101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, 84.396264, 90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, 96.235495, 77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, 106.42811, 64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, 114.799711, 48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, 121.207057, 33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, 125.540516, 16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, 127.725942, 0, 128)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, 127.725942, -16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, 125.540516, -33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, 121.207057, -48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, 114.799711, -64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, 106.42811, -77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, 96.235495, -90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, 84.396264, -101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, 71.11299, -110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, 56.612952, -118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, 41.144252, -123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, 24.971561, -126.904942, 16.707353)
plNext = AddPolyLine_Arc_XY(plNext, -127.725942, 8.371601, -128, 0)
plNext = AddPolyLine_Arc_XY(plNext, -127.725942, -8.371601, -126.904942, -16.707353)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, -24.971561, -123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, -41.144252, -118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, -56.612952, -110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, -71.11299, -101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, -84.396264, -90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, -96.235495, -77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, -106.42811, -64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, -114.799711, -48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, -121.207057, -33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, -125.540516, -16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, -127.725942, 0, -128)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, -127.725942, 16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, -125.540516, 33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, -121.207057, 48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, -114.799711, 64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, -106.42811, 77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, -96.235495, 90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, -84.396264, 101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, -71.11299, 110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, -56.612952, 118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, -41.144252, 123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, -24.971561, 126.904942, -16.707353)
ClosePolyLine_Arc_XY(plNext, 127.725942, -8.371601, plStart)
# End of Outline 2 PolyLine

# End of component housing_rear_1


# Create new component housing_active_2
newComp = CreateNamedComponentWithColour_Radial("housing_active_2", -54.5, -96, 0, 16, 240, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(-128, 0)
plNext = AddPolyLine_Arc_XY(plStart, -127.725942, -8.371601, -126.904942, -16.707353)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, -24.971561, -123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, -41.144252, -118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, -56.612952, -110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, -71.11299, -101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, -84.396264, -90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, -96.235495, -77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, -106.42811, -64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, -114.799711, -48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, -121.207057, -33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, -125.540516, -16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, -127.725942, 0, -128)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, -127.725942, 16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, -125.540516, 33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, -121.207057, 48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, -114.799711, 64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, -106.42811, 77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, -96.235495, 90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, -84.396264, 101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, -71.11299, 110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, -56.612952, 118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, -41.144252, 123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, -24.971561, 126.904942, -16.707353)
plNext = AddPolyLine_Arc_XY(plNext, 127.725942, -8.371601, 128, 0)
plNext = AddPolyLine_Arc_XY(plNext, 127.725942, 8.371601, 126.904942, 16.707353)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, 24.971561, 123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, 41.144252, 118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, 56.612952, 110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, 71.11299, 101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, 84.396264, 90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, 96.235495, 77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, 106.42811, 64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, 114.799711, 48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, 121.207057, 33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, 125.540516, 16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, 127.725942, 0, 128)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, 127.725942, -16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, 125.540516, -33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, 121.207057, -48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, 114.799711, -64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, 106.42811, -77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, 96.235495, -90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, 84.396264, -101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, 71.11299, -110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, 56.612952, -118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, 41.144252, -123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, 24.971561, -126.904942, 16.707353)
ClosePolyLine_Arc_XY(plNext, -127.725942, 8.371601, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(120, 0)
plNext = AddPolyLine_Arc_XY(plStart, 119.743071, 7.848376, 118.973383, 15.663143)
plNext = AddPolyLine_Arc_XY(plNext, 117.694234, 23.410839, 115.911099, 31.058285)
plNext = AddPolyLine_Arc_XY(plNext, 113.631616, 38.572736, 110.865544, 45.922012)
plNext = AddPolyLine_Arc_XY(plNext, 107.624729, 53.074643, 103.923048, 60)
plNext = AddPolyLine_Arc_XY(plNext, 99.776353, 66.668428, 95.202401, 73.051371)
plNext = AddPolyLine_Arc_XY(plNext, 90.220777, 79.121498, 84.852814, 84.852814)
plNext = AddPolyLine_Arc_XY(plNext, 79.121498, 90.220777, 73.051371, 95.202401)
plNext = AddPolyLine_Arc_XY(plNext, 66.668428, 99.776353, 60, 103.923048)
plNext = AddPolyLine_Arc_XY(plNext, 53.074643, 107.624729, 45.922012, 110.865544)
plNext = AddPolyLine_Arc_XY(plNext, 38.572736, 113.631616, 31.058285, 115.911099)
plNext = AddPolyLine_Arc_XY(plNext, 23.410839, 117.694234, 15.663143, 118.973383)
plNext = AddPolyLine_Arc_XY(plNext, 7.848376, 119.743071, 0, 120)
plNext = AddPolyLine_Arc_XY(plNext, -7.848376, 119.743071, -15.663143, 118.973383)
plNext = AddPolyLine_Arc_XY(plNext, -23.410839, 117.694234, -31.058285, 115.911099)
plNext = AddPolyLine_Arc_XY(plNext, -38.572736, 113.631616, -45.922012, 110.865544)
plNext = AddPolyLine_Arc_XY(plNext, -53.074643, 107.624729, -60, 103.923048)
plNext = AddPolyLine_Arc_XY(plNext, -66.668428, 99.776353, -73.051371, 95.202401)
plNext = AddPolyLine_Arc_XY(plNext, -79.121498, 90.220777, -84.852814, 84.852814)
plNext = AddPolyLine_Arc_XY(plNext, -90.220777, 79.121498, -95.202401, 73.051371)
plNext = AddPolyLine_Arc_XY(plNext, -99.776353, 66.668428, -103.923048, 60)
plNext = AddPolyLine_Arc_XY(plNext, -107.624729, 53.074643, -110.865544, 45.922012)
plNext = AddPolyLine_Arc_XY(plNext, -113.631616, 38.572736, -115.911099, 31.058285)
plNext = AddPolyLine_Arc_XY(plNext, -117.694234, 23.410839, -118.973383, 15.663143)
plNext = AddPolyLine_Arc_XY(plNext, -119.743071, 7.848376, -120, 0)
plNext = AddPolyLine_Arc_XY(plNext, -119.743071, -7.848376, -118.973383, -15.663143)
plNext = AddPolyLine_Arc_XY(plNext, -117.694234, -23.410839, -115.911099, -31.058285)
plNext = AddPolyLine_Arc_XY(plNext, -113.631616, -38.572736, -110.865544, -45.922012)
plNext = AddPolyLine_Arc_XY(plNext, -107.624729, -53.074643, -103.923048, -60)
plNext = AddPolyLine_Arc_XY(plNext, -99.776353, -66.668428, -95.202401, -73.051371)
plNext = AddPolyLine_Arc_XY(plNext, -90.220777, -79.121498, -84.852814, -84.852814)
plNext = AddPolyLine_Arc_XY(plNext, -79.121498, -90.220777, -73.051371, -95.202401)
plNext = AddPolyLine_Arc_XY(plNext, -66.668428, -99.776353, -60, -103.923048)
plNext = AddPolyLine_Arc_XY(plNext, -53.074643, -107.624729, -45.922012, -110.865544)
plNext = AddPolyLine_Arc_XY(plNext, -38.572736, -113.631616, -31.058285, -115.911099)
plNext = AddPolyLine_Arc_XY(plNext, -23.410839, -117.694234, -15.663143, -118.973383)
plNext = AddPolyLine_Arc_XY(plNext, -7.848376, -119.743071, 0, -120)
plNext = AddPolyLine_Arc_XY(plNext, 7.848376, -119.743071, 15.663143, -118.973383)
plNext = AddPolyLine_Arc_XY(plNext, 23.410839, -117.694234, 31.058285, -115.911099)
plNext = AddPolyLine_Arc_XY(plNext, 38.572736, -113.631616, 45.922012, -110.865544)
plNext = AddPolyLine_Arc_XY(plNext, 53.074643, -107.624729, 60, -103.923048)
plNext = AddPolyLine_Arc_XY(plNext, 66.668428, -99.776353, 73.051371, -95.202401)
plNext = AddPolyLine_Arc_XY(plNext, 79.121498, -90.220777, 84.852814, -84.852814)
plNext = AddPolyLine_Arc_XY(plNext, 90.220777, -79.121498, 95.202401, -73.051371)
plNext = AddPolyLine_Arc_XY(plNext, 99.776353, -66.668428, 103.923048, -60)
plNext = AddPolyLine_Arc_XY(plNext, 107.624729, -53.074643, 110.865544, -45.922012)
plNext = AddPolyLine_Arc_XY(plNext, 113.631616, -38.572736, 115.911099, -31.058285)
plNext = AddPolyLine_Arc_XY(plNext, 117.694234, -23.410839, 118.973383, -15.663143)
ClosePolyLine_Arc_XY(plNext, 119.743071, -7.848376, plStart)
# End of Outline 2 PolyLine

# End of component housing_active_2


# Create new component housing_front_2
newComp = CreateNamedComponentWithColour_Radial("housing_front_2", -26.5, -28, 0, 16, 240, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(-128, 0)
plNext = AddPolyLine_Arc_XY(plStart, -127.725942, -8.371601, -126.904942, -16.707353)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, -24.971561, -123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, -41.144252, -118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, -56.612952, -110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, -71.11299, -101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, -84.396264, -90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, -96.235495, -77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, -106.42811, -64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, -114.799711, -48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, -121.207057, -33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, -125.540516, -16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, -127.725942, 0, -128)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, -127.725942, 16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, -125.540516, 33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, -121.207057, 48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, -114.799711, 64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, -106.42811, 77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, -96.235495, 90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, -84.396264, 101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, -71.11299, 110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, -56.612952, 118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, -41.144252, 123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, -24.971561, 126.904942, -16.707353)
plNext = AddPolyLine_Arc_XY(plNext, 127.725942, -8.371601, 128, 0)
plNext = AddPolyLine_Arc_XY(plNext, 127.725942, 8.371601, 126.904942, 16.707353)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, 24.971561, 123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, 41.144252, 118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, 56.612952, 110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, 71.11299, 101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, 84.396264, 90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, 96.235495, 77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, 106.42811, 64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, 114.799711, 48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, 121.207057, 33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, 125.540516, 16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, 127.725942, 0, 128)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, 127.725942, -16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, 125.540516, -33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, 121.207057, -48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, 114.799711, -64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, 106.42811, -77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, 96.235495, -90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, 84.396264, -101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, 71.11299, -110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, 56.612952, -118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, 41.144252, -123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, 24.971561, -126.904942, 16.707353)
ClosePolyLine_Arc_XY(plNext, -127.725942, 8.371601, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(120, 0)
plNext = AddPolyLine_Arc_XY(plStart, 119.743071, 7.848376, 118.973383, 15.663143)
plNext = AddPolyLine_Arc_XY(plNext, 117.694234, 23.410839, 115.911099, 31.058285)
plNext = AddPolyLine_Arc_XY(plNext, 113.631616, 38.572736, 110.865544, 45.922012)
plNext = AddPolyLine_Arc_XY(plNext, 107.624729, 53.074643, 103.923048, 60)
plNext = AddPolyLine_Arc_XY(plNext, 99.776353, 66.668428, 95.202401, 73.051371)
plNext = AddPolyLine_Arc_XY(plNext, 90.220777, 79.121498, 84.852814, 84.852814)
plNext = AddPolyLine_Arc_XY(plNext, 79.121498, 90.220777, 73.051371, 95.202401)
plNext = AddPolyLine_Arc_XY(plNext, 66.668428, 99.776353, 60, 103.923048)
plNext = AddPolyLine_Arc_XY(plNext, 53.074643, 107.624729, 45.922012, 110.865544)
plNext = AddPolyLine_Arc_XY(plNext, 38.572736, 113.631616, 31.058285, 115.911099)
plNext = AddPolyLine_Arc_XY(plNext, 23.410839, 117.694234, 15.663143, 118.973383)
plNext = AddPolyLine_Arc_XY(plNext, 7.848376, 119.743071, 0, 120)
plNext = AddPolyLine_Arc_XY(plNext, -7.848376, 119.743071, -15.663143, 118.973383)
plNext = AddPolyLine_Arc_XY(plNext, -23.410839, 117.694234, -31.058285, 115.911099)
plNext = AddPolyLine_Arc_XY(plNext, -38.572736, 113.631616, -45.922012, 110.865544)
plNext = AddPolyLine_Arc_XY(plNext, -53.074643, 107.624729, -60, 103.923048)
plNext = AddPolyLine_Arc_XY(plNext, -66.668428, 99.776353, -73.051371, 95.202401)
plNext = AddPolyLine_Arc_XY(plNext, -79.121498, 90.220777, -84.852814, 84.852814)
plNext = AddPolyLine_Arc_XY(plNext, -90.220777, 79.121498, -95.202401, 73.051371)
plNext = AddPolyLine_Arc_XY(plNext, -99.776353, 66.668428, -103.923048, 60)
plNext = AddPolyLine_Arc_XY(plNext, -107.624729, 53.074643, -110.865544, 45.922012)
plNext = AddPolyLine_Arc_XY(plNext, -113.631616, 38.572736, -115.911099, 31.058285)
plNext = AddPolyLine_Arc_XY(plNext, -117.694234, 23.410839, -118.973383, 15.663143)
plNext = AddPolyLine_Arc_XY(plNext, -119.743071, 7.848376, -120, 0)
plNext = AddPolyLine_Arc_XY(plNext, -119.743071, -7.848376, -118.973383, -15.663143)
plNext = AddPolyLine_Arc_XY(plNext, -117.694234, -23.410839, -115.911099, -31.058285)
plNext = AddPolyLine_Arc_XY(plNext, -113.631616, -38.572736, -110.865544, -45.922012)
plNext = AddPolyLine_Arc_XY(plNext, -107.624729, -53.074643, -103.923048, -60)
plNext = AddPolyLine_Arc_XY(plNext, -99.776353, -66.668428, -95.202401, -73.051371)
plNext = AddPolyLine_Arc_XY(plNext, -90.220777, -79.121498, -84.852814, -84.852814)
plNext = AddPolyLine_Arc_XY(plNext, -79.121498, -90.220777, -73.051371, -95.202401)
plNext = AddPolyLine_Arc_XY(plNext, -66.668428, -99.776353, -60, -103.923048)
plNext = AddPolyLine_Arc_XY(plNext, -53.074643, -107.624729, -45.922012, -110.865544)
plNext = AddPolyLine_Arc_XY(plNext, -38.572736, -113.631616, -31.058285, -115.911099)
plNext = AddPolyLine_Arc_XY(plNext, -23.410839, -117.694234, -15.663143, -118.973383)
plNext = AddPolyLine_Arc_XY(plNext, -7.848376, -119.743071, 0, -120)
plNext = AddPolyLine_Arc_XY(plNext, 7.848376, -119.743071, 15.663143, -118.973383)
plNext = AddPolyLine_Arc_XY(plNext, 23.410839, -117.694234, 31.058285, -115.911099)
plNext = AddPolyLine_Arc_XY(plNext, 38.572736, -113.631616, 45.922012, -110.865544)
plNext = AddPolyLine_Arc_XY(plNext, 53.074643, -107.624729, 60, -103.923048)
plNext = AddPolyLine_Arc_XY(plNext, 66.668428, -99.776353, 73.051371, -95.202401)
plNext = AddPolyLine_Arc_XY(plNext, 79.121498, -90.220777, 84.852814, -84.852814)
plNext = AddPolyLine_Arc_XY(plNext, 90.220777, -79.121498, 95.202401, -73.051371)
plNext = AddPolyLine_Arc_XY(plNext, 99.776353, -66.668428, 103.923048, -60)
plNext = AddPolyLine_Arc_XY(plNext, 107.624729, -53.074643, 110.865544, -45.922012)
plNext = AddPolyLine_Arc_XY(plNext, 113.631616, -38.572736, 115.911099, -31.058285)
plNext = AddPolyLine_Arc_XY(plNext, 117.694234, -23.410839, 118.973383, -15.663143)
ClosePolyLine_Arc_XY(plNext, 119.743071, -7.848376, plStart)
# End of Outline 2 PolyLine

# End of component housing_front_2


# Create new component housing_rear_2
newComp = CreateNamedComponentWithColour_Radial("housing_rear_2", -150.5, -23, 0, 16, 240, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(-128, 0)
plNext = AddPolyLine_Arc_XY(plStart, -127.725942, -8.371601, -126.904942, -16.707353)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, -24.971561, -123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, -41.144252, -118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, -56.612952, -110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, -71.11299, -101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, -84.396264, -90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, -96.235495, -77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, -106.42811, -64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, -114.799711, -48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, -121.207057, -33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, -125.540516, -16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, -127.725942, 0, -128)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, -127.725942, 16.707353, -126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, -125.540516, 33.128838, -123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, -121.207057, 48.983479, -118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, -114.799711, 64, -110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, -106.42811, 77.921463, -101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, -96.235495, 90.509668, -90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, -84.396264, 101.549228, -77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, -71.11299, 110.851252, -64)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, -56.612952, 118.25658, -48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, -41.144252, 123.638506, -33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, -24.971561, 126.904942, -16.707353)
plNext = AddPolyLine_Arc_XY(plNext, 127.725942, -8.371601, 128, 0)
plNext = AddPolyLine_Arc_XY(plNext, 127.725942, 8.371601, 126.904942, 16.707353)
plNext = AddPolyLine_Arc_XY(plNext, 125.540516, 24.971561, 123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, 121.207057, 41.144252, 118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, 114.799711, 56.612952, 110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, 106.42811, 71.11299, 101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, 96.235495, 84.396264, 90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, 84.396264, 96.235495, 77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, 71.11299, 106.42811, 64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, 56.612952, 114.799711, 48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, 41.144252, 121.207057, 33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, 24.971561, 125.540516, 16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, 8.371601, 127.725942, 0, 128)
plNext = AddPolyLine_Arc_XY(plNext, -8.371601, 127.725942, -16.707353, 126.904942)
plNext = AddPolyLine_Arc_XY(plNext, -24.971561, 125.540516, -33.128838, 123.638506)
plNext = AddPolyLine_Arc_XY(plNext, -41.144252, 121.207057, -48.983479, 118.25658)
plNext = AddPolyLine_Arc_XY(plNext, -56.612952, 114.799711, -64, 110.851252)
plNext = AddPolyLine_Arc_XY(plNext, -71.11299, 106.42811, -77.921463, 101.549228)
plNext = AddPolyLine_Arc_XY(plNext, -84.396264, 96.235495, -90.509668, 90.509668)
plNext = AddPolyLine_Arc_XY(plNext, -96.235495, 84.396264, -101.549228, 77.921463)
plNext = AddPolyLine_Arc_XY(plNext, -106.42811, 71.11299, -110.851252, 64)
plNext = AddPolyLine_Arc_XY(plNext, -114.799711, 56.612952, -118.25658, 48.983479)
plNext = AddPolyLine_Arc_XY(plNext, -121.207057, 41.144252, -123.638506, 33.128838)
plNext = AddPolyLine_Arc_XY(plNext, -125.540516, 24.971561, -126.904942, 16.707353)
ClosePolyLine_Arc_XY(plNext, -127.725942, 8.371601, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(120, 0)
plNext = AddPolyLine_Arc_XY(plStart, 119.743071, 7.848376, 118.973383, 15.663143)
plNext = AddPolyLine_Arc_XY(plNext, 117.694234, 23.410839, 115.911099, 31.058285)
plNext = AddPolyLine_Arc_XY(plNext, 113.631616, 38.572736, 110.865544, 45.922012)
plNext = AddPolyLine_Arc_XY(plNext, 107.624729, 53.074643, 103.923048, 60)
plNext = AddPolyLine_Arc_XY(plNext, 99.776353, 66.668428, 95.202401, 73.051371)
plNext = AddPolyLine_Arc_XY(plNext, 90.220777, 79.121498, 84.852814, 84.852814)
plNext = AddPolyLine_Arc_XY(plNext, 79.121498, 90.220777, 73.051371, 95.202401)
plNext = AddPolyLine_Arc_XY(plNext, 66.668428, 99.776353, 60, 103.923048)
plNext = AddPolyLine_Arc_XY(plNext, 53.074643, 107.624729, 45.922012, 110.865544)
plNext = AddPolyLine_Arc_XY(plNext, 38.572736, 113.631616, 31.058285, 115.911099)
plNext = AddPolyLine_Arc_XY(plNext, 23.410839, 117.694234, 15.663143, 118.973383)
plNext = AddPolyLine_Arc_XY(plNext, 7.848376, 119.743071, 0, 120)
plNext = AddPolyLine_Arc_XY(plNext, -7.848376, 119.743071, -15.663143, 118.973383)
plNext = AddPolyLine_Arc_XY(plNext, -23.410839, 117.694234, -31.058285, 115.911099)
plNext = AddPolyLine_Arc_XY(plNext, -38.572736, 113.631616, -45.922012, 110.865544)
plNext = AddPolyLine_Arc_XY(plNext, -53.074643, 107.624729, -60, 103.923048)
plNext = AddPolyLine_Arc_XY(plNext, -66.668428, 99.776353, -73.051371, 95.202401)
plNext = AddPolyLine_Arc_XY(plNext, -79.121498, 90.220777, -84.852814, 84.852814)
plNext = AddPolyLine_Arc_XY(plNext, -90.220777, 79.121498, -95.202401, 73.051371)
plNext = AddPolyLine_Arc_XY(plNext, -99.776353, 66.668428, -103.923048, 60)
plNext = AddPolyLine_Arc_XY(plNext, -107.624729, 53.074643, -110.865544, 45.922012)
plNext = AddPolyLine_Arc_XY(plNext, -113.631616, 38.572736, -115.911099, 31.058285)
plNext = AddPolyLine_Arc_XY(plNext, -117.694234, 23.410839, -118.973383, 15.663143)
plNext = AddPolyLine_Arc_XY(plNext, -119.743071, 7.848376, -120, 0)
plNext = AddPolyLine_Arc_XY(plNext, -119.743071, -7.848376, -118.973383, -15.663143)
plNext = AddPolyLine_Arc_XY(plNext, -117.694234, -23.410839, -115.911099, -31.058285)
plNext = AddPolyLine_Arc_XY(plNext, -113.631616, -38.572736, -110.865544, -45.922012)
plNext = AddPolyLine_Arc_XY(plNext, -107.624729, -53.074643, -103.923048, -60)
plNext = AddPolyLine_Arc_XY(plNext, -99.776353, -66.668428, -95.202401, -73.051371)
plNext = AddPolyLine_Arc_XY(plNext, -90.220777, -79.121498, -84.852814, -84.852814)
plNext = AddPolyLine_Arc_XY(plNext, -79.121498, -90.220777, -73.051371, -95.202401)
plNext = AddPolyLine_Arc_XY(plNext, -66.668428, -99.776353, -60, -103.923048)
plNext = AddPolyLine_Arc_XY(plNext, -53.074643, -107.624729, -45.922012, -110.865544)
plNext = AddPolyLine_Arc_XY(plNext, -38.572736, -113.631616, -31.058285, -115.911099)
plNext = AddPolyLine_Arc_XY(plNext, -23.410839, -117.694234, -15.663143, -118.973383)
plNext = AddPolyLine_Arc_XY(plNext, -7.848376, -119.743071, 0, -120)
plNext = AddPolyLine_Arc_XY(plNext, 7.848376, -119.743071, 15.663143, -118.973383)
plNext = AddPolyLine_Arc_XY(plNext, 23.410839, -117.694234, 31.058285, -115.911099)
plNext = AddPolyLine_Arc_XY(plNext, 38.572736, -113.631616, 45.922012, -110.865544)
plNext = AddPolyLine_Arc_XY(plNext, 53.074643, -107.624729, 60, -103.923048)
plNext = AddPolyLine_Arc_XY(plNext, 66.668428, -99.776353, 73.051371, -95.202401)
plNext = AddPolyLine_Arc_XY(plNext, 79.121498, -90.220777, 84.852814, -84.852814)
plNext = AddPolyLine_Arc_XY(plNext, 90.220777, -79.121498, 95.202401, -73.051371)
plNext = AddPolyLine_Arc_XY(plNext, 99.776353, -66.668428, 103.923048, -60)
plNext = AddPolyLine_Arc_XY(plNext, 107.624729, -53.074643, 110.865544, -45.922012)
plNext = AddPolyLine_Arc_XY(plNext, 113.631616, -38.572736, 115.911099, -31.058285)
plNext = AddPolyLine_Arc_XY(plNext, 117.694234, -23.410839, 118.973383, -15.663143)
ClosePolyLine_Arc_XY(plNext, 119.743071, -7.848376, plStart)
# End of Outline 2 PolyLine

# End of component housing_rear_2


# Create new component stator_lamination
newComp = CreateNamedComponentWithColour_Radial("stator_lamination", -54.5, -96, 247, 127, 135, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-118.973383, 15.663143)
plNext = AddPolyLine_Arc_XY(plStart, -119.743071, 7.848376, -120, 0)
plNext = AddPolyLine_Arc_XY(plNext, -119.743071, -7.848376, -118.973383, -15.663143)
plNext = AddPolyLine_Arc_XY(plNext, -117.694234, -23.410839, -115.911099, -31.058285)
plNext = AddPolyLine_Arc_XY(plNext, -113.631616, -38.572736, -110.865544, -45.922012)
plNext = AddPolyLine_Arc_XY(plNext, -107.624729, -53.074643, -103.923048, -60)
plNext = AddPolyLine_Arc_XY(plNext, -99.776353, -66.668428, -95.202401, -73.051371)
plNext = AddPolyLine_Arc_XY(plNext, -90.220777, -79.121498, -84.852814, -84.852814)
plNext = AddPolyLine_Arc_XY(plNext, -79.121498, -90.220777, -73.051371, -95.202401)
plNext = AddPolyLine_Arc_XY(plNext, -66.668428, -99.776353, -60, -103.923048)
plNext = AddPolyLine_Arc_XY(plNext, -53.074643, -107.624729, -45.922012, -110.865544)
plNext = AddPolyLine_Arc_XY(plNext, -38.572736, -113.631616, -31.058285, -115.911099)
plNext = AddPolyLine_Arc_XY(plNext, -23.410839, -117.694234, -15.663143, -118.973383)
plNext = AddPolyLine_Arc_XY(plNext, -7.848376, -119.743071, 0, -120)
plNext = AddPolyLine_Arc_XY(plNext, 7.848376, -119.743071, 15.663143, -118.973383)
plNext = AddPolyLine_Arc_XY(plNext, 23.410839, -117.694234, 31.058285, -115.911099)
plNext = AddPolyLine_Arc_XY(plNext, 38.572736, -113.631616, 45.922012, -110.865544)
plNext = AddPolyLine_Arc_XY(plNext, 53.074643, -107.624729, 60, -103.923048)
plNext = AddPolyLine_Arc_XY(plNext, 66.668428, -99.776353, 73.051371, -95.202401)
plNext = AddPolyLine_Arc_XY(plNext, 79.121498, -90.220777, 84.852814, -84.852814)
plNext = AddPolyLine_Arc_XY(plNext, 90.220777, -79.121498, 95.202401, -73.051371)
plNext = AddPolyLine_Arc_XY(plNext, 99.776353, -66.668428, 103.923048, -60)
plNext = AddPolyLine_Arc_XY(plNext, 107.624729, -53.074643, 110.865544, -45.922012)
plNext = AddPolyLine_Arc_XY(plNext, 113.631616, -38.572736, 115.911099, -31.058285)
plNext = AddPolyLine_Arc_XY(plNext, 117.694234, -23.410839, 118.973383, -15.663143)
plNext = AddPolyLine_Arc_XY(plNext, 119.743071, -7.848376, 120, 0)
plNext = AddPolyLine_Arc_XY(plNext, 119.743071, 7.848376, 118.973383, 15.663143)
plNext = AddPolyLine_Arc_XY(plNext, 117.694234, 23.410839, 115.911099, 31.058285)
plNext = AddPolyLine_Arc_XY(plNext, 113.631616, 38.572736, 110.865544, 45.922012)
plNext = AddPolyLine_Arc_XY(plNext, 107.624729, 53.074643, 103.923048, 60)
plNext = AddPolyLine_Arc_XY(plNext, 99.776353, 66.668428, 95.202401, 73.051371)
plNext = AddPolyLine_Arc_XY(plNext, 90.220777, 79.121498, 84.852814, 84.852814)
plNext = AddPolyLine_Arc_XY(plNext, 79.121498, 90.220777, 73.051371, 95.202401)
plNext = AddPolyLine_Arc_XY(plNext, 66.668428, 99.776353, 60, 103.923048)
plNext = AddPolyLine_Arc_XY(plNext, 53.074643, 107.624729, 45.922012, 110.865544)
plNext = AddPolyLine_Arc_XY(plNext, 38.572736, 113.631616, 31.058285, 115.911099)
plNext = AddPolyLine_Arc_XY(plNext, 23.410839, 117.694234, 15.663143, 118.973383)
plNext = AddPolyLine_Arc_XY(plNext, 7.848376, 119.743071, 0, 120)
plNext = AddPolyLine_Arc_XY(plNext, -7.848376, 119.743071, -15.663143, 118.973383)
plNext = AddPolyLine_Arc_XY(plNext, -23.410839, 117.694234, -31.058285, 115.911099)
plNext = AddPolyLine_Arc_XY(plNext, -38.572736, 113.631616, -45.922012, 110.865544)
plNext = AddPolyLine_Arc_XY(plNext, -53.074643, 107.624729, -60, 103.923048)
plNext = AddPolyLine_Arc_XY(plNext, -66.668428, 99.776353, -73.051371, 95.202401)
plNext = AddPolyLine_Arc_XY(plNext, -79.121498, 90.220777, -84.852814, 84.852814)
plNext = AddPolyLine_Arc_XY(plNext, -90.220777, 79.121498, -95.202401, 73.051371)
plNext = AddPolyLine_Arc_XY(plNext, -99.776353, 66.668428, -103.923048, 60)
plNext = AddPolyLine_Arc_XY(plNext, -107.624729, 53.074643, -110.865544, 45.922012)
plNext = AddPolyLine_Arc_XY(plNext, -113.631616, 38.572736, -115.911099, 31.058285)
ClosePolyLine_Arc_XY(plNext, -117.694234, 23.410839, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(-77.859946, -2.958619)
plNext = AddPolyLine_Line_XY(plStart, -100.853864, -4.46572)
plNext = AddPolyLine_Line_XY(plNext, -100.713901, -6.601138)
plNext = AddPolyLine_Line_XY(plNext, -100.573938, -8.736556)
plNext = AddPolyLine_Line_XY(plNext, -77.580021, -7.229455)
plNext = AddPolyLine_Line_XY(plNext, -76.793526, -5.634601)
plNext = AddPolyLine_Line_XY(plNext, -75.596095, -5.556117)
plNext = AddPolyLine_Arc_XY(plNext, -75.405006, -7.728199, -75.15152, -9.893885)
plNext = AddPolyLine_Arc_XY(plNext, -74.835848, -12.051385, -74.458249, -14.198912)
plNext = AddPolyLine_Line_XY(plNext, -75.635192, -14.43302)
plNext = AddPolyLine_Line_XY(plNext, -76.807666, -13.09607)
plNext = AddPolyLine_Line_XY(plNext, -99.408152, -17.591586)
plNext = AddPolyLine_Line_XY(plNext, -98.990658, -19.690466)
plNext = AddPolyLine_Line_XY(plNext, -98.573165, -21.789347)
plNext = AddPolyLine_Line_XY(plNext, -75.972679, -17.293831)
plNext = AddPolyLine_Line_XY(plNext, -75.401083, -15.609963)
plNext = AddPolyLine_Line_XY(plNext, -74.224141, -15.375854)
plNext = AddPolyLine_Arc_XY(plNext, -73.751173, -17.504411, -73.217178, -19.618484)
plNext = AddPolyLine_Arc_XY(plNext, -72.622595, -21.716322, -71.967919, -23.79619)
plNext = AddPolyLine_Line_XY(plNext, -73.104235, -24.181917)
plNext = AddPolyLine_Line_XY(plNext, -74.441186, -23.009443)
plNext = AddPolyLine_Line_XY(plNext, -96.261538, -30.416455)
plNext = AddPolyLine_Line_XY(plNext, -95.573658, -32.442885)
plNext = AddPolyLine_Line_XY(plNext, -94.885778, -34.469316)
plNext = AddPolyLine_Line_XY(plNext, -73.065425, -27.062304)
plNext = AddPolyLine_Line_XY(plNext, -72.718508, -25.318234)
plNext = AddPolyLine_Line_XY(plNext, -71.582191, -24.932506)
plNext = AddPolyLine_Arc_XY(plNext, -70.835438, -26.981118, -70.030069, -29.007404)
plNext = AddPolyLine_Arc_XY(plNext, -69.16675, -31.009687, -68.246197, -32.986309)
plNext = AddPolyLine_Line_XY(plNext, -69.322445, -33.517055)
plNext = AddPolyLine_Line_XY(plNext, -70.800996, -32.529119)
plNext = AddPolyLine_Line_XY(plNext, -91.467864, -42.72089)
plNext = AddPolyLine_Line_XY(plNext, -90.521366, -44.640198)
plNext = AddPolyLine_Line_XY(plNext, -89.574868, -46.559505)
plNext = AddPolyLine_Line_XY(plNext, -68.908, -36.367734)
plNext = AddPolyLine_Line_XY(plNext, -68.791698, -34.593302)
plNext = AddPolyLine_Line_XY(plNext, -67.715451, -34.062556)
plNext = AddPolyLine_Arc_XY(plNext, -66.707688, -35.996171, -65.644726, -37.9)
plNext = AddPolyLine_Arc_XY(plNext, -64.527443, -39.772467, -63.356764, -41.612023)
plNext = AddPolyLine_Line_XY(plNext, -64.354528, -42.278707)
plNext = AddPolyLine_Line_XY(plNext, -65.949382, -41.492212)
plNext = AddPolyLine_Line_XY(plNext, -85.109148, -54.294359)
plNext = AddPolyLine_Line_XY(plNext, -83.920228, -56.073704)
plNext = AddPolyLine_Line_XY(plNext, -82.731308, -57.853049)
plNext = AddPolyLine_Line_XY(plNext, -63.571541, -45.050902)
plNext = AddPolyLine_Line_XY(plNext, -63.687844, -43.27647)
plNext = AddPolyLine_Line_XY(plNext, -62.69008, -42.609786)
plNext = AddPolyLine_Arc_XY(plNext, -61.438551, -44.39532, -60.136183, -46.144116)
plNext = AddPolyLine_Arc_XY(plNext, -58.784053, -47.854729, -57.383279, -49.525743)
plNext = AddPolyLine_Line_XY(plNext, -58.285487, -50.316958)
plNext = AddPolyLine_Line_XY(plNext, -59.969355, -49.745362)
plNext = AddPolyLine_Line_XY(plNext, -77.294192, -64.938836)
plNext = AddPolyLine_Line_XY(plNext, -75.883192, -66.547773)
plNext = AddPolyLine_Line_XY(plNext, -74.472192, -68.15671)
plNext = AddPolyLine_Line_XY(plNext, -57.147355, -52.963236)
plNext = AddPolyLine_Line_XY(plNext, -57.494272, -51.219166)
plNext = AddPolyLine_Line_XY(plNext, -56.592065, -50.427951)
plNext = AddPolyLine_Arc_XY(plNext, -55.118184, -52.034852, -53.598694, -53.598694)
plNext = AddPolyLine_Arc_XY(plNext, -52.034852, -55.118184, -50.427951, -56.592065)
plNext = AddPolyLine_Line_XY(plNext, -51.219166, -57.494272)
plNext = AddPolyLine_Line_XY(plNext, -52.963236, -57.147355)
plNext = AddPolyLine_Line_XY(plNext, -68.15671, -74.472192)
plNext = AddPolyLine_Line_XY(plNext, -66.547773, -75.883192)
plNext = AddPolyLine_Line_XY(plNext, -64.938836, -77.294192)
plNext = AddPolyLine_Line_XY(plNext, -49.745362, -59.969355)
plNext = AddPolyLine_Line_XY(plNext, -50.316958, -58.285487)
plNext = AddPolyLine_Line_XY(plNext, -49.525743, -57.383279)
plNext = AddPolyLine_Arc_XY(plNext, -47.854729, -58.784053, -46.144116, -60.136183)
plNext = AddPolyLine_Arc_XY(plNext, -44.39532, -61.438551, -42.609786, -62.69008)
plNext = AddPolyLine_Line_XY(plNext, -43.27647, -63.687844)
plNext = AddPolyLine_Line_XY(plNext, -45.050902, -63.571541)
plNext = AddPolyLine_Line_XY(plNext, -57.853049, -82.731308)
plNext = AddPolyLine_Line_XY(plNext, -56.073704, -83.920228)
plNext = AddPolyLine_Line_XY(plNext, -54.294359, -85.109148)
plNext = AddPolyLine_Line_XY(plNext, -41.492212, -65.949382)
plNext = AddPolyLine_Line_XY(plNext, -42.278707, -64.354528)
plNext = AddPolyLine_Line_XY(plNext, -41.612023, -63.356764)
plNext = AddPolyLine_Arc_XY(plNext, -39.772467, -64.527443, -37.9, -65.644726)
plNext = AddPolyLine_Arc_XY(plNext, -35.996171, -66.707688, -34.062556, -67.715451)
plNext = AddPolyLine_Line_XY(plNext, -34.593302, -68.791698)
plNext = AddPolyLine_Line_XY(plNext, -36.367734, -68.908)
plNext = AddPolyLine_Line_XY(plNext, -46.559505, -89.574868)
plNext = AddPolyLine_Line_XY(plNext, -44.640198, -90.521366)
plNext = AddPolyLine_Line_XY(plNext, -42.72089, -91.467864)
plNext = AddPolyLine_Line_XY(plNext, -32.529119, -70.800996)
plNext = AddPolyLine_Line_XY(plNext, -33.517055, -69.322445)
plNext = AddPolyLine_Line_XY(plNext, -32.986309, -68.246197)
plNext = AddPolyLine_Arc_XY(plNext, -31.009687, -69.16675, -29.007404, -70.030069)
plNext = AddPolyLine_Arc_XY(plNext, -26.981118, -70.835438, -24.932506, -71.582191)
plNext = AddPolyLine_Line_XY(plNext, -25.318234, -72.718508)
plNext = AddPolyLine_Line_XY(plNext, -27.062304, -73.065425)
plNext = AddPolyLine_Line_XY(plNext, -34.469316, -94.885778)
plNext = AddPolyLine_Line_XY(plNext, -32.442885, -95.573658)
plNext = AddPolyLine_Line_XY(plNext, -30.416455, -96.261538)
plNext = AddPolyLine_Line_XY(plNext, -23.009443, -74.441186)
plNext = AddPolyLine_Line_XY(plNext, -24.181917, -73.104235)
plNext = AddPolyLine_Line_XY(plNext, -23.79619, -71.967919)
plNext = AddPolyLine_Arc_XY(plNext, -21.716322, -72.622595, -19.618484, -73.217178)
plNext = AddPolyLine_Arc_XY(plNext, -17.504411, -73.751173, -15.375854, -74.224141)
plNext = AddPolyLine_Line_XY(plNext, -15.609963, -75.401083)
plNext = AddPolyLine_Line_XY(plNext, -17.293831, -75.972679)
plNext = AddPolyLine_Line_XY(plNext, -21.789347, -98.573165)
plNext = AddPolyLine_Line_XY(plNext, -19.690466, -98.990658)
plNext = AddPolyLine_Line_XY(plNext, -17.591586, -99.408152)
plNext = AddPolyLine_Line_XY(plNext, -13.09607, -76.807666)
plNext = AddPolyLine_Line_XY(plNext, -14.43302, -75.635192)
plNext = AddPolyLine_Line_XY(plNext, -14.198912, -74.458249)
plNext = AddPolyLine_Arc_XY(plNext, -12.051385, -74.835848, -9.893885, -75.15152)
plNext = AddPolyLine_Arc_XY(plNext, -7.728199, -75.405006, -5.556117, -75.596095)
plNext = AddPolyLine_Line_XY(plNext, -5.634601, -76.793526)
plNext = AddPolyLine_Line_XY(plNext, -7.229455, -77.580021)
plNext = AddPolyLine_Line_XY(plNext, -8.736556, -100.573938)
plNext = AddPolyLine_Line_XY(plNext, -6.601138, -100.713901)
plNext = AddPolyLine_Line_XY(plNext, -4.46572, -100.853864)
plNext = AddPolyLine_Line_XY(plNext, -2.958619, -77.859946)
plNext = AddPolyLine_Line_XY(plNext, -4.43717, -76.872009)
plNext = AddPolyLine_Line_XY(plNext, -4.358687, -75.674579)
plNext = AddPolyLine_Arc_XY(plNext, -2.180245, -75.768638, 0, -75.8)
plNext = AddPolyLine_Arc_XY(plNext, 2.180245, -75.768638, 4.358687, -75.674579)
plNext = AddPolyLine_Line_XY(plNext, 4.43717, -76.872009)
plNext = AddPolyLine_Line_XY(plNext, 2.958619, -77.859946)
plNext = AddPolyLine_Line_XY(plNext, 4.46572, -100.853864)
plNext = AddPolyLine_Line_XY(plNext, 6.601138, -100.713901)
plNext = AddPolyLine_Line_XY(plNext, 8.736556, -100.573938)
plNext = AddPolyLine_Line_XY(plNext, 7.229455, -77.580021)
plNext = AddPolyLine_Line_XY(plNext, 5.634601, -76.793526)
plNext = AddPolyLine_Line_XY(plNext, 5.556117, -75.596095)
plNext = AddPolyLine_Arc_XY(plNext, 7.728199, -75.405006, 9.893885, -75.15152)
plNext = AddPolyLine_Arc_XY(plNext, 12.051385, -74.835848, 14.198912, -74.458249)
plNext = AddPolyLine_Line_XY(plNext, 14.43302, -75.635192)
plNext = AddPolyLine_Line_XY(plNext, 13.09607, -76.807666)
plNext = AddPolyLine_Line_XY(plNext, 17.591586, -99.408152)
plNext = AddPolyLine_Line_XY(plNext, 19.690466, -98.990658)
plNext = AddPolyLine_Line_XY(plNext, 21.789347, -98.573165)
plNext = AddPolyLine_Line_XY(plNext, 17.293831, -75.972679)
plNext = AddPolyLine_Line_XY(plNext, 15.609963, -75.401083)
plNext = AddPolyLine_Line_XY(plNext, 15.375854, -74.224141)
plNext = AddPolyLine_Arc_XY(plNext, 17.504411, -73.751173, 19.618484, -73.217178)
plNext = AddPolyLine_Arc_XY(plNext, 21.716322, -72.622595, 23.79619, -71.967919)
plNext = AddPolyLine_Line_XY(plNext, 24.181917, -73.104235)
plNext = AddPolyLine_Line_XY(plNext, 23.009443, -74.441186)
plNext = AddPolyLine_Line_XY(plNext, 30.416455, -96.261538)
plNext = AddPolyLine_Line_XY(plNext, 32.442885, -95.573658)
plNext = AddPolyLine_Line_XY(plNext, 34.469316, -94.885778)
plNext = AddPolyLine_Line_XY(plNext, 27.062304, -73.065425)
plNext = AddPolyLine_Line_XY(plNext, 25.318234, -72.718508)
plNext = AddPolyLine_Line_XY(plNext, 24.932506, -71.582191)
plNext = AddPolyLine_Arc_XY(plNext, 26.981118, -70.835438, 29.007404, -70.030069)
plNext = AddPolyLine_Arc_XY(plNext, 31.009687, -69.16675, 32.986309, -68.246197)
plNext = AddPolyLine_Line_XY(plNext, 33.517055, -69.322445)
plNext = AddPolyLine_Line_XY(plNext, 32.529119, -70.800996)
plNext = AddPolyLine_Line_XY(plNext, 42.72089, -91.467864)
plNext = AddPolyLine_Line_XY(plNext, 44.640198, -90.521366)
plNext = AddPolyLine_Line_XY(plNext, 46.559505, -89.574868)
plNext = AddPolyLine_Line_XY(plNext, 36.367734, -68.908)
plNext = AddPolyLine_Line_XY(plNext, 34.593302, -68.791698)
plNext = AddPolyLine_Line_XY(plNext, 34.062556, -67.715451)
plNext = AddPolyLine_Arc_XY(plNext, 35.996171, -66.707688, 37.9, -65.644726)
plNext = AddPolyLine_Arc_XY(plNext, 39.772467, -64.527443, 41.612023, -63.356764)
plNext = AddPolyLine_Line_XY(plNext, 42.278707, -64.354528)
plNext = AddPolyLine_Line_XY(plNext, 41.492212, -65.949382)
plNext = AddPolyLine_Line_XY(plNext, 54.294359, -85.109148)
plNext = AddPolyLine_Line_XY(plNext, 56.073704, -83.920228)
plNext = AddPolyLine_Line_XY(plNext, 57.853049, -82.731308)
plNext = AddPolyLine_Line_XY(plNext, 45.050902, -63.571541)
plNext = AddPolyLine_Line_XY(plNext, 43.27647, -63.687844)
plNext = AddPolyLine_Line_XY(plNext, 42.609786, -62.69008)
plNext = AddPolyLine_Arc_XY(plNext, 44.39532, -61.438551, 46.144116, -60.136183)
plNext = AddPolyLine_Arc_XY(plNext, 47.854729, -58.784053, 49.525743, -57.383279)
plNext = AddPolyLine_Line_XY(plNext, 50.316958, -58.285487)
plNext = AddPolyLine_Line_XY(plNext, 49.745362, -59.969355)
plNext = AddPolyLine_Line_XY(plNext, 64.938836, -77.294192)
plNext = AddPolyLine_Line_XY(plNext, 66.547773, -75.883192)
plNext = AddPolyLine_Line_XY(plNext, 68.15671, -74.472192)
plNext = AddPolyLine_Line_XY(plNext, 52.963236, -57.147355)
plNext = AddPolyLine_Line_XY(plNext, 51.219166, -57.494272)
plNext = AddPolyLine_Line_XY(plNext, 50.427951, -56.592065)
plNext = AddPolyLine_Arc_XY(plNext, 52.034852, -55.118184, 53.598694, -53.598694)
plNext = AddPolyLine_Arc_XY(plNext, 55.118184, -52.034852, 56.592065, -50.427951)
plNext = AddPolyLine_Line_XY(plNext, 57.494272, -51.219166)
plNext = AddPolyLine_Line_XY(plNext, 57.147355, -52.963236)
plNext = AddPolyLine_Line_XY(plNext, 74.472192, -68.15671)
plNext = AddPolyLine_Line_XY(plNext, 75.883192, -66.547773)
plNext = AddPolyLine_Line_XY(plNext, 77.294192, -64.938836)
plNext = AddPolyLine_Line_XY(plNext, 59.969355, -49.745362)
plNext = AddPolyLine_Line_XY(plNext, 58.285487, -50.316958)
plNext = AddPolyLine_Line_XY(plNext, 57.383279, -49.525743)
plNext = AddPolyLine_Arc_XY(plNext, 58.784053, -47.854729, 60.136183, -46.144116)
plNext = AddPolyLine_Arc_XY(plNext, 61.438551, -44.39532, 62.69008, -42.609786)
plNext = AddPolyLine_Line_XY(plNext, 63.687844, -43.27647)
plNext = AddPolyLine_Line_XY(plNext, 63.571541, -45.050902)
plNext = AddPolyLine_Line_XY(plNext, 82.731308, -57.853049)
plNext = AddPolyLine_Line_XY(plNext, 83.920228, -56.073704)
plNext = AddPolyLine_Line_XY(plNext, 85.109148, -54.294359)
plNext = AddPolyLine_Line_XY(plNext, 65.949382, -41.492212)
plNext = AddPolyLine_Line_XY(plNext, 64.354528, -42.278707)
plNext = AddPolyLine_Line_XY(plNext, 63.356764, -41.612023)
plNext = AddPolyLine_Arc_XY(plNext, 64.527443, -39.772467, 65.644726, -37.9)
plNext = AddPolyLine_Arc_XY(plNext, 66.707688, -35.996171, 67.715451, -34.062556)
plNext = AddPolyLine_Line_XY(plNext, 68.791698, -34.593302)
plNext = AddPolyLine_Line_XY(plNext, 68.908, -36.367734)
plNext = AddPolyLine_Line_XY(plNext, 89.574868, -46.559505)
plNext = AddPolyLine_Line_XY(plNext, 90.521366, -44.640198)
plNext = AddPolyLine_Line_XY(plNext, 91.467864, -42.72089)
plNext = AddPolyLine_Line_XY(plNext, 70.800996, -32.529119)
plNext = AddPolyLine_Line_XY(plNext, 69.322445, -33.517055)
plNext = AddPolyLine_Line_XY(plNext, 68.246197, -32.986309)
plNext = AddPolyLine_Arc_XY(plNext, 69.16675, -31.009687, 70.030069, -29.007404)
plNext = AddPolyLine_Arc_XY(plNext, 70.835438, -26.981118, 71.582191, -24.932506)
plNext = AddPolyLine_Line_XY(plNext, 72.718508, -25.318234)
plNext = AddPolyLine_Line_XY(plNext, 73.065425, -27.062304)
plNext = AddPolyLine_Line_XY(plNext, 94.885778, -34.469316)
plNext = AddPolyLine_Line_XY(plNext, 95.573658, -32.442885)
plNext = AddPolyLine_Line_XY(plNext, 96.261538, -30.416455)
plNext = AddPolyLine_Line_XY(plNext, 74.441186, -23.009443)
plNext = AddPolyLine_Line_XY(plNext, 73.104235, -24.181917)
plNext = AddPolyLine_Line_XY(plNext, 71.967919, -23.79619)
plNext = AddPolyLine_Arc_XY(plNext, 72.622595, -21.716322, 73.217178, -19.618484)
plNext = AddPolyLine_Arc_XY(plNext, 73.751173, -17.504411, 74.224141, -15.375854)
plNext = AddPolyLine_Line_XY(plNext, 75.401083, -15.609963)
plNext = AddPolyLine_Line_XY(plNext, 75.972679, -17.293831)
plNext = AddPolyLine_Line_XY(plNext, 98.573165, -21.789347)
plNext = AddPolyLine_Line_XY(plNext, 98.990658, -19.690466)
plNext = AddPolyLine_Line_XY(plNext, 99.408152, -17.591586)
plNext = AddPolyLine_Line_XY(plNext, 76.807666, -13.09607)
plNext = AddPolyLine_Line_XY(plNext, 75.635192, -14.43302)
plNext = AddPolyLine_Line_XY(plNext, 74.458249, -14.198912)
plNext = AddPolyLine_Arc_XY(plNext, 74.835848, -12.051385, 75.15152, -9.893885)
plNext = AddPolyLine_Arc_XY(plNext, 75.405006, -7.728199, 75.596095, -5.556117)
plNext = AddPolyLine_Line_XY(plNext, 76.793526, -5.634601)
plNext = AddPolyLine_Line_XY(plNext, 77.580021, -7.229455)
plNext = AddPolyLine_Line_XY(plNext, 100.573938, -8.736556)
plNext = AddPolyLine_Line_XY(plNext, 100.713901, -6.601138)
plNext = AddPolyLine_Line_XY(plNext, 100.853864, -4.46572)
plNext = AddPolyLine_Line_XY(plNext, 77.859946, -2.958619)
plNext = AddPolyLine_Line_XY(plNext, 76.872009, -4.43717)
plNext = AddPolyLine_Line_XY(plNext, 75.674579, -4.358687)
plNext = AddPolyLine_Arc_XY(plNext, 75.768638, -2.180245, 75.8, 0)
plNext = AddPolyLine_Arc_XY(plNext, 75.768638, 2.180245, 75.674579, 4.358687)
plNext = AddPolyLine_Line_XY(plNext, 76.872009, 4.43717)
plNext = AddPolyLine_Line_XY(plNext, 77.859946, 2.958619)
plNext = AddPolyLine_Line_XY(plNext, 100.853864, 4.46572)
plNext = AddPolyLine_Line_XY(plNext, 100.713901, 6.601138)
plNext = AddPolyLine_Line_XY(plNext, 100.573938, 8.736556)
plNext = AddPolyLine_Line_XY(plNext, 77.580021, 7.229455)
plNext = AddPolyLine_Line_XY(plNext, 76.793526, 5.634601)
plNext = AddPolyLine_Line_XY(plNext, 75.596095, 5.556117)
plNext = AddPolyLine_Arc_XY(plNext, 75.405006, 7.728199, 75.15152, 9.893885)
plNext = AddPolyLine_Arc_XY(plNext, 74.835848, 12.051385, 74.458249, 14.198912)
plNext = AddPolyLine_Line_XY(plNext, 75.635192, 14.43302)
plNext = AddPolyLine_Line_XY(plNext, 76.807666, 13.09607)
plNext = AddPolyLine_Line_XY(plNext, 99.408152, 17.591586)
plNext = AddPolyLine_Line_XY(plNext, 98.990658, 19.690466)
plNext = AddPolyLine_Line_XY(plNext, 98.573165, 21.789347)
plNext = AddPolyLine_Line_XY(plNext, 75.972679, 17.293831)
plNext = AddPolyLine_Line_XY(plNext, 75.401083, 15.609963)
plNext = AddPolyLine_Line_XY(plNext, 74.224141, 15.375854)
plNext = AddPolyLine_Arc_XY(plNext, 73.751173, 17.504411, 73.217178, 19.618484)
plNext = AddPolyLine_Arc_XY(plNext, 72.622595, 21.716322, 71.967919, 23.79619)
plNext = AddPolyLine_Line_XY(plNext, 73.104235, 24.181917)
plNext = AddPolyLine_Line_XY(plNext, 74.441186, 23.009443)
plNext = AddPolyLine_Line_XY(plNext, 96.261538, 30.416455)
plNext = AddPolyLine_Line_XY(plNext, 95.573658, 32.442885)
plNext = AddPolyLine_Line_XY(plNext, 94.885778, 34.469316)
plNext = AddPolyLine_Line_XY(plNext, 73.065425, 27.062304)
plNext = AddPolyLine_Line_XY(plNext, 72.718508, 25.318234)
plNext = AddPolyLine_Line_XY(plNext, 71.582191, 24.932506)
plNext = AddPolyLine_Arc_XY(plNext, 70.835438, 26.981118, 70.030069, 29.007404)
plNext = AddPolyLine_Arc_XY(plNext, 69.16675, 31.009687, 68.246197, 32.986309)
plNext = AddPolyLine_Line_XY(plNext, 69.322445, 33.517055)
plNext = AddPolyLine_Line_XY(plNext, 70.800996, 32.529119)
plNext = AddPolyLine_Line_XY(plNext, 91.467864, 42.72089)
plNext = AddPolyLine_Line_XY(plNext, 90.521366, 44.640198)
plNext = AddPolyLine_Line_XY(plNext, 89.574868, 46.559505)
plNext = AddPolyLine_Line_XY(plNext, 68.908, 36.367734)
plNext = AddPolyLine_Line_XY(plNext, 68.791698, 34.593302)
plNext = AddPolyLine_Line_XY(plNext, 67.715451, 34.062556)
plNext = AddPolyLine_Arc_XY(plNext, 66.707688, 35.996171, 65.644726, 37.9)
plNext = AddPolyLine_Arc_XY(plNext, 64.527443, 39.772467, 63.356764, 41.612023)
plNext = AddPolyLine_Line_XY(plNext, 64.354528, 42.278707)
plNext = AddPolyLine_Line_XY(plNext, 65.949382, 41.492212)
plNext = AddPolyLine_Line_XY(plNext, 85.109148, 54.294359)
plNext = AddPolyLine_Line_XY(plNext, 83.920228, 56.073704)
plNext = AddPolyLine_Line_XY(plNext, 82.731308, 57.853049)
plNext = AddPolyLine_Line_XY(plNext, 63.571541, 45.050902)
plNext = AddPolyLine_Line_XY(plNext, 63.687844, 43.27647)
plNext = AddPolyLine_Line_XY(plNext, 62.69008, 42.609786)
plNext = AddPolyLine_Arc_XY(plNext, 61.438551, 44.39532, 60.136183, 46.144116)
plNext = AddPolyLine_Arc_XY(plNext, 58.784053, 47.854729, 57.383279, 49.525743)
plNext = AddPolyLine_Line_XY(plNext, 58.285487, 50.316958)
plNext = AddPolyLine_Line_XY(plNext, 59.969355, 49.745362)
plNext = AddPolyLine_Line_XY(plNext, 77.294192, 64.938836)
plNext = AddPolyLine_Line_XY(plNext, 75.883192, 66.547773)
plNext = AddPolyLine_Line_XY(plNext, 74.472192, 68.15671)
plNext = AddPolyLine_Line_XY(plNext, 57.147355, 52.963236)
plNext = AddPolyLine_Line_XY(plNext, 57.494272, 51.219166)
plNext = AddPolyLine_Line_XY(plNext, 56.592065, 50.427951)
plNext = AddPolyLine_Arc_XY(plNext, 55.118184, 52.034852, 53.598694, 53.598694)
plNext = AddPolyLine_Arc_XY(plNext, 52.034852, 55.118184, 50.427951, 56.592065)
plNext = AddPolyLine_Line_XY(plNext, 51.219166, 57.494272)
plNext = AddPolyLine_Line_XY(plNext, 52.963236, 57.147355)
plNext = AddPolyLine_Line_XY(plNext, 68.15671, 74.472192)
plNext = AddPolyLine_Line_XY(plNext, 66.547773, 75.883192)
plNext = AddPolyLine_Line_XY(plNext, 64.938836, 77.294192)
plNext = AddPolyLine_Line_XY(plNext, 49.745362, 59.969355)
plNext = AddPolyLine_Line_XY(plNext, 50.316958, 58.285487)
plNext = AddPolyLine_Line_XY(plNext, 49.525743, 57.383279)
plNext = AddPolyLine_Arc_XY(plNext, 47.854729, 58.784053, 46.144116, 60.136183)
plNext = AddPolyLine_Arc_XY(plNext, 44.39532, 61.438551, 42.609786, 62.69008)
plNext = AddPolyLine_Line_XY(plNext, 43.27647, 63.687844)
plNext = AddPolyLine_Line_XY(plNext, 45.050902, 63.571541)
plNext = AddPolyLine_Line_XY(plNext, 57.853049, 82.731308)
plNext = AddPolyLine_Line_XY(plNext, 56.073704, 83.920228)
plNext = AddPolyLine_Line_XY(plNext, 54.294359, 85.109148)
plNext = AddPolyLine_Line_XY(plNext, 41.492212, 65.949382)
plNext = AddPolyLine_Line_XY(plNext, 42.278707, 64.354528)
plNext = AddPolyLine_Line_XY(plNext, 41.612023, 63.356764)
plNext = AddPolyLine_Arc_XY(plNext, 39.772467, 64.527443, 37.9, 65.644726)
plNext = AddPolyLine_Arc_XY(plNext, 35.996171, 66.707688, 34.062556, 67.715451)
plNext = AddPolyLine_Line_XY(plNext, 34.593302, 68.791698)
plNext = AddPolyLine_Line_XY(plNext, 36.367734, 68.908)
plNext = AddPolyLine_Line_XY(plNext, 46.559505, 89.574868)
plNext = AddPolyLine_Line_XY(plNext, 44.640198, 90.521366)
plNext = AddPolyLine_Line_XY(plNext, 42.72089, 91.467864)
plNext = AddPolyLine_Line_XY(plNext, 32.529119, 70.800996)
plNext = AddPolyLine_Line_XY(plNext, 33.517055, 69.322445)
plNext = AddPolyLine_Line_XY(plNext, 32.986309, 68.246197)
plNext = AddPolyLine_Arc_XY(plNext, 31.009687, 69.16675, 29.007404, 70.030069)
plNext = AddPolyLine_Arc_XY(plNext, 26.981118, 70.835438, 24.932506, 71.582191)
plNext = AddPolyLine_Line_XY(plNext, 25.318234, 72.718508)
plNext = AddPolyLine_Line_XY(plNext, 27.062304, 73.065425)
plNext = AddPolyLine_Line_XY(plNext, 34.469316, 94.885778)
plNext = AddPolyLine_Line_XY(plNext, 32.442885, 95.573658)
plNext = AddPolyLine_Line_XY(plNext, 30.416455, 96.261538)
plNext = AddPolyLine_Line_XY(plNext, 23.009443, 74.441186)
plNext = AddPolyLine_Line_XY(plNext, 24.181917, 73.104235)
plNext = AddPolyLine_Line_XY(plNext, 23.79619, 71.967919)
plNext = AddPolyLine_Arc_XY(plNext, 21.716322, 72.622595, 19.618484, 73.217178)
plNext = AddPolyLine_Arc_XY(plNext, 17.504411, 73.751173, 15.375854, 74.224141)
plNext = AddPolyLine_Line_XY(plNext, 15.609963, 75.401083)
plNext = AddPolyLine_Line_XY(plNext, 17.293831, 75.972679)
plNext = AddPolyLine_Line_XY(plNext, 21.789347, 98.573165)
plNext = AddPolyLine_Line_XY(plNext, 19.690466, 98.990658)
plNext = AddPolyLine_Line_XY(plNext, 17.591586, 99.408152)
plNext = AddPolyLine_Line_XY(plNext, 13.09607, 76.807666)
plNext = AddPolyLine_Line_XY(plNext, 14.43302, 75.635192)
plNext = AddPolyLine_Line_XY(plNext, 14.198912, 74.458249)
plNext = AddPolyLine_Arc_XY(plNext, 12.051385, 74.835848, 9.893885, 75.15152)
plNext = AddPolyLine_Arc_XY(plNext, 7.728199, 75.405006, 5.556117, 75.596095)
plNext = AddPolyLine_Line_XY(plNext, 5.634601, 76.793526)
plNext = AddPolyLine_Line_XY(plNext, 7.229455, 77.580021)
plNext = AddPolyLine_Line_XY(plNext, 8.736556, 100.573938)
plNext = AddPolyLine_Line_XY(plNext, 6.601138, 100.713901)
plNext = AddPolyLine_Line_XY(plNext, 4.46572, 100.853864)
plNext = AddPolyLine_Line_XY(plNext, 2.958619, 77.859946)
plNext = AddPolyLine_Line_XY(plNext, 4.43717, 76.872009)
plNext = AddPolyLine_Line_XY(plNext, 4.358687, 75.674579)
plNext = AddPolyLine_Arc_XY(plNext, 2.180245, 75.768638, 0, 75.8)
plNext = AddPolyLine_Arc_XY(plNext, -2.180245, 75.768638, -4.358687, 75.674579)
plNext = AddPolyLine_Line_XY(plNext, -4.43717, 76.872009)
plNext = AddPolyLine_Line_XY(plNext, -2.958619, 77.859946)
plNext = AddPolyLine_Line_XY(plNext, -4.46572, 100.853864)
plNext = AddPolyLine_Line_XY(plNext, -6.601138, 100.713901)
plNext = AddPolyLine_Line_XY(plNext, -8.736556, 100.573938)
plNext = AddPolyLine_Line_XY(plNext, -7.229455, 77.580021)
plNext = AddPolyLine_Line_XY(plNext, -5.634601, 76.793526)
plNext = AddPolyLine_Line_XY(plNext, -5.556117, 75.596095)
plNext = AddPolyLine_Arc_XY(plNext, -7.728199, 75.405006, -9.893885, 75.15152)
plNext = AddPolyLine_Arc_XY(plNext, -12.051385, 74.835848, -14.198912, 74.458249)
plNext = AddPolyLine_Line_XY(plNext, -14.43302, 75.635192)
plNext = AddPolyLine_Line_XY(plNext, -13.09607, 76.807666)
plNext = AddPolyLine_Line_XY(plNext, -17.591586, 99.408152)
plNext = AddPolyLine_Line_XY(plNext, -19.690466, 98.990658)
plNext = AddPolyLine_Line_XY(plNext, -21.789347, 98.573165)
plNext = AddPolyLine_Line_XY(plNext, -17.293831, 75.972679)
plNext = AddPolyLine_Line_XY(plNext, -15.609963, 75.401083)
plNext = AddPolyLine_Line_XY(plNext, -15.375854, 74.224141)
plNext = AddPolyLine_Arc_XY(plNext, -17.504411, 73.751173, -19.618484, 73.217178)
plNext = AddPolyLine_Arc_XY(plNext, -21.716322, 72.622595, -23.79619, 71.967919)
plNext = AddPolyLine_Line_XY(plNext, -24.181917, 73.104235)
plNext = AddPolyLine_Line_XY(plNext, -23.009443, 74.441186)
plNext = AddPolyLine_Line_XY(plNext, -30.416455, 96.261538)
plNext = AddPolyLine_Line_XY(plNext, -32.442885, 95.573658)
plNext = AddPolyLine_Line_XY(plNext, -34.469316, 94.885778)
plNext = AddPolyLine_Line_XY(plNext, -27.062304, 73.065425)
plNext = AddPolyLine_Line_XY(plNext, -25.318234, 72.718508)
plNext = AddPolyLine_Line_XY(plNext, -24.932506, 71.582191)
plNext = AddPolyLine_Arc_XY(plNext, -26.981118, 70.835438, -29.007404, 70.030069)
plNext = AddPolyLine_Arc_XY(plNext, -31.009687, 69.16675, -32.986309, 68.246197)
plNext = AddPolyLine_Line_XY(plNext, -33.517055, 69.322445)
plNext = AddPolyLine_Line_XY(plNext, -32.529119, 70.800996)
plNext = AddPolyLine_Line_XY(plNext, -42.72089, 91.467864)
plNext = AddPolyLine_Line_XY(plNext, -44.640198, 90.521366)
plNext = AddPolyLine_Line_XY(plNext, -46.559505, 89.574868)
plNext = AddPolyLine_Line_XY(plNext, -36.367734, 68.908)
plNext = AddPolyLine_Line_XY(plNext, -34.593302, 68.791698)
plNext = AddPolyLine_Line_XY(plNext, -34.062556, 67.715451)
plNext = AddPolyLine_Arc_XY(plNext, -35.996171, 66.707688, -37.9, 65.644726)
plNext = AddPolyLine_Arc_XY(plNext, -39.772467, 64.527443, -41.612023, 63.356764)
plNext = AddPolyLine_Line_XY(plNext, -42.278707, 64.354528)
plNext = AddPolyLine_Line_XY(plNext, -41.492212, 65.949382)
plNext = AddPolyLine_Line_XY(plNext, -54.294359, 85.109148)
plNext = AddPolyLine_Line_XY(plNext, -56.073704, 83.920228)
plNext = AddPolyLine_Line_XY(plNext, -57.853049, 82.731308)
plNext = AddPolyLine_Line_XY(plNext, -45.050902, 63.571541)
plNext = AddPolyLine_Line_XY(plNext, -43.27647, 63.687844)
plNext = AddPolyLine_Line_XY(plNext, -42.609786, 62.69008)
plNext = AddPolyLine_Arc_XY(plNext, -44.39532, 61.438551, -46.144116, 60.136183)
plNext = AddPolyLine_Arc_XY(plNext, -47.854729, 58.784053, -49.525743, 57.383279)
plNext = AddPolyLine_Line_XY(plNext, -50.316958, 58.285487)
plNext = AddPolyLine_Line_XY(plNext, -49.745362, 59.969355)
plNext = AddPolyLine_Line_XY(plNext, -64.938836, 77.294192)
plNext = AddPolyLine_Line_XY(plNext, -66.547773, 75.883192)
plNext = AddPolyLine_Line_XY(plNext, -68.15671, 74.472192)
plNext = AddPolyLine_Line_XY(plNext, -52.963236, 57.147355)
plNext = AddPolyLine_Line_XY(plNext, -51.219166, 57.494272)
plNext = AddPolyLine_Line_XY(plNext, -50.427951, 56.592065)
plNext = AddPolyLine_Arc_XY(plNext, -52.034852, 55.118184, -53.598694, 53.598694)
plNext = AddPolyLine_Arc_XY(plNext, -55.118184, 52.034852, -56.592065, 50.427951)
plNext = AddPolyLine_Line_XY(plNext, -57.494272, 51.219166)
plNext = AddPolyLine_Line_XY(plNext, -57.147355, 52.963236)
plNext = AddPolyLine_Line_XY(plNext, -74.472192, 68.15671)
plNext = AddPolyLine_Line_XY(plNext, -75.883192, 66.547773)
plNext = AddPolyLine_Line_XY(plNext, -77.294192, 64.938836)
plNext = AddPolyLine_Line_XY(plNext, -59.969355, 49.745362)
plNext = AddPolyLine_Line_XY(plNext, -58.285487, 50.316958)
plNext = AddPolyLine_Line_XY(plNext, -57.383279, 49.525743)
plNext = AddPolyLine_Arc_XY(plNext, -58.784053, 47.854729, -60.136183, 46.144116)
plNext = AddPolyLine_Arc_XY(plNext, -61.438551, 44.39532, -62.69008, 42.609786)
plNext = AddPolyLine_Line_XY(plNext, -63.687844, 43.27647)
plNext = AddPolyLine_Line_XY(plNext, -63.571541, 45.050902)
plNext = AddPolyLine_Line_XY(plNext, -82.731308, 57.853049)
plNext = AddPolyLine_Line_XY(plNext, -83.920228, 56.073704)
plNext = AddPolyLine_Line_XY(plNext, -85.109148, 54.294359)
plNext = AddPolyLine_Line_XY(plNext, -65.949382, 41.492212)
plNext = AddPolyLine_Line_XY(plNext, -64.354528, 42.278707)
plNext = AddPolyLine_Line_XY(plNext, -63.356764, 41.612023)
plNext = AddPolyLine_Arc_XY(plNext, -64.527443, 39.772467, -65.644726, 37.9)
plNext = AddPolyLine_Arc_XY(plNext, -66.707688, 35.996171, -67.715451, 34.062556)
plNext = AddPolyLine_Line_XY(plNext, -68.791698, 34.593302)
plNext = AddPolyLine_Line_XY(plNext, -68.908, 36.367734)
plNext = AddPolyLine_Line_XY(plNext, -89.574868, 46.559505)
plNext = AddPolyLine_Line_XY(plNext, -90.521366, 44.640198)
plNext = AddPolyLine_Line_XY(plNext, -91.467864, 42.72089)
plNext = AddPolyLine_Line_XY(plNext, -70.800996, 32.529119)
plNext = AddPolyLine_Line_XY(plNext, -69.322445, 33.517055)
plNext = AddPolyLine_Line_XY(plNext, -68.246197, 32.986309)
plNext = AddPolyLine_Arc_XY(plNext, -69.16675, 31.009687, -70.030069, 29.007404)
plNext = AddPolyLine_Arc_XY(plNext, -70.835438, 26.981118, -71.582191, 24.932506)
plNext = AddPolyLine_Line_XY(plNext, -72.718508, 25.318234)
plNext = AddPolyLine_Line_XY(plNext, -73.065425, 27.062304)
plNext = AddPolyLine_Line_XY(plNext, -94.885778, 34.469316)
plNext = AddPolyLine_Line_XY(plNext, -95.573658, 32.442885)
plNext = AddPolyLine_Line_XY(plNext, -96.261538, 30.416455)
plNext = AddPolyLine_Line_XY(plNext, -74.441186, 23.009443)
plNext = AddPolyLine_Line_XY(plNext, -73.104235, 24.181917)
plNext = AddPolyLine_Line_XY(plNext, -71.967919, 23.79619)
plNext = AddPolyLine_Arc_XY(plNext, -72.622595, 21.716322, -73.217178, 19.618484)
plNext = AddPolyLine_Arc_XY(plNext, -73.751173, 17.504411, -74.224141, 15.375854)
plNext = AddPolyLine_Line_XY(plNext, -75.401083, 15.609963)
plNext = AddPolyLine_Line_XY(plNext, -75.972679, 17.293831)
plNext = AddPolyLine_Line_XY(plNext, -98.573165, 21.789347)
plNext = AddPolyLine_Line_XY(plNext, -98.990658, 19.690466)
plNext = AddPolyLine_Line_XY(plNext, -99.408152, 17.591586)
plNext = AddPolyLine_Line_XY(plNext, -76.807666, 13.09607)
plNext = AddPolyLine_Line_XY(plNext, -75.635192, 14.43302)
plNext = AddPolyLine_Line_XY(plNext, -74.458249, 14.198912)
plNext = AddPolyLine_Arc_XY(plNext, -74.835848, 12.051385, -75.15152, 9.893885)
plNext = AddPolyLine_Arc_XY(plNext, -75.405006, 7.728199, -75.596095, 5.556117)
plNext = AddPolyLine_Line_XY(plNext, -76.793526, 5.634601)
plNext = AddPolyLine_Line_XY(plNext, -77.580021, 7.229455)
plNext = AddPolyLine_Line_XY(plNext, -100.573938, 8.736556)
plNext = AddPolyLine_Line_XY(plNext, -100.713901, 6.601138)
plNext = AddPolyLine_Line_XY(plNext, -100.853864, 4.46572)
plNext = AddPolyLine_Line_XY(plNext, -77.859946, 2.958619)
plNext = AddPolyLine_Line_XY(plNext, -76.872009, 4.43717)
plNext = AddPolyLine_Line_XY(plNext, -75.674579, 4.358687)
plNext = AddPolyLine_Arc_XY(plNext, -75.768638, 2.180245, -75.8, 0)
plNext = AddPolyLine_Arc_XY(plNext, -75.768638, -2.180245, -75.674579, -4.358687)
plNext = AddPolyLine_Line_XY(plNext, -76.872009, -4.43717)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 2 PolyLine

# End of component stator_lamination


# Create new component armature_winding_active_h1
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h1", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(80.734186, 3.147006)
plNext = AddPolyLine_Line_XY(plStart, 80.45426, 7.417843)
plNext = AddPolyLine_Line_XY(plNext, 77.580021, 7.229455)
plNext = AddPolyLine_Line_XY(plNext, 77.859946, 2.958619)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h1


# Create new component armature_winding_active_a1
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a1", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(97.979624, 4.277332)
plNext = AddPolyLine_Line_XY(plStart, 100.853864, 4.46572)
plNext = AddPolyLine_Line_XY(plNext, 100.713901, 6.601138)
plNext = AddPolyLine_Line_XY(plNext, 100.573938, 8.736556)
plNext = AddPolyLine_Line_XY(plNext, 97.699699, 8.548168)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a1


# Create new component armature_winding_active_b1
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b1", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(95.105384, 4.088944)
plNext = AddPolyLine_Line_XY(plStart, 97.979624, 4.277332)
plNext = AddPolyLine_Line_XY(plNext, 97.699699, 8.548168)
plNext = AddPolyLine_Line_XY(plNext, 94.825459, 8.359781)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b1


# Create new component armature_winding_active_c1
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c1", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(92.231145, 3.900557)
plNext = AddPolyLine_Line_XY(plStart, 95.105384, 4.088944)
plNext = AddPolyLine_Line_XY(plNext, 94.825459, 8.359781)
plNext = AddPolyLine_Line_XY(plNext, 91.951219, 8.171393)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c1


# Create new component armature_winding_active_d1
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d1", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(89.356905, 3.712169)
plNext = AddPolyLine_Line_XY(plStart, 92.231145, 3.900557)
plNext = AddPolyLine_Line_XY(plNext, 91.951219, 8.171393)
plNext = AddPolyLine_Line_XY(plNext, 89.076979, 7.983005)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d1


# Create new component armature_winding_active_e1
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e1", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(86.482665, 3.523782)
plNext = AddPolyLine_Line_XY(plStart, 89.356905, 3.712169)
plNext = AddPolyLine_Line_XY(plNext, 89.076979, 7.983005)
plNext = AddPolyLine_Line_XY(plNext, 86.20274, 7.794618)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e1


# Create new component armature_winding_active_f1
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f1", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(83.608425, 3.335394)
plNext = AddPolyLine_Line_XY(plStart, 86.482665, 3.523782)
plNext = AddPolyLine_Line_XY(plNext, 86.20274, 7.794618)
plNext = AddPolyLine_Line_XY(plNext, 83.3285, 7.60623)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f1


# Create new component armature_winding_active_g1
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g1", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(80.734186, 3.147006)
plNext = AddPolyLine_Line_XY(plStart, 83.608425, 3.335394)
plNext = AddPolyLine_Line_XY(plNext, 83.3285, 7.60623)
plNext = AddPolyLine_Line_XY(plNext, 80.45426, 7.417843)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g1


# Create new component statorwedge
newComp = CreateNamedComponentWithColour_Radial("statorwedge", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-76.872009, 4.43717)
plNext = AddPolyLine_Line_XY(plStart, -76.793526, 5.634601)
plNext = AddPolyLine_Line_XY(plNext, -77.580021, 7.229455)
plNext = AddPolyLine_Line_XY(plNext, -77.859946, 2.958619)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge


# Create new component rotor_lamination
newComp = CreateNamedComponentWithColour_Radial("rotor_lamination", -54.5, -96, 127, 247, 247, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-75, 0)
plNext = AddPolyLine_Arc_XY(plStart, -69.290965, -28.701257, -53.033009, -53.033009)
plNext = AddPolyLine_Arc_XY(plNext, -28.701257, -69.290965, 0, -75)
plNext = AddPolyLine_Arc_XY(plNext, 28.701257, -69.290965, 53.033009, -53.033009)
plNext = AddPolyLine_Arc_XY(plNext, 69.290965, -28.701257, 75, 0)
plNext = AddPolyLine_Arc_XY(plNext, 69.290965, 28.701257, 53.033009, 53.033009)
plNext = AddPolyLine_Arc_XY(plNext, 28.701257, 69.290965, 0, 75)
plNext = AddPolyLine_Arc_XY(plNext, -28.701257, 69.290965, -53.033009, 53.033009)
ClosePolyLine_Arc_XY(plNext, -69.290965, 28.701257, plStart)
# End of Outline 1 PolyLine

# Outline 2 PolyLine
plStart = GetPoint(-24.748737, 24.748737)
plNext = AddPolyLine_Arc_XY(plStart, -32.335784, 13.39392, -35, 0)
plNext = AddPolyLine_Arc_XY(plNext, -32.335784, -13.39392, -24.748737, -24.748737)
plNext = AddPolyLine_Arc_XY(plNext, -13.39392, -32.335784, 0, -35)
plNext = AddPolyLine_Arc_XY(plNext, 13.39392, -32.335784, 24.748737, -24.748737)
plNext = AddPolyLine_Arc_XY(plNext, 32.335784, -13.39392, 35, 0)
plNext = AddPolyLine_Arc_XY(plNext, 32.335784, 13.39392, 24.748737, 24.748737)
plNext = AddPolyLine_Arc_XY(plNext, 13.39392, 32.335784, 0, 35)
ClosePolyLine_Arc_XY(plNext, -13.39392, 32.335784, plStart)
# End of Outline 2 PolyLine

# Outline 3 PolyLine
plStart = GetPoint(67.126913, 6.064394)
plNext = AddPolyLine_Line_XY(plStart, 68.58111, 9.575136)
plNext = AddPolyLine_Arc_XY(plNext, 68.58111, 9.95782, 68.310512, 10.228418)
plNext = AddPolyLine_Line_XY(plNext, 51.68068, 17.11672)
plNext = AddPolyLine_Arc_XY(plNext, 51.297997, 17.116719, 51.027399, 16.846121)
plNext = AddPolyLine_Line_XY(plNext, 49.573202, 13.335379)
plNext = AddPolyLine_Arc_XY(plNext, 49.573202, 12.952696, 49.8438, 12.682098)
plNext = AddPolyLine_Line_XY(plNext, 66.473632, 5.793796)
ClosePolyLine_Arc_XY(plNext, 66.856315, 5.793796, plStart)
# End of Outline 3 PolyLine

# Outline 4 PolyLine
plStart = GetPoint(55.264812, 41.723524)
plNext = AddPolyLine_Line_XY(plStart, 51.75407, 43.177721)
plNext = AddPolyLine_Arc_XY(plNext, 51.371386, 43.177721, 51.100788, 42.907123)
plNext = AddPolyLine_Line_XY(plNext, 44.212486, 26.277292)
plNext = AddPolyLine_Arc_XY(plNext, 44.212486, 25.894608, 44.483084, 25.62401)
plNext = AddPolyLine_Line_XY(plNext, 47.993827, 24.169813)
plNext = AddPolyLine_Arc_XY(plNext, 48.37651, 24.169813, 48.647108, 24.440411)
plNext = AddPolyLine_Line_XY(plNext, 55.53541, 41.070243)
ClosePolyLine_Arc_XY(plNext, 55.53541, 41.452926, plStart)
# End of Outline 4 PolyLine

# Outline 5 PolyLine
plStart = GetPoint(-71.526314, 8.24539)
plNext = AddPolyLine_Arc_XY(plStart, -71.691244, 6.660747, -71.821071, 5.072842)
plNext = AddPolyLine_Arc_XY(plNext, -71.62163, 4.508694, -71.072935, 4.27)
plNext = AddPolyLine_Line_XY(plNext, -69.304967, 4.27)
plNext = AddPolyLine_Arc_XY(plNext, -68.89011, 4.32851, -68.507618, 4.499474)
plNext = AddPolyLine_Line_XY(plNext, -67.004117, 5.443032)
plNext = AddPolyLine_Arc_XY(plNext, -66.894874, 5.505365, -66.780794, 5.558326)
plNext = AddPolyLine_Line_XY(plNext, -66.435363, 5.701408)
plNext = AddPolyLine_Line_XY(plNext, -49.343592, 12.781051)
plNext = AddPolyLine_Line_XY(plNext, -45.260813, 14.472194)
plNext = AddPolyLine_Arc_XY(plNext, -44.374855, 15.798124, -45.260813, 17.124054)
plNext = AddPolyLine_Line_XY(plNext, -47.887868, 18.212216)
plNext = AddPolyLine_Arc_XY(plNext, -48.461893, 18.326397, -49.035918, 18.212216)
plNext = AddPolyLine_Line_XY(plNext, -51.218741, 17.308061)
plNext = AddPolyLine_Line_XY(plNext, -51.68068, 17.116719)
plNext = AddPolyLine_Arc_XY(plNext, -51.297997, 17.11672, -51.027399, 16.846121)
plNext = AddPolyLine_Line_XY(plNext, -49.573202, 13.335379)
plNext = AddPolyLine_Arc_XY(plNext, -49.573202, 12.952696, -49.8438, 12.682098)
plNext = AddPolyLine_Line_XY(plNext, -66.473632, 5.793796)
plNext = AddPolyLine_Arc_XY(plNext, -66.856315, 5.793796, -67.126913, 6.064394)
plNext = AddPolyLine_Line_XY(plNext, -68.58111, 9.575136)
plNext = AddPolyLine_Arc_XY(plNext, -68.58111, 9.95782, -68.310512, 10.228418)
plNext = AddPolyLine_Line_XY(plNext, -70.811719, 9.192384)
ClosePolyLine_Arc_XY(plNext, -71.297938, 8.81617, plStart)
# End of Outline 5 PolyLine

# Outline 6 PolyLine
plStart = GetPoint(-71.821071, -5.072842)
plNext = AddPolyLine_Arc_XY(plStart, -71.691244, -6.660747, -71.526314, -8.24539)
plNext = AddPolyLine_Arc_XY(plNext, -71.297938, -8.81617, -70.811719, -9.192384)
plNext = AddPolyLine_Line_XY(plNext, -68.310512, -10.228418)
plNext = AddPolyLine_Arc_XY(plNext, -68.58111, -9.95782, -68.58111, -9.575136)
plNext = AddPolyLine_Line_XY(plNext, -67.126913, -6.064394)
plNext = AddPolyLine_Arc_XY(plNext, -66.856315, -5.793796, -66.473632, -5.793796)
plNext = AddPolyLine_Line_XY(plNext, -49.8438, -12.682098)
plNext = AddPolyLine_Arc_XY(plNext, -49.573202, -12.952696, -49.573202, -13.335379)
plNext = AddPolyLine_Line_XY(plNext, -51.027399, -16.846121)
plNext = AddPolyLine_Arc_XY(plNext, -51.297997, -17.116719, -51.68068, -17.11672)
plNext = AddPolyLine_Line_XY(plNext, -51.218741, -17.308061)
plNext = AddPolyLine_Line_XY(plNext, -49.035918, -18.212216)
plNext = AddPolyLine_Arc_XY(plNext, -48.461893, -18.326397, -47.887868, -18.212216)
plNext = AddPolyLine_Line_XY(plNext, -45.260813, -17.124054)
plNext = AddPolyLine_Arc_XY(plNext, -44.374855, -15.798124, -45.260813, -14.472194)
plNext = AddPolyLine_Line_XY(plNext, -49.343592, -12.781051)
plNext = AddPolyLine_Line_XY(plNext, -66.435363, -5.701408)
plNext = AddPolyLine_Line_XY(plNext, -66.780794, -5.558326)
plNext = AddPolyLine_Arc_XY(plNext, -66.894874, -5.505365, -67.004117, -5.443032)
plNext = AddPolyLine_Line_XY(plNext, -68.507618, -4.499474)
plNext = AddPolyLine_Arc_XY(plNext, -68.89011, -4.32851, -69.304967, -4.27)
plNext = AddPolyLine_Line_XY(plNext, -71.072935, -4.27)
ClosePolyLine_Arc_XY(plNext, -71.62163, -4.508694, plStart)
# End of Outline 6 PolyLine

# Outline 7 PolyLine
plStart = GetPoint(67.70997, 14.835902)
plNext = AddPolyLine_Line_XY(plStart, 69.344264, 16.985108)
plNext = AddPolyLine_Arc_XY(plNext, 69.441696, 17.35518, 69.24891, 17.685756)
plNext = AddPolyLine_Line_XY(plNext, 62.403293, 22.891284)
plNext = AddPolyLine_Arc_XY(plNext, 62.03322, 22.988716, 61.702645, 22.79593)
plNext = AddPolyLine_Line_XY(plNext, 60.068351, 20.646724)
plNext = AddPolyLine_Arc_XY(plNext, 59.970919, 20.276652, 60.163705, 19.946076)
plNext = AddPolyLine_Line_XY(plNext, 67.009322, 14.740548)
ClosePolyLine_Arc_XY(plNext, 67.379395, 14.643116, plStart)
# End of Outline 7 PolyLine

# Outline 8 PolyLine
plStart = GetPoint(61.044084, 37.023515)
plNext = AddPolyLine_Line_XY(plStart, 58.368746, 37.387612)
plNext = AddPolyLine_Arc_XY(plNext, 57.998674, 37.29018, 57.805888, 36.959605)
plNext = AddPolyLine_Line_XY(plNext, 56.64617, 28.438158)
plNext = AddPolyLine_Arc_XY(plNext, 56.743602, 28.068086, 57.074177, 27.8753)
plNext = AddPolyLine_Line_XY(plNext, 59.749515, 27.511202)
plNext = AddPolyLine_Arc_XY(plNext, 60.119588, 27.608634, 60.312374, 27.93921)
plNext = AddPolyLine_Line_XY(plNext, 61.472092, 36.460656)
ClosePolyLine_Arc_XY(plNext, 61.37466, 36.830729, plStart)
# End of Outline 8 PolyLine

# Outline 9 PolyLine
plStart = GetPoint(-71.847535, 15.497795)
plNext = AddPolyLine_Arc_XY(plStart, -72.099381, 14.280382, -72.330599, 13.058884)
plNext = AddPolyLine_Arc_XY(plNext, -72.319762, 13.017939, -72.281395, 13)
plNext = AddPolyLine_Line_XY(plNext, -72.241206, 13)
plNext = AddPolyLine_Arc_XY(plNext, -72.142157, 13.006847, -72.044993, 13.027258)
plNext = AddPolyLine_Line_XY(plNext, -67.587327, 14.290156)
plNext = AddPolyLine_Arc_XY(plNext, -67.357268, 14.379279, -67.147793, 14.509625)
plNext = AddPolyLine_Line_XY(plNext, -66.948793, 14.660948)
plNext = AddPolyLine_Line_XY(plNext, -59.705175, 20.169123)
plNext = AddPolyLine_Line_XY(plNext, -57.987233, 21.475476)
plNext = AddPolyLine_Arc_XY(plNext, -57.498979, 22.6434, -58.268499, 23.648526)
plNext = AddPolyLine_Line_XY(plNext, -59.504488, 24.160489)
plNext = AddPolyLine_Arc_XY(plNext, -60.271057, 24.262261, -60.986454, 23.968673)
plNext = AddPolyLine_Line_XY(plNext, -62.005292, 23.193931)
plNext = AddPolyLine_Line_XY(plNext, -62.403293, 22.891284)
plNext = AddPolyLine_Arc_XY(plNext, -62.03322, 22.988716, -61.702645, 22.79593)
plNext = AddPolyLine_Line_XY(plNext, -60.068351, 20.646724)
plNext = AddPolyLine_Arc_XY(plNext, -59.970919, 20.276652, -60.163705, 19.946076)
plNext = AddPolyLine_Line_XY(plNext, -67.009322, 14.740548)
plNext = AddPolyLine_Arc_XY(plNext, -67.379395, 14.643116, -67.70997, 14.835902)
plNext = AddPolyLine_Line_XY(plNext, -69.344264, 16.985108)
plNext = AddPolyLine_Arc_XY(plNext, -69.441696, 17.35518, -69.24891, 17.685755)
plNext = AddPolyLine_Line_XY(plNext, -71.586427, 15.908267)
ClosePolyLine_Arc_XY(plNext, -71.753703, 15.72639, plStart)
# End of Outline 9 PolyLine

# Outline 10 PolyLine
plStart = GetPoint(-72.330599, -13.058884)
plNext = AddPolyLine_Arc_XY(plStart, -72.099381, -14.280382, -71.847535, -15.497795)
plNext = AddPolyLine_Arc_XY(plNext, -71.753703, -15.72639, -71.586427, -15.908267)
plNext = AddPolyLine_Line_XY(plNext, -69.24891, -17.685755)
plNext = AddPolyLine_Arc_XY(plNext, -69.441696, -17.35518, -69.344264, -16.985108)
plNext = AddPolyLine_Line_XY(plNext, -67.70997, -14.835902)
plNext = AddPolyLine_Arc_XY(plNext, -67.379395, -14.643116, -67.009322, -14.740548)
plNext = AddPolyLine_Line_XY(plNext, -60.163705, -19.946076)
plNext = AddPolyLine_Arc_XY(plNext, -59.970919, -20.276652, -60.068351, -20.646724)
plNext = AddPolyLine_Line_XY(plNext, -61.702645, -22.79593)
plNext = AddPolyLine_Arc_XY(plNext, -62.03322, -22.988716, -62.403293, -22.891284)
plNext = AddPolyLine_Line_XY(plNext, -62.005292, -23.193931)
plNext = AddPolyLine_Line_XY(plNext, -60.986454, -23.968673)
plNext = AddPolyLine_Arc_XY(plNext, -60.271057, -24.262261, -59.504488, -24.160489)
plNext = AddPolyLine_Line_XY(plNext, -58.268499, -23.648526)
plNext = AddPolyLine_Arc_XY(plNext, -57.498979, -22.6434, -57.987233, -21.475476)
plNext = AddPolyLine_Line_XY(plNext, -59.705175, -20.169123)
plNext = AddPolyLine_Line_XY(plNext, -66.948793, -14.660948)
plNext = AddPolyLine_Line_XY(plNext, -67.147793, -14.509625)
plNext = AddPolyLine_Arc_XY(plNext, -67.357268, -14.379279, -67.587327, -14.290156)
plNext = AddPolyLine_Line_XY(plNext, -72.044993, -13.027258)
plNext = AddPolyLine_Arc_XY(plNext, -72.142157, -13.006847, -72.241206, -13)
plNext = AddPolyLine_Line_XY(plNext, -72.281395, -13)
ClosePolyLine_Arc_XY(plNext, -72.319762, -13.017939, plStart)
# End of Outline 10 PolyLine

# Outline 11 PolyLine
plStart = GetPoint(-61.472092, 36.460656)
plNext = AddPolyLine_Arc_XY(plStart, -61.37466, 36.830729, -61.044084, 37.023515)
plNext = AddPolyLine_Line_XY(plNext, -58.368746, 37.387612)
plNext = AddPolyLine_Arc_XY(plNext, -57.998674, 37.29018, -57.805888, 36.959605)
plNext = AddPolyLine_Line_XY(plNext, -56.64617, 28.438158)
plNext = AddPolyLine_Arc_XY(plNext, -56.743602, 28.068086, -57.074177, 27.8753)
plNext = AddPolyLine_Line_XY(plNext, -59.749515, 27.511202)
plNext = AddPolyLine_Arc_XY(plNext, -60.119588, 27.608634, -60.312374, 27.93921)
plNext = AddPolyLine_Line_XY(plNext, -60.244948, 27.443777)
plNext = AddPolyLine_Line_XY(plNext, -60.072346, 26.175524)
plNext = AddPolyLine_Arc_XY(plNext, -59.774083, 25.462064, -59.160073, 24.991981)
plNext = AddPolyLine_Line_XY(plNext, -57.924084, 24.480018)
plNext = AddPolyLine_Arc_XY(plNext, -56.66922, 24.646616, -56.188621, 25.817711)
plNext = AddPolyLine_Line_XY(plNext, -56.479658, 27.95621)
plNext = AddPolyLine_Line_XY(plNext, -57.706801, 36.97309)
plNext = AddPolyLine_Line_XY(plNext, -57.740514, 37.220806)
plNext = AddPolyLine_Arc_XY(plNext, -57.796466, 37.461096, -57.896123, 37.686791)
plNext = AddPolyLine_Line_XY(plNext, -60.155165, 41.73184)
plNext = AddPolyLine_Arc_XY(plNext, -60.209438, 41.814979, -60.274635, 41.889858)
plNext = AddPolyLine_Line_XY(plNext, -60.303052, 41.918276)
plNext = AddPolyLine_Arc_XY(plNext, -60.342867, 41.932721, -60.379482, 41.911432)
plNext = AddPolyLine_Arc_XY(plNext, -61.079716, 40.884206, -61.762475, 39.845284)
plNext = AddPolyLine_Arc_XY(plNext, -61.857767, 39.617293, -61.868091, 39.370404)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 11 PolyLine

# Outline 12 PolyLine
plStart = GetPoint(-41.889858, -60.274635)
plNext = AddPolyLine_Line_XY(plStart, -41.918276, -60.303052)
plNext = AddPolyLine_Arc_XY(plNext, -41.932721, -60.342867, -41.911432, -60.379482)
plNext = AddPolyLine_Arc_XY(plNext, -40.884206, -61.079716, -39.845284, -61.762475)
plNext = AddPolyLine_Arc_XY(plNext, -39.617293, -61.857767, -39.370404, -61.868091)
plNext = AddPolyLine_Line_XY(plNext, -36.460656, -61.472092)
plNext = AddPolyLine_Arc_XY(plNext, -36.830729, -61.37466, -37.023515, -61.044084)
plNext = AddPolyLine_Line_XY(plNext, -37.387612, -58.368746)
plNext = AddPolyLine_Arc_XY(plNext, -37.29018, -57.998674, -36.959605, -57.805888)
plNext = AddPolyLine_Line_XY(plNext, -28.438158, -56.64617)
plNext = AddPolyLine_Arc_XY(plNext, -28.068086, -56.743602, -27.8753, -57.074177)
plNext = AddPolyLine_Line_XY(plNext, -27.511202, -59.749515)
plNext = AddPolyLine_Arc_XY(plNext, -27.608634, -60.119588, -27.93921, -60.312374)
plNext = AddPolyLine_Line_XY(plNext, -27.443777, -60.244948)
plNext = AddPolyLine_Line_XY(plNext, -26.175524, -60.072346)
plNext = AddPolyLine_Arc_XY(plNext, -25.462064, -59.774083, -24.991981, -59.160073)
plNext = AddPolyLine_Line_XY(plNext, -24.480018, -57.924084)
plNext = AddPolyLine_Arc_XY(plNext, -24.646616, -56.66922, -25.817711, -56.188621)
plNext = AddPolyLine_Line_XY(plNext, -27.95621, -56.479658)
plNext = AddPolyLine_Line_XY(plNext, -36.97309, -57.706801)
plNext = AddPolyLine_Line_XY(plNext, -37.220806, -57.740514)
plNext = AddPolyLine_Arc_XY(plNext, -37.461096, -57.796466, -37.686791, -57.896123)
plNext = AddPolyLine_Line_XY(plNext, -41.73184, -60.155165)
ClosePolyLine_Arc_XY(plNext, -41.814979, -60.209438, plStart)
# End of Outline 12 PolyLine

# Outline 13 PolyLine
plStart = GetPoint(-23.648526, 58.268499)
plNext = AddPolyLine_Arc_XY(plStart, -22.6434, 57.498979, -21.475476, 57.987233)
plNext = AddPolyLine_Line_XY(plNext, -20.169123, 59.705175)
plNext = AddPolyLine_Line_XY(plNext, -14.660948, 66.948793)
plNext = AddPolyLine_Line_XY(plNext, -14.509625, 67.147793)
plNext = AddPolyLine_Arc_XY(plNext, -14.379279, 67.357268, -14.290156, 67.587327)
plNext = AddPolyLine_Line_XY(plNext, -13.027258, 72.044993)
plNext = AddPolyLine_Arc_XY(plNext, -13.006847, 72.142157, -13, 72.241206)
plNext = AddPolyLine_Line_XY(plNext, -13, 72.281395)
plNext = AddPolyLine_Arc_XY(plNext, -13.017939, 72.319762, -13.058884, 72.330599)
plNext = AddPolyLine_Arc_XY(plNext, -14.280382, 72.099381, -15.497795, 71.847535)
plNext = AddPolyLine_Arc_XY(plNext, -15.72639, 71.753703, -15.908267, 71.586427)
plNext = AddPolyLine_Line_XY(plNext, -17.685755, 69.24891)
plNext = AddPolyLine_Arc_XY(plNext, -17.35518, 69.441696, -16.985108, 69.344264)
plNext = AddPolyLine_Line_XY(plNext, -14.835902, 67.70997)
plNext = AddPolyLine_Arc_XY(plNext, -14.643116, 67.379395, -14.740548, 67.009322)
plNext = AddPolyLine_Line_XY(plNext, -19.946076, 60.163705)
plNext = AddPolyLine_Arc_XY(plNext, -20.276652, 59.970919, -20.646724, 60.068351)
plNext = AddPolyLine_Line_XY(plNext, -22.79593, 61.702645)
plNext = AddPolyLine_Arc_XY(plNext, -22.988716, 62.03322, -22.891284, 62.403293)
plNext = AddPolyLine_Line_XY(plNext, -23.193931, 62.005292)
plNext = AddPolyLine_Line_XY(plNext, -23.968673, 60.986454)
plNext = AddPolyLine_Arc_XY(plNext, -24.262261, 60.271057, -24.160489, 59.504488)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 13 PolyLine

# Outline 14 PolyLine
plStart = GetPoint(13, -72.241206)
plNext = AddPolyLine_Line_XY(plStart, 13, -72.281395)
plNext = AddPolyLine_Arc_XY(plNext, 13.017939, -72.319762, 13.058884, -72.330599)
plNext = AddPolyLine_Arc_XY(plNext, 14.280382, -72.099381, 15.497795, -71.847535)
plNext = AddPolyLine_Arc_XY(plNext, 15.72639, -71.753703, 15.908267, -71.586427)
plNext = AddPolyLine_Line_XY(plNext, 17.685755, -69.24891)
plNext = AddPolyLine_Arc_XY(plNext, 17.35518, -69.441696, 16.985108, -69.344264)
plNext = AddPolyLine_Line_XY(plNext, 14.835902, -67.70997)
plNext = AddPolyLine_Arc_XY(plNext, 14.643116, -67.379395, 14.740548, -67.009322)
plNext = AddPolyLine_Line_XY(plNext, 19.946076, -60.163705)
plNext = AddPolyLine_Arc_XY(plNext, 20.276652, -59.970919, 20.646724, -60.068351)
plNext = AddPolyLine_Line_XY(plNext, 22.79593, -61.702645)
plNext = AddPolyLine_Arc_XY(plNext, 22.988716, -62.03322, 22.891284, -62.403293)
plNext = AddPolyLine_Line_XY(plNext, 23.193931, -62.005292)
plNext = AddPolyLine_Line_XY(plNext, 23.968673, -60.986454)
plNext = AddPolyLine_Arc_XY(plNext, 24.262261, -60.271057, 24.160489, -59.504488)
plNext = AddPolyLine_Line_XY(plNext, 23.648526, -58.268499)
plNext = AddPolyLine_Arc_XY(plNext, 22.6434, -57.498979, 21.475476, -57.987233)
plNext = AddPolyLine_Line_XY(plNext, 20.169123, -59.705175)
plNext = AddPolyLine_Line_XY(plNext, 14.660948, -66.948793)
plNext = AddPolyLine_Line_XY(plNext, 14.509625, -67.147793)
plNext = AddPolyLine_Arc_XY(plNext, 14.379279, -67.357268, 14.290156, -67.587327)
plNext = AddPolyLine_Line_XY(plNext, 13.027258, -72.044993)
ClosePolyLine_Arc_XY(plNext, 13.006847, -72.142157, plStart)
# End of Outline 14 PolyLine

# Outline 15 PolyLine
plStart = GetPoint(24.991981, 59.160073)
plNext = AddPolyLine_Line_XY(plStart, 24.480018, 57.924084)
plNext = AddPolyLine_Arc_XY(plNext, 24.646616, 56.66922, 25.817711, 56.188621)
plNext = AddPolyLine_Line_XY(plNext, 27.95621, 56.479658)
plNext = AddPolyLine_Line_XY(plNext, 36.97309, 57.706801)
plNext = AddPolyLine_Line_XY(plNext, 37.220806, 57.740514)
plNext = AddPolyLine_Arc_XY(plNext, 37.461096, 57.796466, 37.686791, 57.896123)
plNext = AddPolyLine_Line_XY(plNext, 41.73184, 60.155165)
plNext = AddPolyLine_Arc_XY(plNext, 41.814979, 60.209438, 41.889858, 60.274635)
plNext = AddPolyLine_Line_XY(plNext, 41.918276, 60.303052)
plNext = AddPolyLine_Arc_XY(plNext, 41.932721, 60.342867, 41.911432, 60.379482)
plNext = AddPolyLine_Arc_XY(plNext, 40.884206, 61.079716, 39.845284, 61.762475)
plNext = AddPolyLine_Arc_XY(plNext, 39.617293, 61.857767, 39.370404, 61.868091)
plNext = AddPolyLine_Line_XY(plNext, 36.460656, 61.472092)
plNext = AddPolyLine_Arc_XY(plNext, 36.830729, 61.37466, 37.023515, 61.044084)
plNext = AddPolyLine_Line_XY(plNext, 37.387612, 58.368746)
plNext = AddPolyLine_Arc_XY(plNext, 37.29018, 57.998674, 36.959605, 57.805888)
plNext = AddPolyLine_Line_XY(plNext, 28.438158, 56.64617)
plNext = AddPolyLine_Arc_XY(plNext, 28.068086, 56.743602, 27.8753, 57.074177)
plNext = AddPolyLine_Line_XY(plNext, 27.511202, 59.749515)
plNext = AddPolyLine_Arc_XY(plNext, 27.608634, 60.119588, 27.93921, 60.312374)
plNext = AddPolyLine_Line_XY(plNext, 27.443777, 60.244948)
plNext = AddPolyLine_Line_XY(plNext, 26.175524, 60.072346)
ClosePolyLine_Arc_XY(plNext, 25.462064, 59.774083, plStart)
# End of Outline 15 PolyLine

# Outline 16 PolyLine
plStart = GetPoint(56.479658, -27.95621)
plNext = AddPolyLine_Line_XY(plStart, 57.706801, -36.97309)
plNext = AddPolyLine_Line_XY(plNext, 57.740514, -37.220806)
plNext = AddPolyLine_Arc_XY(plNext, 57.796466, -37.461096, 57.896123, -37.686791)
plNext = AddPolyLine_Line_XY(plNext, 60.155165, -41.73184)
plNext = AddPolyLine_Arc_XY(plNext, 60.209438, -41.814979, 60.274635, -41.889858)
plNext = AddPolyLine_Line_XY(plNext, 60.303052, -41.918276)
plNext = AddPolyLine_Arc_XY(plNext, 60.342867, -41.932721, 60.379482, -41.911432)
plNext = AddPolyLine_Arc_XY(plNext, 61.079716, -40.884206, 61.762475, -39.845284)
plNext = AddPolyLine_Arc_XY(plNext, 61.857767, -39.617293, 61.868091, -39.370404)
plNext = AddPolyLine_Line_XY(plNext, 61.472092, -36.460656)
plNext = AddPolyLine_Arc_XY(plNext, 61.37466, -36.830729, 61.044084, -37.023515)
plNext = AddPolyLine_Line_XY(plNext, 58.368746, -37.387612)
plNext = AddPolyLine_Arc_XY(plNext, 57.998674, -37.29018, 57.805888, -36.959605)
plNext = AddPolyLine_Line_XY(plNext, 56.64617, -28.438158)
plNext = AddPolyLine_Arc_XY(plNext, 56.743602, -28.068086, 57.074177, -27.8753)
plNext = AddPolyLine_Line_XY(plNext, 59.749515, -27.511202)
plNext = AddPolyLine_Arc_XY(plNext, 60.119588, -27.608634, 60.312374, -27.93921)
plNext = AddPolyLine_Line_XY(plNext, 60.244948, -27.443777)
plNext = AddPolyLine_Line_XY(plNext, 60.072346, -26.175524)
plNext = AddPolyLine_Arc_XY(plNext, 59.774083, -25.462064, 59.160073, -24.991981)
plNext = AddPolyLine_Line_XY(plNext, 57.924084, -24.480018)
plNext = AddPolyLine_Arc_XY(plNext, 56.66922, -24.646616, 56.188621, -25.817711)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 16 PolyLine

# Outline 17 PolyLine
plStart = GetPoint(59.705175, 20.169123)
plNext = AddPolyLine_Line_XY(plStart, 66.948793, 14.660948)
plNext = AddPolyLine_Line_XY(plNext, 67.147793, 14.509625)
plNext = AddPolyLine_Arc_XY(plNext, 67.357268, 14.379279, 67.587327, 14.290156)
plNext = AddPolyLine_Line_XY(plNext, 72.044993, 13.027258)
plNext = AddPolyLine_Arc_XY(plNext, 72.142157, 13.006847, 72.241206, 13)
plNext = AddPolyLine_Line_XY(plNext, 72.281395, 13)
plNext = AddPolyLine_Arc_XY(plNext, 72.319762, 13.017939, 72.330599, 13.058884)
plNext = AddPolyLine_Arc_XY(plNext, 72.099381, 14.280382, 71.847535, 15.497795)
plNext = AddPolyLine_Arc_XY(plNext, 71.753703, 15.72639, 71.586427, 15.908267)
plNext = AddPolyLine_Line_XY(plNext, 69.24891, 17.685755)
plNext = AddPolyLine_Arc_XY(plNext, 69.441696, 17.35518, 69.344264, 16.985108)
plNext = AddPolyLine_Line_XY(plNext, 67.70997, 14.835902)
plNext = AddPolyLine_Arc_XY(plNext, 67.379395, 14.643116, 67.009322, 14.740548)
plNext = AddPolyLine_Line_XY(plNext, 60.163705, 19.946076)
plNext = AddPolyLine_Arc_XY(plNext, 59.970919, 20.276652, 60.068351, 20.646724)
plNext = AddPolyLine_Line_XY(plNext, 61.702645, 22.79593)
plNext = AddPolyLine_Arc_XY(plNext, 62.03322, 22.988716, 62.403293, 22.891284)
plNext = AddPolyLine_Line_XY(plNext, 62.005292, 23.193931)
plNext = AddPolyLine_Line_XY(plNext, 60.986454, 23.968673)
plNext = AddPolyLine_Arc_XY(plNext, 60.271057, 24.262261, 59.504488, 24.160489)
plNext = AddPolyLine_Line_XY(plNext, 58.268499, 23.648526)
plNext = AddPolyLine_Arc_XY(plNext, 57.498979, 22.6434, 57.987233, 21.475476)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 17 PolyLine

# Outline 18 PolyLine
plStart = GetPoint(-61.472092, -36.460656)
plNext = AddPolyLine_Line_XY(plStart, -61.868091, -39.370404)
plNext = AddPolyLine_Arc_XY(plNext, -61.857767, -39.617293, -61.762475, -39.845284)
plNext = AddPolyLine_Arc_XY(plNext, -61.079716, -40.884206, -60.379482, -41.911432)
plNext = AddPolyLine_Arc_XY(plNext, -60.342867, -41.932721, -60.303052, -41.918276)
plNext = AddPolyLine_Line_XY(plNext, -60.274635, -41.889858)
plNext = AddPolyLine_Arc_XY(plNext, -60.209438, -41.814979, -60.155165, -41.73184)
plNext = AddPolyLine_Line_XY(plNext, -57.896123, -37.686791)
plNext = AddPolyLine_Arc_XY(plNext, -57.796466, -37.461096, -57.740514, -37.220806)
plNext = AddPolyLine_Line_XY(plNext, -57.706801, -36.97309)
plNext = AddPolyLine_Line_XY(plNext, -56.479658, -27.95621)
plNext = AddPolyLine_Line_XY(plNext, -56.188621, -25.817711)
plNext = AddPolyLine_Arc_XY(plNext, -56.66922, -24.646616, -57.924084, -24.480018)
plNext = AddPolyLine_Line_XY(plNext, -59.160073, -24.991981)
plNext = AddPolyLine_Arc_XY(plNext, -59.774083, -25.462064, -60.072346, -26.175524)
plNext = AddPolyLine_Line_XY(plNext, -60.244948, -27.443777)
plNext = AddPolyLine_Line_XY(plNext, -60.312374, -27.93921)
plNext = AddPolyLine_Arc_XY(plNext, -60.119588, -27.608634, -59.749515, -27.511202)
plNext = AddPolyLine_Line_XY(plNext, -57.074177, -27.8753)
plNext = AddPolyLine_Arc_XY(plNext, -56.743602, -28.068086, -56.64617, -28.438158)
plNext = AddPolyLine_Line_XY(plNext, -57.805888, -36.959605)
plNext = AddPolyLine_Arc_XY(plNext, -57.998674, -37.29018, -58.368746, -37.387612)
plNext = AddPolyLine_Line_XY(plNext, -61.044084, -37.023515)
ClosePolyLine_Arc_XY(plNext, -61.37466, -36.830729, plStart)
# End of Outline 18 PolyLine

# Outline 19 PolyLine
plStart = GetPoint(-41.889858, 60.274635)
plNext = AddPolyLine_Arc_XY(plStart, -41.814979, 60.209438, -41.73184, 60.155165)
plNext = AddPolyLine_Line_XY(plNext, -37.686791, 57.896123)
plNext = AddPolyLine_Arc_XY(plNext, -37.461096, 57.796466, -37.220806, 57.740514)
plNext = AddPolyLine_Line_XY(plNext, -36.97309, 57.706801)
plNext = AddPolyLine_Line_XY(plNext, -27.95621, 56.479658)
plNext = AddPolyLine_Line_XY(plNext, -25.817711, 56.188621)
plNext = AddPolyLine_Arc_XY(plNext, -24.646616, 56.66922, -24.480018, 57.924084)
plNext = AddPolyLine_Line_XY(plNext, -24.991981, 59.160073)
plNext = AddPolyLine_Arc_XY(plNext, -25.462064, 59.774083, -26.175524, 60.072346)
plNext = AddPolyLine_Line_XY(plNext, -27.443777, 60.244948)
plNext = AddPolyLine_Line_XY(plNext, -27.93921, 60.312374)
plNext = AddPolyLine_Arc_XY(plNext, -27.608634, 60.119588, -27.511202, 59.749515)
plNext = AddPolyLine_Line_XY(plNext, -27.8753, 57.074177)
plNext = AddPolyLine_Arc_XY(plNext, -28.068086, 56.743602, -28.438158, 56.64617)
plNext = AddPolyLine_Line_XY(plNext, -36.959605, 57.805888)
plNext = AddPolyLine_Arc_XY(plNext, -37.29018, 57.998674, -37.387612, 58.368746)
plNext = AddPolyLine_Line_XY(plNext, -37.023515, 61.044084)
plNext = AddPolyLine_Arc_XY(plNext, -36.830729, 61.37466, -36.460656, 61.472092)
plNext = AddPolyLine_Line_XY(plNext, -39.370404, 61.868091)
plNext = AddPolyLine_Arc_XY(plNext, -39.617293, 61.857767, -39.845284, 61.762475)
plNext = AddPolyLine_Arc_XY(plNext, -40.884206, 61.079716, -41.911432, 60.379482)
plNext = AddPolyLine_Arc_XY(plNext, -41.932721, 60.342867, -41.918276, 60.303052)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 19 PolyLine

# Outline 20 PolyLine
plStart = GetPoint(-23.648526, -58.268499)
plNext = AddPolyLine_Line_XY(plStart, -24.160489, -59.504488)
plNext = AddPolyLine_Arc_XY(plNext, -24.262261, -60.271057, -23.968673, -60.986454)
plNext = AddPolyLine_Line_XY(plNext, -23.193931, -62.005292)
plNext = AddPolyLine_Line_XY(plNext, -22.891284, -62.403293)
plNext = AddPolyLine_Arc_XY(plNext, -22.988716, -62.03322, -22.79593, -61.702645)
plNext = AddPolyLine_Line_XY(plNext, -20.646724, -60.068351)
plNext = AddPolyLine_Arc_XY(plNext, -20.276652, -59.970919, -19.946076, -60.163705)
plNext = AddPolyLine_Line_XY(plNext, -14.740548, -67.009322)
plNext = AddPolyLine_Arc_XY(plNext, -14.643116, -67.379395, -14.835902, -67.70997)
plNext = AddPolyLine_Line_XY(plNext, -16.985108, -69.344264)
plNext = AddPolyLine_Arc_XY(plNext, -17.35518, -69.441696, -17.685755, -69.24891)
plNext = AddPolyLine_Line_XY(plNext, -15.908267, -71.586427)
plNext = AddPolyLine_Arc_XY(plNext, -15.72639, -71.753703, -15.497795, -71.847535)
plNext = AddPolyLine_Arc_XY(plNext, -14.280382, -72.099381, -13.058884, -72.330599)
plNext = AddPolyLine_Arc_XY(plNext, -13.017939, -72.319762, -13, -72.281395)
plNext = AddPolyLine_Line_XY(plNext, -13, -72.241206)
plNext = AddPolyLine_Arc_XY(plNext, -13.006847, -72.142157, -13.027258, -72.044993)
plNext = AddPolyLine_Line_XY(plNext, -14.290156, -67.587327)
plNext = AddPolyLine_Arc_XY(plNext, -14.379279, -67.357268, -14.509625, -67.147793)
plNext = AddPolyLine_Line_XY(plNext, -14.660948, -66.948793)
plNext = AddPolyLine_Line_XY(plNext, -20.169123, -59.705175)
plNext = AddPolyLine_Line_XY(plNext, -21.475476, -57.987233)
ClosePolyLine_Arc_XY(plNext, -22.6434, -57.498979, plStart)
# End of Outline 20 PolyLine

# Outline 21 PolyLine
plStart = GetPoint(13, 72.281395)
plNext = AddPolyLine_Line_XY(plStart, 13, 72.241206)
plNext = AddPolyLine_Arc_XY(plNext, 13.006847, 72.142157, 13.027258, 72.044993)
plNext = AddPolyLine_Line_XY(plNext, 14.290156, 67.587327)
plNext = AddPolyLine_Arc_XY(plNext, 14.379279, 67.357268, 14.509625, 67.147793)
plNext = AddPolyLine_Line_XY(plNext, 14.660948, 66.948793)
plNext = AddPolyLine_Line_XY(plNext, 20.169123, 59.705175)
plNext = AddPolyLine_Line_XY(plNext, 21.475476, 57.987233)
plNext = AddPolyLine_Arc_XY(plNext, 22.6434, 57.498979, 23.648526, 58.268499)
plNext = AddPolyLine_Line_XY(plNext, 24.160489, 59.504488)
plNext = AddPolyLine_Arc_XY(plNext, 24.262261, 60.271057, 23.968673, 60.986454)
plNext = AddPolyLine_Line_XY(plNext, 23.193931, 62.005292)
plNext = AddPolyLine_Line_XY(plNext, 22.891284, 62.403293)
plNext = AddPolyLine_Arc_XY(plNext, 22.988716, 62.03322, 22.79593, 61.702645)
plNext = AddPolyLine_Line_XY(plNext, 20.646724, 60.068351)
plNext = AddPolyLine_Arc_XY(plNext, 20.276652, 59.970919, 19.946076, 60.163705)
plNext = AddPolyLine_Line_XY(plNext, 14.740548, 67.009322)
plNext = AddPolyLine_Arc_XY(plNext, 14.643116, 67.379395, 14.835902, 67.70997)
plNext = AddPolyLine_Line_XY(plNext, 16.985108, 69.344264)
plNext = AddPolyLine_Arc_XY(plNext, 17.35518, 69.441696, 17.685755, 69.24891)
plNext = AddPolyLine_Line_XY(plNext, 15.908267, 71.586427)
plNext = AddPolyLine_Arc_XY(plNext, 15.72639, 71.753703, 15.497795, 71.847535)
plNext = AddPolyLine_Arc_XY(plNext, 14.280382, 72.099381, 13.058884, 72.330599)
ClosePolyLine_Arc_XY(plNext, 13.017939, 72.319762, plStart)
# End of Outline 21 PolyLine

# Outline 22 PolyLine
plStart = GetPoint(24.991981, -59.160073)
plNext = AddPolyLine_Arc_XY(plStart, 25.462064, -59.774083, 26.175524, -60.072346)
plNext = AddPolyLine_Line_XY(plNext, 27.443777, -60.244948)
plNext = AddPolyLine_Line_XY(plNext, 27.93921, -60.312374)
plNext = AddPolyLine_Arc_XY(plNext, 27.608634, -60.119588, 27.511202, -59.749515)
plNext = AddPolyLine_Line_XY(plNext, 27.8753, -57.074177)
plNext = AddPolyLine_Arc_XY(plNext, 28.068086, -56.743602, 28.438158, -56.64617)
plNext = AddPolyLine_Line_XY(plNext, 36.959605, -57.805888)
plNext = AddPolyLine_Arc_XY(plNext, 37.29018, -57.998674, 37.387612, -58.368746)
plNext = AddPolyLine_Line_XY(plNext, 37.023515, -61.044084)
plNext = AddPolyLine_Arc_XY(plNext, 36.830729, -61.37466, 36.460656, -61.472092)
plNext = AddPolyLine_Line_XY(plNext, 39.370404, -61.868091)
plNext = AddPolyLine_Arc_XY(plNext, 39.617293, -61.857767, 39.845284, -61.762475)
plNext = AddPolyLine_Arc_XY(plNext, 40.884206, -61.079716, 41.911432, -60.379482)
plNext = AddPolyLine_Arc_XY(plNext, 41.932721, -60.342867, 41.918276, -60.303052)
plNext = AddPolyLine_Line_XY(plNext, 41.889858, -60.274635)
plNext = AddPolyLine_Arc_XY(plNext, 41.814979, -60.209438, 41.73184, -60.155165)
plNext = AddPolyLine_Line_XY(plNext, 37.686791, -57.896123)
plNext = AddPolyLine_Arc_XY(plNext, 37.461096, -57.796466, 37.220806, -57.740514)
plNext = AddPolyLine_Line_XY(plNext, 36.97309, -57.706801)
plNext = AddPolyLine_Line_XY(plNext, 27.95621, -56.479658)
plNext = AddPolyLine_Line_XY(plNext, 25.817711, -56.188621)
plNext = AddPolyLine_Arc_XY(plNext, 24.646616, -56.66922, 24.480018, -57.924084)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 22 PolyLine

# Outline 23 PolyLine
plStart = GetPoint(56.479658, 27.95621)
plNext = AddPolyLine_Line_XY(plStart, 56.188621, 25.817711)
plNext = AddPolyLine_Arc_XY(plNext, 56.66922, 24.646616, 57.924084, 24.480018)
plNext = AddPolyLine_Line_XY(plNext, 59.160073, 24.991981)
plNext = AddPolyLine_Arc_XY(plNext, 59.774083, 25.462064, 60.072346, 26.175524)
plNext = AddPolyLine_Line_XY(plNext, 60.244948, 27.443777)
plNext = AddPolyLine_Line_XY(plNext, 60.312374, 27.93921)
plNext = AddPolyLine_Arc_XY(plNext, 60.119588, 27.608634, 59.749515, 27.511202)
plNext = AddPolyLine_Line_XY(plNext, 57.074177, 27.8753)
plNext = AddPolyLine_Arc_XY(plNext, 56.743602, 28.068086, 56.64617, 28.438158)
plNext = AddPolyLine_Line_XY(plNext, 57.805888, 36.959605)
plNext = AddPolyLine_Arc_XY(plNext, 57.998674, 37.29018, 58.368746, 37.387612)
plNext = AddPolyLine_Line_XY(plNext, 61.044084, 37.023515)
plNext = AddPolyLine_Arc_XY(plNext, 61.37466, 36.830729, 61.472092, 36.460656)
plNext = AddPolyLine_Line_XY(plNext, 61.868091, 39.370404)
plNext = AddPolyLine_Arc_XY(plNext, 61.857767, 39.617293, 61.762475, 39.845284)
plNext = AddPolyLine_Arc_XY(plNext, 61.079716, 40.884206, 60.379482, 41.911432)
plNext = AddPolyLine_Arc_XY(plNext, 60.342867, 41.932721, 60.303052, 41.918276)
plNext = AddPolyLine_Line_XY(plNext, 60.274635, 41.889858)
plNext = AddPolyLine_Arc_XY(plNext, 60.209438, 41.814979, 60.155165, 41.73184)
plNext = AddPolyLine_Line_XY(plNext, 57.896123, 37.686791)
plNext = AddPolyLine_Arc_XY(plNext, 57.796466, 37.461096, 57.740514, 37.220806)
plNext = AddPolyLine_Line_XY(plNext, 57.706801, 36.97309)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 23 PolyLine

# Outline 24 PolyLine
plStart = GetPoint(59.705175, -20.169123)
plNext = AddPolyLine_Line_XY(plStart, 57.987233, -21.475476)
plNext = AddPolyLine_Arc_XY(plNext, 57.498979, -22.6434, 58.268499, -23.648526)
plNext = AddPolyLine_Line_XY(plNext, 59.504488, -24.160489)
plNext = AddPolyLine_Arc_XY(plNext, 60.271057, -24.262261, 60.986454, -23.968673)
plNext = AddPolyLine_Line_XY(plNext, 62.005292, -23.193931)
plNext = AddPolyLine_Line_XY(plNext, 62.403293, -22.891284)
plNext = AddPolyLine_Arc_XY(plNext, 62.03322, -22.988716, 61.702645, -22.79593)
plNext = AddPolyLine_Line_XY(plNext, 60.068351, -20.646724)
plNext = AddPolyLine_Arc_XY(plNext, 59.970919, -20.276652, 60.163705, -19.946076)
plNext = AddPolyLine_Line_XY(plNext, 67.009322, -14.740548)
plNext = AddPolyLine_Arc_XY(plNext, 67.379395, -14.643116, 67.70997, -14.835902)
plNext = AddPolyLine_Line_XY(plNext, 69.344264, -16.985108)
plNext = AddPolyLine_Arc_XY(plNext, 69.441696, -17.35518, 69.24891, -17.685755)
plNext = AddPolyLine_Line_XY(plNext, 71.586427, -15.908267)
plNext = AddPolyLine_Arc_XY(plNext, 71.753703, -15.72639, 71.847535, -15.497795)
plNext = AddPolyLine_Arc_XY(plNext, 72.099381, -14.280382, 72.330599, -13.058884)
plNext = AddPolyLine_Arc_XY(plNext, 72.319762, -13.017939, 72.281395, -13)
plNext = AddPolyLine_Line_XY(plNext, 72.241206, -13)
plNext = AddPolyLine_Arc_XY(plNext, 72.142157, -13.006847, 72.044993, -13.027258)
plNext = AddPolyLine_Line_XY(plNext, 67.587327, -14.290156)
plNext = AddPolyLine_Arc_XY(plNext, 67.357268, -14.379279, 67.147793, -14.509625)
plNext = AddPolyLine_Line_XY(plNext, 66.948793, -14.660948)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 24 PolyLine

# Outline 25 PolyLine
plStart = GetPoint(16.985108, 69.344264)
plNext = AddPolyLine_Line_XY(plStart, 14.835902, 67.70997)
plNext = AddPolyLine_Arc_XY(plNext, 14.643116, 67.379395, 14.740548, 67.009322)
plNext = AddPolyLine_Line_XY(plNext, 19.946076, 60.163705)
plNext = AddPolyLine_Arc_XY(plNext, 20.276652, 59.970919, 20.646724, 60.068351)
plNext = AddPolyLine_Line_XY(plNext, 22.79593, 61.702645)
plNext = AddPolyLine_Arc_XY(plNext, 22.988716, 62.03322, 22.891284, 62.403293)
plNext = AddPolyLine_Line_XY(plNext, 17.685755, 69.24891)
ClosePolyLine_Arc_XY(plNext, 17.35518, 69.441696, plStart)
# End of Outline 25 PolyLine

# Outline 26 PolyLine
plStart = GetPoint(-37.023515, 61.044084)
plNext = AddPolyLine_Line_XY(plStart, -37.387612, 58.368746)
plNext = AddPolyLine_Arc_XY(plNext, -37.29018, 57.998674, -36.959605, 57.805888)
plNext = AddPolyLine_Line_XY(plNext, -28.438158, 56.64617)
plNext = AddPolyLine_Arc_XY(plNext, -28.068086, 56.743602, -27.8753, 57.074177)
plNext = AddPolyLine_Line_XY(plNext, -27.511202, 59.749515)
plNext = AddPolyLine_Arc_XY(plNext, -27.608634, 60.119588, -27.93921, 60.312374)
plNext = AddPolyLine_Line_XY(plNext, -36.460656, 61.472092)
ClosePolyLine_Arc_XY(plNext, -36.830729, 61.37466, plStart)
# End of Outline 26 PolyLine

# Outline 27 PolyLine
plStart = GetPoint(-69.344264, 16.985108)
plNext = AddPolyLine_Line_XY(plStart, -67.70997, 14.835902)
plNext = AddPolyLine_Arc_XY(plNext, -67.379395, 14.643116, -67.009322, 14.740548)
plNext = AddPolyLine_Line_XY(plNext, -60.163705, 19.946076)
plNext = AddPolyLine_Arc_XY(plNext, -59.970919, 20.276652, -60.068351, 20.646724)
plNext = AddPolyLine_Line_XY(plNext, -61.702645, 22.79593)
plNext = AddPolyLine_Arc_XY(plNext, -62.03322, 22.988716, -62.403293, 22.891284)
plNext = AddPolyLine_Line_XY(plNext, -69.24891, 17.685755)
ClosePolyLine_Arc_XY(plNext, -69.441696, 17.35518, plStart)
# End of Outline 27 PolyLine

# Outline 28 PolyLine
plStart = GetPoint(-61.044084, -37.023515)
plNext = AddPolyLine_Line_XY(plStart, -58.368746, -37.387612)
plNext = AddPolyLine_Arc_XY(plNext, -57.998674, -37.29018, -57.805888, -36.959605)
plNext = AddPolyLine_Line_XY(plNext, -56.64617, -28.438158)
plNext = AddPolyLine_Arc_XY(plNext, -56.743602, -28.068086, -57.074177, -27.8753)
plNext = AddPolyLine_Line_XY(plNext, -59.749515, -27.511202)
plNext = AddPolyLine_Arc_XY(plNext, -60.119588, -27.608634, -60.312374, -27.93921)
plNext = AddPolyLine_Line_XY(plNext, -61.472092, -36.460656)
ClosePolyLine_Arc_XY(plNext, -61.37466, -36.830729, plStart)
# End of Outline 28 PolyLine

# Outline 29 PolyLine
plStart = GetPoint(-16.985108, -69.344264)
plNext = AddPolyLine_Line_XY(plStart, -14.835902, -67.70997)
plNext = AddPolyLine_Arc_XY(plNext, -14.643116, -67.379395, -14.740548, -67.009322)
plNext = AddPolyLine_Line_XY(plNext, -19.946076, -60.163705)
plNext = AddPolyLine_Arc_XY(plNext, -20.276652, -59.970919, -20.646724, -60.068351)
plNext = AddPolyLine_Line_XY(plNext, -22.79593, -61.702645)
plNext = AddPolyLine_Arc_XY(plNext, -22.988716, -62.03322, -22.891284, -62.403293)
plNext = AddPolyLine_Line_XY(plNext, -17.685755, -69.24891)
ClosePolyLine_Arc_XY(plNext, -17.35518, -69.441696, plStart)
# End of Outline 29 PolyLine

# Outline 30 PolyLine
plStart = GetPoint(37.023515, -61.044084)
plNext = AddPolyLine_Line_XY(plStart, 37.387612, -58.368746)
plNext = AddPolyLine_Arc_XY(plNext, 37.29018, -57.998674, 36.959605, -57.805888)
plNext = AddPolyLine_Line_XY(plNext, 28.438158, -56.64617)
plNext = AddPolyLine_Arc_XY(plNext, 28.068086, -56.743602, 27.8753, -57.074177)
plNext = AddPolyLine_Line_XY(plNext, 27.511202, -59.749515)
plNext = AddPolyLine_Arc_XY(plNext, 27.608634, -60.119588, 27.93921, -60.312374)
plNext = AddPolyLine_Line_XY(plNext, 36.460656, -61.472092)
ClosePolyLine_Arc_XY(plNext, 36.830729, -61.37466, plStart)
# End of Outline 30 PolyLine

# Outline 31 PolyLine
plStart = GetPoint(69.344264, -16.985108)
plNext = AddPolyLine_Line_XY(plStart, 67.70997, -14.835902)
plNext = AddPolyLine_Arc_XY(plNext, 67.379395, -14.643116, 67.009322, -14.740548)
plNext = AddPolyLine_Line_XY(plNext, 60.163705, -19.946076)
plNext = AddPolyLine_Arc_XY(plNext, 59.970919, -20.276652, 60.068351, -20.646724)
plNext = AddPolyLine_Line_XY(plNext, 61.702645, -22.79593)
plNext = AddPolyLine_Arc_XY(plNext, 62.03322, -22.988716, 62.403293, -22.891284)
plNext = AddPolyLine_Line_XY(plNext, 69.24891, -17.685755)
ClosePolyLine_Arc_XY(plNext, 69.441696, -17.35518, plStart)
# End of Outline 31 PolyLine

# Outline 32 PolyLine
plStart = GetPoint(37.387612, 58.368746)
plNext = AddPolyLine_Line_XY(plStart, 37.023515, 61.044084)
plNext = AddPolyLine_Arc_XY(plNext, 36.830729, 61.37466, 36.460656, 61.472092)
plNext = AddPolyLine_Line_XY(plNext, 27.93921, 60.312374)
plNext = AddPolyLine_Arc_XY(plNext, 27.608634, 60.119588, 27.511202, 59.749515)
plNext = AddPolyLine_Line_XY(plNext, 27.8753, 57.074177)
plNext = AddPolyLine_Arc_XY(plNext, 28.068086, 56.743602, 28.438158, 56.64617)
plNext = AddPolyLine_Line_XY(plNext, 36.959605, 57.805888)
ClosePolyLine_Arc_XY(plNext, 37.29018, 57.998674, plStart)
# End of Outline 32 PolyLine

# Outline 33 PolyLine
plStart = GetPoint(-14.835902, 67.70997)
plNext = AddPolyLine_Line_XY(plStart, -16.985108, 69.344264)
plNext = AddPolyLine_Arc_XY(plNext, -17.35518, 69.441696, -17.685756, 69.24891)
plNext = AddPolyLine_Line_XY(plNext, -22.891284, 62.403293)
plNext = AddPolyLine_Arc_XY(plNext, -22.988716, 62.03322, -22.79593, 61.702645)
plNext = AddPolyLine_Line_XY(plNext, -20.646724, 60.068351)
plNext = AddPolyLine_Arc_XY(plNext, -20.276652, 59.970919, -19.946076, 60.163705)
plNext = AddPolyLine_Line_XY(plNext, -14.740548, 67.009322)
ClosePolyLine_Arc_XY(plNext, -14.643116, 67.379395, plStart)
# End of Outline 33 PolyLine

# Outline 34 PolyLine
plStart = GetPoint(-58.368746, 37.387612)
plNext = AddPolyLine_Line_XY(plStart, -61.044084, 37.023515)
plNext = AddPolyLine_Arc_XY(plNext, -61.37466, 36.830729, -61.472092, 36.460656)
plNext = AddPolyLine_Line_XY(plNext, -60.312374, 27.93921)
plNext = AddPolyLine_Arc_XY(plNext, -60.119588, 27.608634, -59.749515, 27.511202)
plNext = AddPolyLine_Line_XY(plNext, -57.074177, 27.8753)
plNext = AddPolyLine_Arc_XY(plNext, -56.743602, 28.068086, -56.64617, 28.438158)
plNext = AddPolyLine_Line_XY(plNext, -57.805888, 36.959605)
ClosePolyLine_Arc_XY(plNext, -57.998674, 37.29018, plStart)
# End of Outline 34 PolyLine

# Outline 35 PolyLine
plStart = GetPoint(-67.70997, -14.835902)
plNext = AddPolyLine_Line_XY(plStart, -69.344264, -16.985108)
plNext = AddPolyLine_Arc_XY(plNext, -69.441696, -17.35518, -69.24891, -17.685756)
plNext = AddPolyLine_Line_XY(plNext, -62.403293, -22.891284)
plNext = AddPolyLine_Arc_XY(plNext, -62.03322, -22.988716, -61.702645, -22.79593)
plNext = AddPolyLine_Line_XY(plNext, -60.068351, -20.646724)
plNext = AddPolyLine_Arc_XY(plNext, -59.970919, -20.276652, -60.163705, -19.946076)
plNext = AddPolyLine_Line_XY(plNext, -67.009322, -14.740548)
ClosePolyLine_Arc_XY(plNext, -67.379395, -14.643116, plStart)
# End of Outline 35 PolyLine

# Outline 36 PolyLine
plStart = GetPoint(-37.387612, -58.368746)
plNext = AddPolyLine_Line_XY(plStart, -37.023515, -61.044084)
plNext = AddPolyLine_Arc_XY(plNext, -36.830729, -61.37466, -36.460656, -61.472092)
plNext = AddPolyLine_Line_XY(plNext, -27.93921, -60.312374)
plNext = AddPolyLine_Arc_XY(plNext, -27.608634, -60.119588, -27.511202, -59.749515)
plNext = AddPolyLine_Line_XY(plNext, -27.8753, -57.074177)
plNext = AddPolyLine_Arc_XY(plNext, -28.068086, -56.743602, -28.438158, -56.64617)
plNext = AddPolyLine_Line_XY(plNext, -36.959605, -57.805888)
ClosePolyLine_Arc_XY(plNext, -37.29018, -57.998674, plStart)
# End of Outline 36 PolyLine

# Outline 37 PolyLine
plStart = GetPoint(14.835902, -67.70997)
plNext = AddPolyLine_Line_XY(plStart, 16.985108, -69.344264)
plNext = AddPolyLine_Arc_XY(plNext, 17.35518, -69.441696, 17.685756, -69.24891)
plNext = AddPolyLine_Line_XY(plNext, 22.891284, -62.403293)
plNext = AddPolyLine_Arc_XY(plNext, 22.988716, -62.03322, 22.79593, -61.702645)
plNext = AddPolyLine_Line_XY(plNext, 20.646724, -60.068351)
plNext = AddPolyLine_Arc_XY(plNext, 20.276652, -59.970919, 19.946076, -60.163705)
plNext = AddPolyLine_Line_XY(plNext, 14.740548, -67.009322)
ClosePolyLine_Arc_XY(plNext, 14.643116, -67.379395, plStart)
# End of Outline 37 PolyLine

# Outline 38 PolyLine
plStart = GetPoint(58.368746, -37.387612)
plNext = AddPolyLine_Line_XY(plStart, 61.044084, -37.023515)
plNext = AddPolyLine_Arc_XY(plNext, 61.37466, -36.830729, 61.472092, -36.460656)
plNext = AddPolyLine_Line_XY(plNext, 60.312374, -27.93921)
plNext = AddPolyLine_Arc_XY(plNext, 60.119588, -27.608634, 59.749515, -27.511202)
plNext = AddPolyLine_Line_XY(plNext, 57.074177, -27.8753)
plNext = AddPolyLine_Arc_XY(plNext, 56.743602, -28.068086, 56.64617, -28.438158)
plNext = AddPolyLine_Line_XY(plNext, 57.805888, -36.959605)
ClosePolyLine_Arc_XY(plNext, 57.998674, -37.29018, plStart)
# End of Outline 38 PolyLine

# Outline 39 PolyLine
plStart = GetPoint(-55.53541, 41.070243)
plNext = AddPolyLine_Arc_XY(plStart, -55.53541, 41.452926, -55.264812, 41.723524)
plNext = AddPolyLine_Line_XY(plNext, -51.75407, 43.177721)
plNext = AddPolyLine_Arc_XY(plNext, -51.371386, 43.177721, -51.100788, 42.907123)
plNext = AddPolyLine_Line_XY(plNext, -44.212486, 26.277292)
plNext = AddPolyLine_Arc_XY(plNext, -44.212486, 25.894608, -44.483084, 25.62401)
plNext = AddPolyLine_Line_XY(plNext, -47.993827, 24.169813)
plNext = AddPolyLine_Arc_XY(plNext, -48.37651, 24.169813, -48.647108, 24.440411)
plNext = AddPolyLine_Line_XY(plNext, -48.455766, 23.978471)
plNext = AddPolyLine_Line_XY(plNext, -47.551612, 21.795649)
plNext = AddPolyLine_Arc_XY(plNext, -47.226453, 21.309014, -46.739818, 20.983855)
plNext = AddPolyLine_Line_XY(plNext, -44.112763, 19.895693)
plNext = AddPolyLine_Arc_XY(plNext, -42.548721, 20.2068, -42.237614, 21.770842)
plNext = AddPolyLine_Line_XY(plNext, -43.928757, 25.85362)
plNext = AddPolyLine_Line_XY(plNext, -51.0084, 42.945392)
plNext = AddPolyLine_Line_XY(plNext, -51.151482, 43.290822)
plNext = AddPolyLine_Arc_XY(plNext, -51.1947, 43.408939, -51.227871, 43.530261)
plNext = AddPolyLine_Line_XY(plNext, -51.62381, 45.260592)
plNext = AddPolyLine_Arc_XY(plNext, -51.773383, 45.651946, -52.025358, 45.986666)
plNext = AddPolyLine_Line_XY(plNext, -53.2755, 47.236808)
plNext = AddPolyLine_Arc_XY(plNext, -53.832268, 47.456012, -54.372208, 47.198125)
plNext = AddPolyLine_Arc_XY(plNext, -55.403224, 45.983505, -56.407113, 44.74637)
plNext = AddPolyLine_Arc_XY(plNext, -56.649229, 44.181281, -56.571444, 43.57145)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 39 PolyLine

# Outline 40 PolyLine
plStart = GetPoint(-45.986666, -52.025358)
plNext = AddPolyLine_Line_XY(plStart, -47.236808, -53.2755)
plNext = AddPolyLine_Arc_XY(plNext, -47.456012, -53.832268, -47.198125, -54.372208)
plNext = AddPolyLine_Arc_XY(plNext, -45.983505, -55.403224, -44.74637, -56.407113)
plNext = AddPolyLine_Arc_XY(plNext, -44.181281, -56.649229, -43.57145, -56.571444)
plNext = AddPolyLine_Line_XY(plNext, -41.070243, -55.53541)
plNext = AddPolyLine_Arc_XY(plNext, -41.452926, -55.53541, -41.723524, -55.264812)
plNext = AddPolyLine_Line_XY(plNext, -43.177721, -51.75407)
plNext = AddPolyLine_Arc_XY(plNext, -43.177721, -51.371386, -42.907123, -51.100788)
plNext = AddPolyLine_Line_XY(plNext, -26.277292, -44.212486)
plNext = AddPolyLine_Arc_XY(plNext, -25.894608, -44.212486, -25.62401, -44.483084)
plNext = AddPolyLine_Line_XY(plNext, -24.169813, -47.993827)
plNext = AddPolyLine_Arc_XY(plNext, -24.169813, -48.37651, -24.440411, -48.647108)
plNext = AddPolyLine_Line_XY(plNext, -23.978471, -48.455766)
plNext = AddPolyLine_Line_XY(plNext, -21.795649, -47.551612)
plNext = AddPolyLine_Arc_XY(plNext, -21.309014, -47.226453, -20.983855, -46.739818)
plNext = AddPolyLine_Line_XY(plNext, -19.895693, -44.112763)
plNext = AddPolyLine_Arc_XY(plNext, -20.2068, -42.548721, -21.770842, -42.237614)
plNext = AddPolyLine_Line_XY(plNext, -25.85362, -43.928757)
plNext = AddPolyLine_Line_XY(plNext, -42.945392, -51.0084)
plNext = AddPolyLine_Line_XY(plNext, -43.290822, -51.151482)
plNext = AddPolyLine_Arc_XY(plNext, -43.408939, -51.1947, -43.530261, -51.227871)
plNext = AddPolyLine_Line_XY(plNext, -45.260592, -51.62381)
ClosePolyLine_Arc_XY(plNext, -45.651946, -51.773383, plStart)
# End of Outline 40 PolyLine

# Outline 41 PolyLine
plStart = GetPoint(-17.124054, 45.260813)
plNext = AddPolyLine_Arc_XY(plStart, -15.798124, 44.374855, -14.472194, 45.260813)
plNext = AddPolyLine_Line_XY(plNext, -12.781051, 49.343592)
plNext = AddPolyLine_Line_XY(plNext, -5.701408, 66.435363)
plNext = AddPolyLine_Line_XY(plNext, -5.558326, 66.780794)
plNext = AddPolyLine_Arc_XY(plNext, -5.505365, 66.894874, -5.443032, 67.004117)
plNext = AddPolyLine_Line_XY(plNext, -4.499474, 68.507618)
plNext = AddPolyLine_Arc_XY(plNext, -4.32851, 68.89011, -4.27, 69.304967)
plNext = AddPolyLine_Line_XY(plNext, -4.27, 71.072935)
plNext = AddPolyLine_Arc_XY(plNext, -4.508694, 71.62163, -5.072842, 71.821071)
plNext = AddPolyLine_Arc_XY(plNext, -6.660747, 71.691244, -8.24539, 71.526314)
plNext = AddPolyLine_Arc_XY(plNext, -8.81617, 71.297938, -9.192384, 70.811719)
plNext = AddPolyLine_Line_XY(plNext, -10.228418, 68.310512)
plNext = AddPolyLine_Arc_XY(plNext, -9.95782, 68.58111, -9.575136, 68.58111)
plNext = AddPolyLine_Line_XY(plNext, -6.064394, 67.126913)
plNext = AddPolyLine_Arc_XY(plNext, -5.793796, 66.856315, -5.793796, 66.473632)
plNext = AddPolyLine_Line_XY(plNext, -12.682098, 49.8438)
plNext = AddPolyLine_Arc_XY(plNext, -12.952696, 49.573202, -13.335379, 49.573202)
plNext = AddPolyLine_Line_XY(plNext, -16.846121, 51.027399)
plNext = AddPolyLine_Arc_XY(plNext, -17.116719, 51.297997, -17.11672, 51.68068)
plNext = AddPolyLine_Line_XY(plNext, -17.308061, 51.218741)
plNext = AddPolyLine_Line_XY(plNext, -18.212216, 49.035918)
plNext = AddPolyLine_Arc_XY(plNext, -18.326397, 48.461893, -18.212216, 47.887868)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 41 PolyLine

# Outline 42 PolyLine
plStart = GetPoint(4.27, -69.304967)
plNext = AddPolyLine_Line_XY(plStart, 4.27, -71.072935)
plNext = AddPolyLine_Arc_XY(plNext, 4.508694, -71.62163, 5.072842, -71.821071)
plNext = AddPolyLine_Arc_XY(plNext, 6.660747, -71.691244, 8.24539, -71.526314)
plNext = AddPolyLine_Arc_XY(plNext, 8.81617, -71.297938, 9.192384, -70.811719)
plNext = AddPolyLine_Line_XY(plNext, 10.228418, -68.310512)
plNext = AddPolyLine_Arc_XY(plNext, 9.95782, -68.58111, 9.575136, -68.58111)
plNext = AddPolyLine_Line_XY(plNext, 6.064394, -67.126913)
plNext = AddPolyLine_Arc_XY(plNext, 5.793796, -66.856315, 5.793796, -66.473632)
plNext = AddPolyLine_Line_XY(plNext, 12.682098, -49.8438)
plNext = AddPolyLine_Arc_XY(plNext, 12.952696, -49.573202, 13.335379, -49.573202)
plNext = AddPolyLine_Line_XY(plNext, 16.846121, -51.027399)
plNext = AddPolyLine_Arc_XY(plNext, 17.116719, -51.297997, 17.11672, -51.68068)
plNext = AddPolyLine_Line_XY(plNext, 17.308061, -51.218741)
plNext = AddPolyLine_Line_XY(plNext, 18.212216, -49.035918)
plNext = AddPolyLine_Arc_XY(plNext, 18.326397, -48.461893, 18.212216, -47.887868)
plNext = AddPolyLine_Line_XY(plNext, 17.124054, -45.260813)
plNext = AddPolyLine_Arc_XY(plNext, 15.798124, -44.374855, 14.472194, -45.260813)
plNext = AddPolyLine_Line_XY(plNext, 12.781051, -49.343592)
plNext = AddPolyLine_Line_XY(plNext, 5.701408, -66.435363)
plNext = AddPolyLine_Line_XY(plNext, 5.558326, -66.780794)
plNext = AddPolyLine_Arc_XY(plNext, 5.505365, -66.894874, 5.443032, -67.004117)
plNext = AddPolyLine_Line_XY(plNext, 4.499474, -68.507618)
ClosePolyLine_Arc_XY(plNext, 4.32851, -68.89011, plStart)
# End of Outline 42 PolyLine

# Outline 43 PolyLine
plStart = GetPoint(20.983855, 46.739818)
plNext = AddPolyLine_Line_XY(plStart, 19.895693, 44.112763)
plNext = AddPolyLine_Arc_XY(plNext, 20.2068, 42.548721, 21.770842, 42.237614)
plNext = AddPolyLine_Line_XY(plNext, 25.85362, 43.928757)
plNext = AddPolyLine_Line_XY(plNext, 42.945392, 51.0084)
plNext = AddPolyLine_Line_XY(plNext, 43.290822, 51.151482)
plNext = AddPolyLine_Arc_XY(plNext, 43.408939, 51.1947, 43.530261, 51.227871)
plNext = AddPolyLine_Line_XY(plNext, 45.260592, 51.62381)
plNext = AddPolyLine_Arc_XY(plNext, 45.651946, 51.773383, 45.986666, 52.025358)
plNext = AddPolyLine_Line_XY(plNext, 47.236808, 53.2755)
plNext = AddPolyLine_Arc_XY(plNext, 47.456012, 53.832268, 47.198125, 54.372208)
plNext = AddPolyLine_Arc_XY(plNext, 45.983505, 55.403224, 44.74637, 56.407113)
plNext = AddPolyLine_Arc_XY(plNext, 44.181281, 56.649229, 43.57145, 56.571444)
plNext = AddPolyLine_Line_XY(plNext, 41.070243, 55.53541)
plNext = AddPolyLine_Arc_XY(plNext, 41.452926, 55.53541, 41.723524, 55.264812)
plNext = AddPolyLine_Line_XY(plNext, 43.177721, 51.75407)
plNext = AddPolyLine_Arc_XY(plNext, 43.177721, 51.371386, 42.907123, 51.100788)
plNext = AddPolyLine_Line_XY(plNext, 26.277292, 44.212486)
plNext = AddPolyLine_Arc_XY(plNext, 25.894608, 44.212486, 25.62401, 44.483084)
plNext = AddPolyLine_Line_XY(plNext, 24.169813, 47.993827)
plNext = AddPolyLine_Arc_XY(plNext, 24.169813, 48.37651, 24.440411, 48.647108)
plNext = AddPolyLine_Line_XY(plNext, 23.978471, 48.455766)
plNext = AddPolyLine_Line_XY(plNext, 21.795649, 47.551612)
ClosePolyLine_Arc_XY(plNext, 21.309014, 47.226453, plStart)
# End of Outline 43 PolyLine

# Outline 44 PolyLine
plStart = GetPoint(43.928757, -25.85362)
plNext = AddPolyLine_Line_XY(plStart, 51.0084, -42.945392)
plNext = AddPolyLine_Line_XY(plNext, 51.151482, -43.290822)
plNext = AddPolyLine_Arc_XY(plNext, 51.1947, -43.408939, 51.227871, -43.530261)
plNext = AddPolyLine_Line_XY(plNext, 51.62381, -45.260592)
plNext = AddPolyLine_Arc_XY(plNext, 51.773383, -45.651946, 52.025358, -45.986666)
plNext = AddPolyLine_Line_XY(plNext, 53.2755, -47.236808)
plNext = AddPolyLine_Arc_XY(plNext, 53.832268, -47.456012, 54.372208, -47.198125)
plNext = AddPolyLine_Arc_XY(plNext, 55.403224, -45.983505, 56.407113, -44.74637)
plNext = AddPolyLine_Arc_XY(plNext, 56.649229, -44.181281, 56.571444, -43.57145)
plNext = AddPolyLine_Line_XY(plNext, 55.53541, -41.070243)
plNext = AddPolyLine_Arc_XY(plNext, 55.53541, -41.452926, 55.264812, -41.723524)
plNext = AddPolyLine_Line_XY(plNext, 51.75407, -43.177721)
plNext = AddPolyLine_Arc_XY(plNext, 51.371386, -43.177721, 51.100788, -42.907123)
plNext = AddPolyLine_Line_XY(plNext, 44.212486, -26.277292)
plNext = AddPolyLine_Arc_XY(plNext, 44.212486, -25.894608, 44.483084, -25.62401)
plNext = AddPolyLine_Line_XY(plNext, 47.993827, -24.169813)
plNext = AddPolyLine_Arc_XY(plNext, 48.37651, -24.169813, 48.647108, -24.440411)
plNext = AddPolyLine_Line_XY(plNext, 48.455766, -23.978471)
plNext = AddPolyLine_Line_XY(plNext, 47.551612, -21.795649)
plNext = AddPolyLine_Arc_XY(plNext, 47.226453, -21.309014, 46.739818, -20.983855)
plNext = AddPolyLine_Line_XY(plNext, 44.112763, -19.895693)
plNext = AddPolyLine_Arc_XY(plNext, 42.548721, -20.2068, 42.237614, -21.770842)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 44 PolyLine

# Outline 45 PolyLine
plStart = GetPoint(47.887868, 18.212216)
plNext = AddPolyLine_Line_XY(plStart, 45.260813, 17.124054)
plNext = AddPolyLine_Arc_XY(plNext, 44.374855, 15.798124, 45.260813, 14.472194)
plNext = AddPolyLine_Line_XY(plNext, 49.343592, 12.781051)
plNext = AddPolyLine_Line_XY(plNext, 66.435363, 5.701408)
plNext = AddPolyLine_Line_XY(plNext, 66.780794, 5.558326)
plNext = AddPolyLine_Arc_XY(plNext, 66.894874, 5.505365, 67.004117, 5.443032)
plNext = AddPolyLine_Line_XY(plNext, 68.507618, 4.499474)
plNext = AddPolyLine_Arc_XY(plNext, 68.89011, 4.32851, 69.304967, 4.27)
plNext = AddPolyLine_Line_XY(plNext, 71.072935, 4.27)
plNext = AddPolyLine_Arc_XY(plNext, 71.62163, 4.508694, 71.821071, 5.072842)
plNext = AddPolyLine_Arc_XY(plNext, 71.691244, 6.660747, 71.526314, 8.24539)
plNext = AddPolyLine_Arc_XY(plNext, 71.297938, 8.81617, 70.811719, 9.192384)
plNext = AddPolyLine_Line_XY(plNext, 68.310512, 10.228418)
plNext = AddPolyLine_Arc_XY(plNext, 68.58111, 9.95782, 68.58111, 9.575136)
plNext = AddPolyLine_Line_XY(plNext, 67.126913, 6.064394)
plNext = AddPolyLine_Arc_XY(plNext, 66.856315, 5.793796, 66.473632, 5.793796)
plNext = AddPolyLine_Line_XY(plNext, 49.8438, 12.682098)
plNext = AddPolyLine_Arc_XY(plNext, 49.573202, 12.952696, 49.573202, 13.335379)
plNext = AddPolyLine_Line_XY(plNext, 51.027399, 16.846121)
plNext = AddPolyLine_Arc_XY(plNext, 51.297997, 17.116719, 51.68068, 17.11672)
plNext = AddPolyLine_Line_XY(plNext, 51.218741, 17.308061)
plNext = AddPolyLine_Line_XY(plNext, 49.035918, 18.212216)
ClosePolyLine_Arc_XY(plNext, 48.461893, 18.326397, plStart)
# End of Outline 45 PolyLine

# Outline 46 PolyLine
plStart = GetPoint(-55.53541, -41.070243)
plNext = AddPolyLine_Line_XY(plStart, -56.571444, -43.57145)
plNext = AddPolyLine_Arc_XY(plNext, -56.649229, -44.181281, -56.407113, -44.74637)
plNext = AddPolyLine_Arc_XY(plNext, -55.403224, -45.983505, -54.372208, -47.198125)
plNext = AddPolyLine_Arc_XY(plNext, -53.832268, -47.456012, -53.2755, -47.236808)
plNext = AddPolyLine_Line_XY(plNext, -52.025358, -45.986666)
plNext = AddPolyLine_Arc_XY(plNext, -51.773383, -45.651946, -51.62381, -45.260592)
plNext = AddPolyLine_Line_XY(plNext, -51.227871, -43.530261)
plNext = AddPolyLine_Arc_XY(plNext, -51.1947, -43.408939, -51.151482, -43.290822)
plNext = AddPolyLine_Line_XY(plNext, -51.0084, -42.945392)
plNext = AddPolyLine_Line_XY(plNext, -43.928757, -25.85362)
plNext = AddPolyLine_Line_XY(plNext, -42.237614, -21.770842)
plNext = AddPolyLine_Arc_XY(plNext, -42.548721, -20.2068, -44.112763, -19.895693)
plNext = AddPolyLine_Line_XY(plNext, -46.739818, -20.983855)
plNext = AddPolyLine_Arc_XY(plNext, -47.226453, -21.309014, -47.551612, -21.795649)
plNext = AddPolyLine_Line_XY(plNext, -48.455766, -23.978471)
plNext = AddPolyLine_Line_XY(plNext, -48.647108, -24.440411)
plNext = AddPolyLine_Arc_XY(plNext, -48.37651, -24.169813, -47.993827, -24.169813)
plNext = AddPolyLine_Line_XY(plNext, -44.483084, -25.62401)
plNext = AddPolyLine_Arc_XY(plNext, -44.212486, -25.894608, -44.212486, -26.277292)
plNext = AddPolyLine_Line_XY(plNext, -51.100788, -42.907123)
plNext = AddPolyLine_Arc_XY(plNext, -51.371386, -43.177721, -51.75407, -43.177721)
plNext = AddPolyLine_Line_XY(plNext, -55.264812, -41.723524)
ClosePolyLine_Arc_XY(plNext, -55.53541, -41.452926, plStart)
# End of Outline 46 PolyLine

# Outline 47 PolyLine
plStart = GetPoint(-45.986666, 52.025358)
plNext = AddPolyLine_Arc_XY(plStart, -45.651946, 51.773383, -45.260592, 51.62381)
plNext = AddPolyLine_Line_XY(plNext, -43.530261, 51.227871)
plNext = AddPolyLine_Arc_XY(plNext, -43.408939, 51.1947, -43.290822, 51.151482)
plNext = AddPolyLine_Line_XY(plNext, -42.945392, 51.0084)
plNext = AddPolyLine_Line_XY(plNext, -25.85362, 43.928757)
plNext = AddPolyLine_Line_XY(plNext, -21.770842, 42.237614)
plNext = AddPolyLine_Arc_XY(plNext, -20.2068, 42.548721, -19.895693, 44.112763)
plNext = AddPolyLine_Line_XY(plNext, -20.983855, 46.739818)
plNext = AddPolyLine_Arc_XY(plNext, -21.309014, 47.226453, -21.795649, 47.551612)
plNext = AddPolyLine_Line_XY(plNext, -23.978471, 48.455766)
plNext = AddPolyLine_Line_XY(plNext, -24.440411, 48.647108)
plNext = AddPolyLine_Arc_XY(plNext, -24.169813, 48.37651, -24.169813, 47.993827)
plNext = AddPolyLine_Line_XY(plNext, -25.62401, 44.483084)
plNext = AddPolyLine_Arc_XY(plNext, -25.894608, 44.212486, -26.277292, 44.212486)
plNext = AddPolyLine_Line_XY(plNext, -42.907123, 51.100788)
plNext = AddPolyLine_Arc_XY(plNext, -43.177721, 51.371386, -43.177721, 51.75407)
plNext = AddPolyLine_Line_XY(plNext, -41.723524, 55.264812)
plNext = AddPolyLine_Arc_XY(plNext, -41.452926, 55.53541, -41.070243, 55.53541)
plNext = AddPolyLine_Line_XY(plNext, -43.57145, 56.571444)
plNext = AddPolyLine_Arc_XY(plNext, -44.181281, 56.649229, -44.74637, 56.407113)
plNext = AddPolyLine_Arc_XY(plNext, -45.983505, 55.403224, -47.198125, 54.372208)
plNext = AddPolyLine_Arc_XY(plNext, -47.456012, 53.832268, -47.236808, 53.2755)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 47 PolyLine

# Outline 48 PolyLine
plStart = GetPoint(-17.124054, -45.260813)
plNext = AddPolyLine_Line_XY(plStart, -18.212216, -47.887868)
plNext = AddPolyLine_Arc_XY(plNext, -18.326397, -48.461893, -18.212216, -49.035918)
plNext = AddPolyLine_Line_XY(plNext, -17.308061, -51.218741)
plNext = AddPolyLine_Line_XY(plNext, -17.116719, -51.68068)
plNext = AddPolyLine_Arc_XY(plNext, -17.11672, -51.297997, -16.846121, -51.027399)
plNext = AddPolyLine_Line_XY(plNext, -13.335379, -49.573202)
plNext = AddPolyLine_Arc_XY(plNext, -12.952696, -49.573202, -12.682098, -49.8438)
plNext = AddPolyLine_Line_XY(plNext, -5.793796, -66.473632)
plNext = AddPolyLine_Arc_XY(plNext, -5.793796, -66.856315, -6.064394, -67.126913)
plNext = AddPolyLine_Line_XY(plNext, -9.575136, -68.58111)
plNext = AddPolyLine_Arc_XY(plNext, -9.95782, -68.58111, -10.228418, -68.310512)
plNext = AddPolyLine_Line_XY(plNext, -9.192384, -70.811719)
plNext = AddPolyLine_Arc_XY(plNext, -8.81617, -71.297938, -8.24539, -71.526314)
plNext = AddPolyLine_Arc_XY(plNext, -6.660747, -71.691244, -5.072842, -71.821071)
plNext = AddPolyLine_Arc_XY(plNext, -4.508694, -71.62163, -4.27, -71.072935)
plNext = AddPolyLine_Line_XY(plNext, -4.27, -69.304967)
plNext = AddPolyLine_Arc_XY(plNext, -4.32851, -68.89011, -4.499474, -68.507618)
plNext = AddPolyLine_Line_XY(plNext, -5.443032, -67.004117)
plNext = AddPolyLine_Arc_XY(plNext, -5.505365, -66.894874, -5.558326, -66.780794)
plNext = AddPolyLine_Line_XY(plNext, -5.701408, -66.435363)
plNext = AddPolyLine_Line_XY(plNext, -12.781051, -49.343592)
plNext = AddPolyLine_Line_XY(plNext, -14.472194, -45.260813)
ClosePolyLine_Arc_XY(plNext, -15.798124, -44.374855, plStart)
# End of Outline 48 PolyLine

# Outline 49 PolyLine
plStart = GetPoint(4.27, 71.072935)
plNext = AddPolyLine_Line_XY(plStart, 4.27, 69.304967)
plNext = AddPolyLine_Arc_XY(plNext, 4.32851, 68.89011, 4.499474, 68.507618)
plNext = AddPolyLine_Line_XY(plNext, 5.443032, 67.004117)
plNext = AddPolyLine_Arc_XY(plNext, 5.505365, 66.894874, 5.558326, 66.780794)
plNext = AddPolyLine_Line_XY(plNext, 5.701408, 66.435363)
plNext = AddPolyLine_Line_XY(plNext, 12.781051, 49.343592)
plNext = AddPolyLine_Line_XY(plNext, 14.472194, 45.260813)
plNext = AddPolyLine_Arc_XY(plNext, 15.798124, 44.374855, 17.124054, 45.260813)
plNext = AddPolyLine_Line_XY(plNext, 18.212216, 47.887868)
plNext = AddPolyLine_Arc_XY(plNext, 18.326397, 48.461893, 18.212216, 49.035918)
plNext = AddPolyLine_Line_XY(plNext, 17.308061, 51.218741)
plNext = AddPolyLine_Line_XY(plNext, 17.116719, 51.68068)
plNext = AddPolyLine_Arc_XY(plNext, 17.11672, 51.297997, 16.846121, 51.027399)
plNext = AddPolyLine_Line_XY(plNext, 13.335379, 49.573202)
plNext = AddPolyLine_Arc_XY(plNext, 12.952696, 49.573202, 12.682098, 49.8438)
plNext = AddPolyLine_Line_XY(plNext, 5.793796, 66.473632)
plNext = AddPolyLine_Arc_XY(plNext, 5.793796, 66.856315, 6.064394, 67.126913)
plNext = AddPolyLine_Line_XY(plNext, 9.575136, 68.58111)
plNext = AddPolyLine_Arc_XY(plNext, 9.95782, 68.58111, 10.228418, 68.310512)
plNext = AddPolyLine_Line_XY(plNext, 9.192384, 70.811719)
plNext = AddPolyLine_Arc_XY(plNext, 8.81617, 71.297938, 8.24539, 71.526314)
plNext = AddPolyLine_Arc_XY(plNext, 6.660747, 71.691244, 5.072842, 71.821071)
ClosePolyLine_Arc_XY(plNext, 4.508694, 71.62163, plStart)
# End of Outline 49 PolyLine

# Outline 50 PolyLine
plStart = GetPoint(20.983855, -46.739818)
plNext = AddPolyLine_Arc_XY(plStart, 21.309014, -47.226453, 21.795649, -47.551612)
plNext = AddPolyLine_Line_XY(plNext, 23.978471, -48.455766)
plNext = AddPolyLine_Line_XY(plNext, 24.440411, -48.647108)
plNext = AddPolyLine_Arc_XY(plNext, 24.169813, -48.37651, 24.169813, -47.993827)
plNext = AddPolyLine_Line_XY(plNext, 25.62401, -44.483084)
plNext = AddPolyLine_Arc_XY(plNext, 25.894608, -44.212486, 26.277292, -44.212486)
plNext = AddPolyLine_Line_XY(plNext, 42.907123, -51.100788)
plNext = AddPolyLine_Arc_XY(plNext, 43.177721, -51.371386, 43.177721, -51.75407)
plNext = AddPolyLine_Line_XY(plNext, 41.723524, -55.264812)
plNext = AddPolyLine_Arc_XY(plNext, 41.452926, -55.53541, 41.070243, -55.53541)
plNext = AddPolyLine_Line_XY(plNext, 43.57145, -56.571444)
plNext = AddPolyLine_Arc_XY(plNext, 44.181281, -56.649229, 44.74637, -56.407113)
plNext = AddPolyLine_Arc_XY(plNext, 45.983505, -55.403224, 47.198125, -54.372208)
plNext = AddPolyLine_Arc_XY(plNext, 47.456012, -53.832268, 47.236808, -53.2755)
plNext = AddPolyLine_Line_XY(plNext, 45.986666, -52.025358)
plNext = AddPolyLine_Arc_XY(plNext, 45.651946, -51.773383, 45.260592, -51.62381)
plNext = AddPolyLine_Line_XY(plNext, 43.530261, -51.227871)
plNext = AddPolyLine_Arc_XY(plNext, 43.408939, -51.1947, 43.290822, -51.151482)
plNext = AddPolyLine_Line_XY(plNext, 42.945392, -51.0084)
plNext = AddPolyLine_Line_XY(plNext, 25.85362, -43.928757)
plNext = AddPolyLine_Line_XY(plNext, 21.770842, -42.237614)
plNext = AddPolyLine_Arc_XY(plNext, 20.2068, -42.548721, 19.895693, -44.112763)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 50 PolyLine

# Outline 51 PolyLine
plStart = GetPoint(43.928757, 25.85362)
plNext = AddPolyLine_Line_XY(plStart, 42.237614, 21.770842)
plNext = AddPolyLine_Arc_XY(plNext, 42.548721, 20.2068, 44.112763, 19.895693)
plNext = AddPolyLine_Line_XY(plNext, 46.739818, 20.983855)
plNext = AddPolyLine_Arc_XY(plNext, 47.226453, 21.309014, 47.551612, 21.795649)
plNext = AddPolyLine_Line_XY(plNext, 48.455766, 23.978471)
plNext = AddPolyLine_Line_XY(plNext, 48.647108, 24.440411)
plNext = AddPolyLine_Arc_XY(plNext, 48.37651, 24.169813, 47.993827, 24.169813)
plNext = AddPolyLine_Line_XY(plNext, 44.483084, 25.62401)
plNext = AddPolyLine_Arc_XY(plNext, 44.212486, 25.894608, 44.212486, 26.277292)
plNext = AddPolyLine_Line_XY(plNext, 51.100788, 42.907123)
plNext = AddPolyLine_Arc_XY(plNext, 51.371386, 43.177721, 51.75407, 43.177721)
plNext = AddPolyLine_Line_XY(plNext, 55.264812, 41.723524)
plNext = AddPolyLine_Arc_XY(plNext, 55.53541, 41.452926, 55.53541, 41.070243)
plNext = AddPolyLine_Line_XY(plNext, 56.571444, 43.57145)
plNext = AddPolyLine_Arc_XY(plNext, 56.649229, 44.181281, 56.407113, 44.74637)
plNext = AddPolyLine_Arc_XY(plNext, 55.403224, 45.983505, 54.372208, 47.198125)
plNext = AddPolyLine_Arc_XY(plNext, 53.832268, 47.456012, 53.2755, 47.236808)
plNext = AddPolyLine_Line_XY(plNext, 52.025358, 45.986666)
plNext = AddPolyLine_Arc_XY(plNext, 51.773383, 45.651946, 51.62381, 45.260592)
plNext = AddPolyLine_Line_XY(plNext, 51.227871, 43.530261)
plNext = AddPolyLine_Arc_XY(plNext, 51.1947, 43.408939, 51.151482, 43.290822)
plNext = AddPolyLine_Line_XY(plNext, 51.0084, 42.945392)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 51 PolyLine

# Outline 52 PolyLine
plStart = GetPoint(47.887868, -18.212216)
plNext = AddPolyLine_Arc_XY(plStart, 48.461893, -18.326397, 49.035918, -18.212216)
plNext = AddPolyLine_Line_XY(plNext, 51.218741, -17.308061)
plNext = AddPolyLine_Line_XY(plNext, 51.68068, -17.116719)
plNext = AddPolyLine_Arc_XY(plNext, 51.297997, -17.11672, 51.027399, -16.846121)
plNext = AddPolyLine_Line_XY(plNext, 49.573202, -13.335379)
plNext = AddPolyLine_Arc_XY(plNext, 49.573202, -12.952696, 49.8438, -12.682098)
plNext = AddPolyLine_Line_XY(plNext, 66.473632, -5.793796)
plNext = AddPolyLine_Arc_XY(plNext, 66.856315, -5.793796, 67.126913, -6.064394)
plNext = AddPolyLine_Line_XY(plNext, 68.58111, -9.575136)
plNext = AddPolyLine_Arc_XY(plNext, 68.58111, -9.95782, 68.310512, -10.228418)
plNext = AddPolyLine_Line_XY(plNext, 70.811719, -9.192384)
plNext = AddPolyLine_Arc_XY(plNext, 71.297938, -8.81617, 71.526314, -8.24539)
plNext = AddPolyLine_Arc_XY(plNext, 71.691244, -6.660747, 71.821071, -5.072842)
plNext = AddPolyLine_Arc_XY(plNext, 71.62163, -4.508694, 71.072935, -4.27)
plNext = AddPolyLine_Line_XY(plNext, 69.304967, -4.27)
plNext = AddPolyLine_Arc_XY(plNext, 68.89011, -4.32851, 68.507618, -4.499474)
plNext = AddPolyLine_Line_XY(plNext, 67.004117, -5.443032)
plNext = AddPolyLine_Arc_XY(plNext, 66.894874, -5.505365, 66.780794, -5.558326)
plNext = AddPolyLine_Line_XY(plNext, 66.435363, -5.701408)
plNext = AddPolyLine_Line_XY(plNext, 49.343592, -12.781051)
plNext = AddPolyLine_Line_XY(plNext, 45.260813, -14.472194)
plNext = AddPolyLine_Arc_XY(plNext, 44.374855, -15.798124, 45.260813, -17.124054)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 52 PolyLine

# Outline 53 PolyLine
plStart = GetPoint(9.575136, 68.58111)
plNext = AddPolyLine_Line_XY(plStart, 6.064394, 67.126913)
plNext = AddPolyLine_Arc_XY(plNext, 5.793796, 66.856315, 5.793796, 66.473632)
plNext = AddPolyLine_Line_XY(plNext, 12.682098, 49.8438)
plNext = AddPolyLine_Arc_XY(plNext, 12.952696, 49.573202, 13.335379, 49.573202)
plNext = AddPolyLine_Line_XY(plNext, 16.846121, 51.027399)
plNext = AddPolyLine_Arc_XY(plNext, 17.11672, 51.297997, 17.116719, 51.68068)
plNext = AddPolyLine_Line_XY(plNext, 10.228418, 68.310512)
ClosePolyLine_Arc_XY(plNext, 9.95782, 68.58111, plStart)
# End of Outline 53 PolyLine

# Outline 54 PolyLine
plStart = GetPoint(-41.723524, 55.264812)
plNext = AddPolyLine_Line_XY(plStart, -43.177721, 51.75407)
plNext = AddPolyLine_Arc_XY(plNext, -43.177721, 51.371386, -42.907123, 51.100788)
plNext = AddPolyLine_Line_XY(plNext, -26.277292, 44.212486)
plNext = AddPolyLine_Arc_XY(plNext, -25.894608, 44.212486, -25.62401, 44.483084)
plNext = AddPolyLine_Line_XY(plNext, -24.169813, 47.993827)
plNext = AddPolyLine_Arc_XY(plNext, -24.169813, 48.37651, -24.440411, 48.647108)
plNext = AddPolyLine_Line_XY(plNext, -41.070243, 55.53541)
ClosePolyLine_Arc_XY(plNext, -41.452926, 55.53541, plStart)
# End of Outline 54 PolyLine

# Outline 55 PolyLine
plStart = GetPoint(-68.58111, 9.575136)
plNext = AddPolyLine_Line_XY(plStart, -67.126913, 6.064394)
plNext = AddPolyLine_Arc_XY(plNext, -66.856315, 5.793796, -66.473632, 5.793796)
plNext = AddPolyLine_Line_XY(plNext, -49.8438, 12.682098)
plNext = AddPolyLine_Arc_XY(plNext, -49.573202, 12.952696, -49.573202, 13.335379)
plNext = AddPolyLine_Line_XY(plNext, -51.027399, 16.846121)
plNext = AddPolyLine_Arc_XY(plNext, -51.297997, 17.11672, -51.68068, 17.116719)
plNext = AddPolyLine_Line_XY(plNext, -68.310512, 10.228418)
ClosePolyLine_Arc_XY(plNext, -68.58111, 9.95782, plStart)
# End of Outline 55 PolyLine

# Outline 56 PolyLine
plStart = GetPoint(-55.264812, -41.723524)
plNext = AddPolyLine_Line_XY(plStart, -51.75407, -43.177721)
plNext = AddPolyLine_Arc_XY(plNext, -51.371386, -43.177721, -51.100788, -42.907123)
plNext = AddPolyLine_Line_XY(plNext, -44.212486, -26.277292)
plNext = AddPolyLine_Arc_XY(plNext, -44.212486, -25.894608, -44.483084, -25.62401)
plNext = AddPolyLine_Line_XY(plNext, -47.993827, -24.169813)
plNext = AddPolyLine_Arc_XY(plNext, -48.37651, -24.169813, -48.647108, -24.440411)
plNext = AddPolyLine_Line_XY(plNext, -55.53541, -41.070243)
ClosePolyLine_Arc_XY(plNext, -55.53541, -41.452926, plStart)
# End of Outline 56 PolyLine

# Outline 57 PolyLine
plStart = GetPoint(-9.575136, -68.58111)
plNext = AddPolyLine_Line_XY(plStart, -6.064394, -67.126913)
plNext = AddPolyLine_Arc_XY(plNext, -5.793796, -66.856315, -5.793796, -66.473632)
plNext = AddPolyLine_Line_XY(plNext, -12.682098, -49.8438)
plNext = AddPolyLine_Arc_XY(plNext, -12.952696, -49.573202, -13.335379, -49.573202)
plNext = AddPolyLine_Line_XY(plNext, -16.846121, -51.027399)
plNext = AddPolyLine_Arc_XY(plNext, -17.11672, -51.297997, -17.116719, -51.68068)
plNext = AddPolyLine_Line_XY(plNext, -10.228418, -68.310512)
ClosePolyLine_Arc_XY(plNext, -9.95782, -68.58111, plStart)
# End of Outline 57 PolyLine

# Outline 58 PolyLine
plStart = GetPoint(41.723524, -55.264812)
plNext = AddPolyLine_Line_XY(plStart, 43.177721, -51.75407)
plNext = AddPolyLine_Arc_XY(plNext, 43.177721, -51.371386, 42.907123, -51.100788)
plNext = AddPolyLine_Line_XY(plNext, 26.277292, -44.212486)
plNext = AddPolyLine_Arc_XY(plNext, 25.894608, -44.212486, 25.62401, -44.483084)
plNext = AddPolyLine_Line_XY(plNext, 24.169813, -47.993827)
plNext = AddPolyLine_Arc_XY(plNext, 24.169813, -48.37651, 24.440411, -48.647108)
plNext = AddPolyLine_Line_XY(plNext, 41.070243, -55.53541)
ClosePolyLine_Arc_XY(plNext, 41.452926, -55.53541, plStart)
# End of Outline 58 PolyLine

# Outline 59 PolyLine
plStart = GetPoint(68.58111, -9.575136)
plNext = AddPolyLine_Line_XY(plStart, 67.126913, -6.064394)
plNext = AddPolyLine_Arc_XY(plNext, 66.856315, -5.793796, 66.473632, -5.793796)
plNext = AddPolyLine_Line_XY(plNext, 49.8438, -12.682098)
plNext = AddPolyLine_Arc_XY(plNext, 49.573202, -12.952696, 49.573202, -13.335379)
plNext = AddPolyLine_Line_XY(plNext, 51.027399, -16.846121)
plNext = AddPolyLine_Arc_XY(plNext, 51.297997, -17.11672, 51.68068, -17.116719)
plNext = AddPolyLine_Line_XY(plNext, 68.310512, -10.228418)
ClosePolyLine_Arc_XY(plNext, 68.58111, -9.95782, plStart)
# End of Outline 59 PolyLine

# Outline 60 PolyLine
plStart = GetPoint(43.177721, 51.75407)
plNext = AddPolyLine_Line_XY(plStart, 41.723524, 55.264812)
plNext = AddPolyLine_Arc_XY(plNext, 41.452926, 55.53541, 41.070243, 55.53541)
plNext = AddPolyLine_Line_XY(plNext, 24.440411, 48.647108)
plNext = AddPolyLine_Arc_XY(plNext, 24.169813, 48.37651, 24.169813, 47.993827)
plNext = AddPolyLine_Line_XY(plNext, 25.62401, 44.483084)
plNext = AddPolyLine_Arc_XY(plNext, 25.894608, 44.212486, 26.277292, 44.212486)
plNext = AddPolyLine_Line_XY(plNext, 42.907123, 51.100788)
ClosePolyLine_Arc_XY(plNext, 43.177721, 51.371386, plStart)
# End of Outline 60 PolyLine

# Outline 61 PolyLine
plStart = GetPoint(-6.064394, 67.126913)
plNext = AddPolyLine_Line_XY(plStart, -9.575136, 68.58111)
plNext = AddPolyLine_Arc_XY(plNext, -9.95782, 68.58111, -10.228418, 68.310512)
plNext = AddPolyLine_Line_XY(plNext, -17.11672, 51.68068)
plNext = AddPolyLine_Arc_XY(plNext, -17.116719, 51.297997, -16.846121, 51.027399)
plNext = AddPolyLine_Line_XY(plNext, -13.335379, 49.573202)
plNext = AddPolyLine_Arc_XY(plNext, -12.952696, 49.573202, -12.682098, 49.8438)
plNext = AddPolyLine_Line_XY(plNext, -5.793796, 66.473632)
ClosePolyLine_Arc_XY(plNext, -5.793796, 66.856315, plStart)
# End of Outline 61 PolyLine

# Outline 62 PolyLine
plStart = GetPoint(-51.75407, 43.177721)
plNext = AddPolyLine_Line_XY(plStart, -55.264812, 41.723524)
plNext = AddPolyLine_Arc_XY(plNext, -55.53541, 41.452926, -55.53541, 41.070243)
plNext = AddPolyLine_Line_XY(plNext, -48.647108, 24.440411)
plNext = AddPolyLine_Arc_XY(plNext, -48.37651, 24.169813, -47.993827, 24.169813)
plNext = AddPolyLine_Line_XY(plNext, -44.483084, 25.62401)
plNext = AddPolyLine_Arc_XY(plNext, -44.212486, 25.894608, -44.212486, 26.277292)
plNext = AddPolyLine_Line_XY(plNext, -51.100788, 42.907123)
ClosePolyLine_Arc_XY(plNext, -51.371386, 43.177721, plStart)
# End of Outline 62 PolyLine

# Outline 63 PolyLine
plStart = GetPoint(-67.126913, -6.064394)
plNext = AddPolyLine_Line_XY(plStart, -68.58111, -9.575136)
plNext = AddPolyLine_Arc_XY(plNext, -68.58111, -9.95782, -68.310512, -10.228418)
plNext = AddPolyLine_Line_XY(plNext, -51.68068, -17.11672)
plNext = AddPolyLine_Arc_XY(plNext, -51.297997, -17.116719, -51.027399, -16.846121)
plNext = AddPolyLine_Line_XY(plNext, -49.573202, -13.335379)
plNext = AddPolyLine_Arc_XY(plNext, -49.573202, -12.952696, -49.8438, -12.682098)
plNext = AddPolyLine_Line_XY(plNext, -66.473632, -5.793796)
ClosePolyLine_Arc_XY(plNext, -66.856315, -5.793796, plStart)
# End of Outline 63 PolyLine

# Outline 64 PolyLine
plStart = GetPoint(-43.177721, -51.75407)
plNext = AddPolyLine_Line_XY(plStart, -41.723524, -55.264812)
plNext = AddPolyLine_Arc_XY(plNext, -41.452926, -55.53541, -41.070243, -55.53541)
plNext = AddPolyLine_Line_XY(plNext, -24.440411, -48.647108)
plNext = AddPolyLine_Arc_XY(plNext, -24.169813, -48.37651, -24.169813, -47.993827)
plNext = AddPolyLine_Line_XY(plNext, -25.62401, -44.483084)
plNext = AddPolyLine_Arc_XY(plNext, -25.894608, -44.212486, -26.277292, -44.212486)
plNext = AddPolyLine_Line_XY(plNext, -42.907123, -51.100788)
ClosePolyLine_Arc_XY(plNext, -43.177721, -51.371386, plStart)
# End of Outline 64 PolyLine

# Outline 65 PolyLine
plStart = GetPoint(6.064394, -67.126913)
plNext = AddPolyLine_Line_XY(plStart, 9.575136, -68.58111)
plNext = AddPolyLine_Arc_XY(plNext, 9.95782, -68.58111, 10.228418, -68.310512)
plNext = AddPolyLine_Line_XY(plNext, 17.11672, -51.68068)
plNext = AddPolyLine_Arc_XY(plNext, 17.116719, -51.297997, 16.846121, -51.027399)
plNext = AddPolyLine_Line_XY(plNext, 13.335379, -49.573202)
plNext = AddPolyLine_Arc_XY(plNext, 12.952696, -49.573202, 12.682098, -49.8438)
plNext = AddPolyLine_Line_XY(plNext, 5.793796, -66.473632)
ClosePolyLine_Arc_XY(plNext, 5.793796, -66.856315, plStart)
# End of Outline 65 PolyLine

# Outline 66 PolyLine
plStart = GetPoint(51.75407, -43.177721)
plNext = AddPolyLine_Line_XY(plStart, 55.264812, -41.723524)
plNext = AddPolyLine_Arc_XY(plNext, 55.53541, -41.452926, 55.53541, -41.070243)
plNext = AddPolyLine_Line_XY(plNext, 48.647108, -24.440411)
plNext = AddPolyLine_Arc_XY(plNext, 48.37651, -24.169813, 47.993827, -24.169813)
plNext = AddPolyLine_Line_XY(plNext, 44.483084, -25.62401)
plNext = AddPolyLine_Arc_XY(plNext, 44.212486, -25.894608, 44.212486, -26.277292)
plNext = AddPolyLine_Line_XY(plNext, 51.100788, -42.907123)
ClosePolyLine_Arc_XY(plNext, 51.371386, -43.177721, plStart)
# End of Outline 66 PolyLine

# End of component rotor_lamination


# Create new component magnet_p_1_l1_m0_s0
newComp = CreateNamedComponentWithColour_Radial("magnet_p_1_l1_m0_s0", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(67.126913, 6.064394)
plNext = AddPolyLine_Line_XY(plStart, 68.58111, 9.575136)
plNext = AddPolyLine_Arc_XY(plNext, 68.58111, 9.95782, 68.310512, 10.228418)
plNext = AddPolyLine_Line_XY(plNext, 51.68068, 17.11672)
plNext = AddPolyLine_Arc_XY(plNext, 51.297997, 17.116719, 51.027399, 16.846121)
plNext = AddPolyLine_Line_XY(plNext, 49.573202, 13.335379)
plNext = AddPolyLine_Arc_XY(plNext, 49.573202, 12.952696, 49.8438, 12.682098)
plNext = AddPolyLine_Line_XY(plNext, 66.473632, 5.793796)
ClosePolyLine_Arc_XY(plNext, 66.856315, 5.793796, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p_1_l1_m0_s0


# Create new component magnet_p_1_l1_m0_s_1
newComp = CreateNamedComponentWithColour_Radial("magnet_p_1_l1_m0_s_1", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(55.264812, 41.723524)
plNext = AddPolyLine_Line_XY(plStart, 51.75407, 43.177721)
plNext = AddPolyLine_Arc_XY(plNext, 51.371386, 43.177721, 51.100788, 42.907123)
plNext = AddPolyLine_Line_XY(plNext, 44.212486, 26.277292)
plNext = AddPolyLine_Arc_XY(plNext, 44.212486, 25.894608, 44.483084, 25.62401)
plNext = AddPolyLine_Line_XY(plNext, 47.993827, 24.169813)
plNext = AddPolyLine_Arc_XY(plNext, 48.37651, 24.169813, 48.647108, 24.440411)
plNext = AddPolyLine_Line_XY(plNext, 55.53541, 41.070243)
ClosePolyLine_Arc_XY(plNext, 55.53541, 41.452926, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p_1_l1_m0_s_1


# Create new component fluid_rotor_pocket
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-71.526314, 8.24539)
plNext = AddPolyLine_Arc_XY(plStart, -71.691244, 6.660747, -71.821071, 5.072842)
plNext = AddPolyLine_Arc_XY(plNext, -71.62163, 4.508694, -71.072935, 4.27)
plNext = AddPolyLine_Line_XY(plNext, -69.304967, 4.27)
plNext = AddPolyLine_Arc_XY(plNext, -68.89011, 4.32851, -68.507618, 4.499474)
plNext = AddPolyLine_Line_XY(plNext, -67.004117, 5.443032)
plNext = AddPolyLine_Arc_XY(plNext, -66.894874, 5.505365, -66.780794, 5.558326)
plNext = AddPolyLine_Line_XY(plNext, -66.435363, 5.701408)
plNext = AddPolyLine_Line_XY(plNext, -49.343592, 12.781051)
plNext = AddPolyLine_Line_XY(plNext, -45.260813, 14.472194)
plNext = AddPolyLine_Arc_XY(plNext, -44.374855, 15.798124, -45.260813, 17.124054)
plNext = AddPolyLine_Line_XY(plNext, -47.887868, 18.212216)
plNext = AddPolyLine_Arc_XY(plNext, -48.461893, 18.326397, -49.035918, 18.212216)
plNext = AddPolyLine_Line_XY(plNext, -51.218741, 17.308061)
plNext = AddPolyLine_Line_XY(plNext, -51.68068, 17.116719)
plNext = AddPolyLine_Arc_XY(plNext, -51.297997, 17.11672, -51.027399, 16.846121)
plNext = AddPolyLine_Line_XY(plNext, -49.573202, 13.335379)
plNext = AddPolyLine_Arc_XY(plNext, -49.573202, 12.952696, -49.8438, 12.682098)
plNext = AddPolyLine_Line_XY(plNext, -66.473632, 5.793796)
plNext = AddPolyLine_Arc_XY(plNext, -66.856315, 5.793796, -67.126913, 6.064394)
plNext = AddPolyLine_Line_XY(plNext, -68.58111, 9.575136)
plNext = AddPolyLine_Arc_XY(plNext, -68.58111, 9.95782, -68.310512, 10.228418)
plNext = AddPolyLine_Line_XY(plNext, -70.811719, 9.192384)
ClosePolyLine_Arc_XY(plNext, -71.297938, 8.81617, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket


# Create new component fluid_rotor_pocket_1
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_1", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-71.821071, -5.072842)
plNext = AddPolyLine_Arc_XY(plStart, -71.691244, -6.660747, -71.526314, -8.24539)
plNext = AddPolyLine_Arc_XY(plNext, -71.297938, -8.81617, -70.811719, -9.192384)
plNext = AddPolyLine_Line_XY(plNext, -68.310512, -10.228418)
plNext = AddPolyLine_Arc_XY(plNext, -68.58111, -9.95782, -68.58111, -9.575136)
plNext = AddPolyLine_Line_XY(plNext, -67.126913, -6.064394)
plNext = AddPolyLine_Arc_XY(plNext, -66.856315, -5.793796, -66.473632, -5.793796)
plNext = AddPolyLine_Line_XY(plNext, -49.8438, -12.682098)
plNext = AddPolyLine_Arc_XY(plNext, -49.573202, -12.952696, -49.573202, -13.335379)
plNext = AddPolyLine_Line_XY(plNext, -51.027399, -16.846121)
plNext = AddPolyLine_Arc_XY(plNext, -51.297997, -17.116719, -51.68068, -17.11672)
plNext = AddPolyLine_Line_XY(plNext, -51.218741, -17.308061)
plNext = AddPolyLine_Line_XY(plNext, -49.035918, -18.212216)
plNext = AddPolyLine_Arc_XY(plNext, -48.461893, -18.326397, -47.887868, -18.212216)
plNext = AddPolyLine_Line_XY(plNext, -45.260813, -17.124054)
plNext = AddPolyLine_Arc_XY(plNext, -44.374855, -15.798124, -45.260813, -14.472194)
plNext = AddPolyLine_Line_XY(plNext, -49.343592, -12.781051)
plNext = AddPolyLine_Line_XY(plNext, -66.435363, -5.701408)
plNext = AddPolyLine_Line_XY(plNext, -66.780794, -5.558326)
plNext = AddPolyLine_Arc_XY(plNext, -66.894874, -5.505365, -67.004117, -5.443032)
plNext = AddPolyLine_Line_XY(plNext, -68.507618, -4.499474)
plNext = AddPolyLine_Arc_XY(plNext, -68.89011, -4.32851, -69.304967, -4.27)
plNext = AddPolyLine_Line_XY(plNext, -71.072935, -4.27)
ClosePolyLine_Arc_XY(plNext, -71.62163, -4.508694, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_1


# Create new component magnet_p_1_l1_m0_s_2
newComp = CreateNamedComponentWithColour_Radial("magnet_p_1_l1_m0_s_2", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(67.70997, 14.835902)
plNext = AddPolyLine_Line_XY(plStart, 69.344264, 16.985108)
plNext = AddPolyLine_Arc_XY(plNext, 69.441696, 17.35518, 69.24891, 17.685756)
plNext = AddPolyLine_Line_XY(plNext, 62.403293, 22.891284)
plNext = AddPolyLine_Arc_XY(plNext, 62.03322, 22.988716, 61.702645, 22.79593)
plNext = AddPolyLine_Line_XY(plNext, 60.068351, 20.646724)
plNext = AddPolyLine_Arc_XY(plNext, 59.970919, 20.276652, 60.163705, 19.946076)
plNext = AddPolyLine_Line_XY(plNext, 67.009322, 14.740548)
ClosePolyLine_Arc_XY(plNext, 67.379395, 14.643116, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p_1_l1_m0_s_2


# Create new component magnet_p_1_l1_m0_s_3
newComp = CreateNamedComponentWithColour_Radial("magnet_p_1_l1_m0_s_3", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(61.044084, 37.023515)
plNext = AddPolyLine_Line_XY(plStart, 58.368746, 37.387612)
plNext = AddPolyLine_Arc_XY(plNext, 57.998674, 37.29018, 57.805888, 36.959605)
plNext = AddPolyLine_Line_XY(plNext, 56.64617, 28.438158)
plNext = AddPolyLine_Arc_XY(plNext, 56.743602, 28.068086, 57.074177, 27.8753)
plNext = AddPolyLine_Line_XY(plNext, 59.749515, 27.511202)
plNext = AddPolyLine_Arc_XY(plNext, 60.119588, 27.608634, 60.312374, 27.93921)
plNext = AddPolyLine_Line_XY(plNext, 61.472092, 36.460656)
ClosePolyLine_Arc_XY(plNext, 61.37466, 36.830729, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p_1_l1_m0_s_3


# Create new component fluid_rotor_pocket_2
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_2", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-71.847535, 15.497795)
plNext = AddPolyLine_Arc_XY(plStart, -72.099381, 14.280382, -72.330599, 13.058884)
plNext = AddPolyLine_Arc_XY(plNext, -72.319762, 13.017939, -72.281395, 13)
plNext = AddPolyLine_Line_XY(plNext, -72.241206, 13)
plNext = AddPolyLine_Arc_XY(plNext, -72.142157, 13.006847, -72.044993, 13.027258)
plNext = AddPolyLine_Line_XY(plNext, -67.587327, 14.290156)
plNext = AddPolyLine_Arc_XY(plNext, -67.357268, 14.379279, -67.147793, 14.509625)
plNext = AddPolyLine_Line_XY(plNext, -66.948793, 14.660948)
plNext = AddPolyLine_Line_XY(plNext, -59.705175, 20.169123)
plNext = AddPolyLine_Line_XY(plNext, -57.987233, 21.475476)
plNext = AddPolyLine_Arc_XY(plNext, -57.498979, 22.6434, -58.268499, 23.648526)
plNext = AddPolyLine_Line_XY(plNext, -59.504488, 24.160489)
plNext = AddPolyLine_Arc_XY(plNext, -60.271057, 24.262261, -60.986454, 23.968673)
plNext = AddPolyLine_Line_XY(plNext, -62.005292, 23.193931)
plNext = AddPolyLine_Line_XY(plNext, -62.403293, 22.891284)
plNext = AddPolyLine_Arc_XY(plNext, -62.03322, 22.988716, -61.702645, 22.79593)
plNext = AddPolyLine_Line_XY(plNext, -60.068351, 20.646724)
plNext = AddPolyLine_Arc_XY(plNext, -59.970919, 20.276652, -60.163705, 19.946076)
plNext = AddPolyLine_Line_XY(plNext, -67.009322, 14.740548)
plNext = AddPolyLine_Arc_XY(plNext, -67.379395, 14.643116, -67.70997, 14.835902)
plNext = AddPolyLine_Line_XY(plNext, -69.344264, 16.985108)
plNext = AddPolyLine_Arc_XY(plNext, -69.441696, 17.35518, -69.24891, 17.685755)
plNext = AddPolyLine_Line_XY(plNext, -71.586427, 15.908267)
ClosePolyLine_Arc_XY(plNext, -71.753703, 15.72639, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_2


# Create new component fluid_rotor_pocket_3
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_3", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-72.330599, -13.058884)
plNext = AddPolyLine_Arc_XY(plStart, -72.099381, -14.280382, -71.847535, -15.497795)
plNext = AddPolyLine_Arc_XY(plNext, -71.753703, -15.72639, -71.586427, -15.908267)
plNext = AddPolyLine_Line_XY(plNext, -69.24891, -17.685755)
plNext = AddPolyLine_Arc_XY(plNext, -69.441696, -17.35518, -69.344264, -16.985108)
plNext = AddPolyLine_Line_XY(plNext, -67.70997, -14.835902)
plNext = AddPolyLine_Arc_XY(plNext, -67.379395, -14.643116, -67.009322, -14.740548)
plNext = AddPolyLine_Line_XY(plNext, -60.163705, -19.946076)
plNext = AddPolyLine_Arc_XY(plNext, -59.970919, -20.276652, -60.068351, -20.646724)
plNext = AddPolyLine_Line_XY(plNext, -61.702645, -22.79593)
plNext = AddPolyLine_Arc_XY(plNext, -62.03322, -22.988716, -62.403293, -22.891284)
plNext = AddPolyLine_Line_XY(plNext, -62.005292, -23.193931)
plNext = AddPolyLine_Line_XY(plNext, -60.986454, -23.968673)
plNext = AddPolyLine_Arc_XY(plNext, -60.271057, -24.262261, -59.504488, -24.160489)
plNext = AddPolyLine_Line_XY(plNext, -58.268499, -23.648526)
plNext = AddPolyLine_Arc_XY(plNext, -57.498979, -22.6434, -57.987233, -21.475476)
plNext = AddPolyLine_Line_XY(plNext, -59.705175, -20.169123)
plNext = AddPolyLine_Line_XY(plNext, -66.948793, -14.660948)
plNext = AddPolyLine_Line_XY(plNext, -67.147793, -14.509625)
plNext = AddPolyLine_Arc_XY(plNext, -67.357268, -14.379279, -67.587327, -14.290156)
plNext = AddPolyLine_Line_XY(plNext, -72.044993, -13.027258)
plNext = AddPolyLine_Arc_XY(plNext, -72.142157, -13.006847, -72.241206, -13)
plNext = AddPolyLine_Line_XY(plNext, -72.281395, -13)
ClosePolyLine_Arc_XY(plNext, -72.319762, -13.017939, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_3


# Create new component fluid_rotor_pocket_4
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_4", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-61.472092, 36.460656)
plNext = AddPolyLine_Arc_XY(plStart, -61.37466, 36.830729, -61.044084, 37.023515)
plNext = AddPolyLine_Line_XY(plNext, -58.368746, 37.387612)
plNext = AddPolyLine_Arc_XY(plNext, -57.998674, 37.29018, -57.805888, 36.959605)
plNext = AddPolyLine_Line_XY(plNext, -56.64617, 28.438158)
plNext = AddPolyLine_Arc_XY(plNext, -56.743602, 28.068086, -57.074177, 27.8753)
plNext = AddPolyLine_Line_XY(plNext, -59.749515, 27.511202)
plNext = AddPolyLine_Arc_XY(plNext, -60.119588, 27.608634, -60.312374, 27.93921)
plNext = AddPolyLine_Line_XY(plNext, -60.244948, 27.443777)
plNext = AddPolyLine_Line_XY(plNext, -60.072346, 26.175524)
plNext = AddPolyLine_Arc_XY(plNext, -59.774083, 25.462064, -59.160073, 24.991981)
plNext = AddPolyLine_Line_XY(plNext, -57.924084, 24.480018)
plNext = AddPolyLine_Arc_XY(plNext, -56.66922, 24.646616, -56.188621, 25.817711)
plNext = AddPolyLine_Line_XY(plNext, -56.479658, 27.95621)
plNext = AddPolyLine_Line_XY(plNext, -57.706801, 36.97309)
plNext = AddPolyLine_Line_XY(plNext, -57.740514, 37.220806)
plNext = AddPolyLine_Arc_XY(plNext, -57.796466, 37.461096, -57.896123, 37.686791)
plNext = AddPolyLine_Line_XY(plNext, -60.155165, 41.73184)
plNext = AddPolyLine_Arc_XY(plNext, -60.209438, 41.814979, -60.274635, 41.889858)
plNext = AddPolyLine_Line_XY(plNext, -60.303052, 41.918276)
plNext = AddPolyLine_Arc_XY(plNext, -60.342867, 41.932721, -60.379482, 41.911432)
plNext = AddPolyLine_Arc_XY(plNext, -61.079716, 40.884206, -61.762475, 39.845284)
plNext = AddPolyLine_Arc_XY(plNext, -61.857767, 39.617293, -61.868091, 39.370404)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_4


# Create new component fluid_rotor_pocket_5
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_5", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-41.889858, -60.274635)
plNext = AddPolyLine_Line_XY(plStart, -41.918276, -60.303052)
plNext = AddPolyLine_Arc_XY(plNext, -41.932721, -60.342867, -41.911432, -60.379482)
plNext = AddPolyLine_Arc_XY(plNext, -40.884206, -61.079716, -39.845284, -61.762475)
plNext = AddPolyLine_Arc_XY(plNext, -39.617293, -61.857767, -39.370404, -61.868091)
plNext = AddPolyLine_Line_XY(plNext, -36.460656, -61.472092)
plNext = AddPolyLine_Arc_XY(plNext, -36.830729, -61.37466, -37.023515, -61.044084)
plNext = AddPolyLine_Line_XY(plNext, -37.387612, -58.368746)
plNext = AddPolyLine_Arc_XY(plNext, -37.29018, -57.998674, -36.959605, -57.805888)
plNext = AddPolyLine_Line_XY(plNext, -28.438158, -56.64617)
plNext = AddPolyLine_Arc_XY(plNext, -28.068086, -56.743602, -27.8753, -57.074177)
plNext = AddPolyLine_Line_XY(plNext, -27.511202, -59.749515)
plNext = AddPolyLine_Arc_XY(plNext, -27.608634, -60.119588, -27.93921, -60.312374)
plNext = AddPolyLine_Line_XY(plNext, -27.443777, -60.244948)
plNext = AddPolyLine_Line_XY(plNext, -26.175524, -60.072346)
plNext = AddPolyLine_Arc_XY(plNext, -25.462064, -59.774083, -24.991981, -59.160073)
plNext = AddPolyLine_Line_XY(plNext, -24.480018, -57.924084)
plNext = AddPolyLine_Arc_XY(plNext, -24.646616, -56.66922, -25.817711, -56.188621)
plNext = AddPolyLine_Line_XY(plNext, -27.95621, -56.479658)
plNext = AddPolyLine_Line_XY(plNext, -36.97309, -57.706801)
plNext = AddPolyLine_Line_XY(plNext, -37.220806, -57.740514)
plNext = AddPolyLine_Arc_XY(plNext, -37.461096, -57.796466, -37.686791, -57.896123)
plNext = AddPolyLine_Line_XY(plNext, -41.73184, -60.155165)
ClosePolyLine_Arc_XY(plNext, -41.814979, -60.209438, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_5


# Create new component fluid_rotor_pocket_6
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_6", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-23.648526, 58.268499)
plNext = AddPolyLine_Arc_XY(plStart, -22.6434, 57.498979, -21.475476, 57.987233)
plNext = AddPolyLine_Line_XY(plNext, -20.169123, 59.705175)
plNext = AddPolyLine_Line_XY(plNext, -14.660948, 66.948793)
plNext = AddPolyLine_Line_XY(plNext, -14.509625, 67.147793)
plNext = AddPolyLine_Arc_XY(plNext, -14.379279, 67.357268, -14.290156, 67.587327)
plNext = AddPolyLine_Line_XY(plNext, -13.027258, 72.044993)
plNext = AddPolyLine_Arc_XY(plNext, -13.006847, 72.142157, -13, 72.241206)
plNext = AddPolyLine_Line_XY(plNext, -13, 72.281395)
plNext = AddPolyLine_Arc_XY(plNext, -13.017939, 72.319762, -13.058884, 72.330599)
plNext = AddPolyLine_Arc_XY(plNext, -14.280382, 72.099381, -15.497795, 71.847535)
plNext = AddPolyLine_Arc_XY(plNext, -15.72639, 71.753703, -15.908267, 71.586427)
plNext = AddPolyLine_Line_XY(plNext, -17.685755, 69.24891)
plNext = AddPolyLine_Arc_XY(plNext, -17.35518, 69.441696, -16.985108, 69.344264)
plNext = AddPolyLine_Line_XY(plNext, -14.835902, 67.70997)
plNext = AddPolyLine_Arc_XY(plNext, -14.643116, 67.379395, -14.740548, 67.009322)
plNext = AddPolyLine_Line_XY(plNext, -19.946076, 60.163705)
plNext = AddPolyLine_Arc_XY(plNext, -20.276652, 59.970919, -20.646724, 60.068351)
plNext = AddPolyLine_Line_XY(plNext, -22.79593, 61.702645)
plNext = AddPolyLine_Arc_XY(plNext, -22.988716, 62.03322, -22.891284, 62.403293)
plNext = AddPolyLine_Line_XY(plNext, -23.193931, 62.005292)
plNext = AddPolyLine_Line_XY(plNext, -23.968673, 60.986454)
plNext = AddPolyLine_Arc_XY(plNext, -24.262261, 60.271057, -24.160489, 59.504488)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_6


# Create new component fluid_rotor_pocket_7
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_7", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(13, -72.241206)
plNext = AddPolyLine_Line_XY(plStart, 13, -72.281395)
plNext = AddPolyLine_Arc_XY(plNext, 13.017939, -72.319762, 13.058884, -72.330599)
plNext = AddPolyLine_Arc_XY(plNext, 14.280382, -72.099381, 15.497795, -71.847535)
plNext = AddPolyLine_Arc_XY(plNext, 15.72639, -71.753703, 15.908267, -71.586427)
plNext = AddPolyLine_Line_XY(plNext, 17.685755, -69.24891)
plNext = AddPolyLine_Arc_XY(plNext, 17.35518, -69.441696, 16.985108, -69.344264)
plNext = AddPolyLine_Line_XY(plNext, 14.835902, -67.70997)
plNext = AddPolyLine_Arc_XY(plNext, 14.643116, -67.379395, 14.740548, -67.009322)
plNext = AddPolyLine_Line_XY(plNext, 19.946076, -60.163705)
plNext = AddPolyLine_Arc_XY(plNext, 20.276652, -59.970919, 20.646724, -60.068351)
plNext = AddPolyLine_Line_XY(plNext, 22.79593, -61.702645)
plNext = AddPolyLine_Arc_XY(plNext, 22.988716, -62.03322, 22.891284, -62.403293)
plNext = AddPolyLine_Line_XY(plNext, 23.193931, -62.005292)
plNext = AddPolyLine_Line_XY(plNext, 23.968673, -60.986454)
plNext = AddPolyLine_Arc_XY(plNext, 24.262261, -60.271057, 24.160489, -59.504488)
plNext = AddPolyLine_Line_XY(plNext, 23.648526, -58.268499)
plNext = AddPolyLine_Arc_XY(plNext, 22.6434, -57.498979, 21.475476, -57.987233)
plNext = AddPolyLine_Line_XY(plNext, 20.169123, -59.705175)
plNext = AddPolyLine_Line_XY(plNext, 14.660948, -66.948793)
plNext = AddPolyLine_Line_XY(plNext, 14.509625, -67.147793)
plNext = AddPolyLine_Arc_XY(plNext, 14.379279, -67.357268, 14.290156, -67.587327)
plNext = AddPolyLine_Line_XY(plNext, 13.027258, -72.044993)
ClosePolyLine_Arc_XY(plNext, 13.006847, -72.142157, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_7


# Create new component fluid_rotor_pocket_8
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_8", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(24.991981, 59.160073)
plNext = AddPolyLine_Line_XY(plStart, 24.480018, 57.924084)
plNext = AddPolyLine_Arc_XY(plNext, 24.646616, 56.66922, 25.817711, 56.188621)
plNext = AddPolyLine_Line_XY(plNext, 27.95621, 56.479658)
plNext = AddPolyLine_Line_XY(plNext, 36.97309, 57.706801)
plNext = AddPolyLine_Line_XY(plNext, 37.220806, 57.740514)
plNext = AddPolyLine_Arc_XY(plNext, 37.461096, 57.796466, 37.686791, 57.896123)
plNext = AddPolyLine_Line_XY(plNext, 41.73184, 60.155165)
plNext = AddPolyLine_Arc_XY(plNext, 41.814979, 60.209438, 41.889858, 60.274635)
plNext = AddPolyLine_Line_XY(plNext, 41.918276, 60.303052)
plNext = AddPolyLine_Arc_XY(plNext, 41.932721, 60.342867, 41.911432, 60.379482)
plNext = AddPolyLine_Arc_XY(plNext, 40.884206, 61.079716, 39.845284, 61.762475)
plNext = AddPolyLine_Arc_XY(plNext, 39.617293, 61.857767, 39.370404, 61.868091)
plNext = AddPolyLine_Line_XY(plNext, 36.460656, 61.472092)
plNext = AddPolyLine_Arc_XY(plNext, 36.830729, 61.37466, 37.023515, 61.044084)
plNext = AddPolyLine_Line_XY(plNext, 37.387612, 58.368746)
plNext = AddPolyLine_Arc_XY(plNext, 37.29018, 57.998674, 36.959605, 57.805888)
plNext = AddPolyLine_Line_XY(plNext, 28.438158, 56.64617)
plNext = AddPolyLine_Arc_XY(plNext, 28.068086, 56.743602, 27.8753, 57.074177)
plNext = AddPolyLine_Line_XY(plNext, 27.511202, 59.749515)
plNext = AddPolyLine_Arc_XY(plNext, 27.608634, 60.119588, 27.93921, 60.312374)
plNext = AddPolyLine_Line_XY(plNext, 27.443777, 60.244948)
plNext = AddPolyLine_Line_XY(plNext, 26.175524, 60.072346)
ClosePolyLine_Arc_XY(plNext, 25.462064, 59.774083, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_8


# Create new component fluid_rotor_pocket_9
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_9", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(56.479658, -27.95621)
plNext = AddPolyLine_Line_XY(plStart, 57.706801, -36.97309)
plNext = AddPolyLine_Line_XY(plNext, 57.740514, -37.220806)
plNext = AddPolyLine_Arc_XY(plNext, 57.796466, -37.461096, 57.896123, -37.686791)
plNext = AddPolyLine_Line_XY(plNext, 60.155165, -41.73184)
plNext = AddPolyLine_Arc_XY(plNext, 60.209438, -41.814979, 60.274635, -41.889858)
plNext = AddPolyLine_Line_XY(plNext, 60.303052, -41.918276)
plNext = AddPolyLine_Arc_XY(plNext, 60.342867, -41.932721, 60.379482, -41.911432)
plNext = AddPolyLine_Arc_XY(plNext, 61.079716, -40.884206, 61.762475, -39.845284)
plNext = AddPolyLine_Arc_XY(plNext, 61.857767, -39.617293, 61.868091, -39.370404)
plNext = AddPolyLine_Line_XY(plNext, 61.472092, -36.460656)
plNext = AddPolyLine_Arc_XY(plNext, 61.37466, -36.830729, 61.044084, -37.023515)
plNext = AddPolyLine_Line_XY(plNext, 58.368746, -37.387612)
plNext = AddPolyLine_Arc_XY(plNext, 57.998674, -37.29018, 57.805888, -36.959605)
plNext = AddPolyLine_Line_XY(plNext, 56.64617, -28.438158)
plNext = AddPolyLine_Arc_XY(plNext, 56.743602, -28.068086, 57.074177, -27.8753)
plNext = AddPolyLine_Line_XY(plNext, 59.749515, -27.511202)
plNext = AddPolyLine_Arc_XY(plNext, 60.119588, -27.608634, 60.312374, -27.93921)
plNext = AddPolyLine_Line_XY(plNext, 60.244948, -27.443777)
plNext = AddPolyLine_Line_XY(plNext, 60.072346, -26.175524)
plNext = AddPolyLine_Arc_XY(plNext, 59.774083, -25.462064, 59.160073, -24.991981)
plNext = AddPolyLine_Line_XY(plNext, 57.924084, -24.480018)
plNext = AddPolyLine_Arc_XY(plNext, 56.66922, -24.646616, 56.188621, -25.817711)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_9


# Create new component fluid_rotor_pocket_10
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_10", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(59.705175, 20.169123)
plNext = AddPolyLine_Line_XY(plStart, 66.948793, 14.660948)
plNext = AddPolyLine_Line_XY(plNext, 67.147793, 14.509625)
plNext = AddPolyLine_Arc_XY(plNext, 67.357268, 14.379279, 67.587327, 14.290156)
plNext = AddPolyLine_Line_XY(plNext, 72.044993, 13.027258)
plNext = AddPolyLine_Arc_XY(plNext, 72.142157, 13.006847, 72.241206, 13)
plNext = AddPolyLine_Line_XY(plNext, 72.281395, 13)
plNext = AddPolyLine_Arc_XY(plNext, 72.319762, 13.017939, 72.330599, 13.058884)
plNext = AddPolyLine_Arc_XY(plNext, 72.099381, 14.280382, 71.847535, 15.497795)
plNext = AddPolyLine_Arc_XY(plNext, 71.753703, 15.72639, 71.586427, 15.908267)
plNext = AddPolyLine_Line_XY(plNext, 69.24891, 17.685755)
plNext = AddPolyLine_Arc_XY(plNext, 69.441696, 17.35518, 69.344264, 16.985108)
plNext = AddPolyLine_Line_XY(plNext, 67.70997, 14.835902)
plNext = AddPolyLine_Arc_XY(plNext, 67.379395, 14.643116, 67.009322, 14.740548)
plNext = AddPolyLine_Line_XY(plNext, 60.163705, 19.946076)
plNext = AddPolyLine_Arc_XY(plNext, 59.970919, 20.276652, 60.068351, 20.646724)
plNext = AddPolyLine_Line_XY(plNext, 61.702645, 22.79593)
plNext = AddPolyLine_Arc_XY(plNext, 62.03322, 22.988716, 62.403293, 22.891284)
plNext = AddPolyLine_Line_XY(plNext, 62.005292, 23.193931)
plNext = AddPolyLine_Line_XY(plNext, 60.986454, 23.968673)
plNext = AddPolyLine_Arc_XY(plNext, 60.271057, 24.262261, 59.504488, 24.160489)
plNext = AddPolyLine_Line_XY(plNext, 58.268499, 23.648526)
plNext = AddPolyLine_Arc_XY(plNext, 57.498979, 22.6434, 57.987233, 21.475476)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_10


# Create new component fluid_rotor_pocket_11
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_11", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-61.472092, -36.460656)
plNext = AddPolyLine_Line_XY(plStart, -61.868091, -39.370404)
plNext = AddPolyLine_Arc_XY(plNext, -61.857767, -39.617293, -61.762475, -39.845284)
plNext = AddPolyLine_Arc_XY(plNext, -61.079716, -40.884206, -60.379482, -41.911432)
plNext = AddPolyLine_Arc_XY(plNext, -60.342867, -41.932721, -60.303052, -41.918276)
plNext = AddPolyLine_Line_XY(plNext, -60.274635, -41.889858)
plNext = AddPolyLine_Arc_XY(plNext, -60.209438, -41.814979, -60.155165, -41.73184)
plNext = AddPolyLine_Line_XY(plNext, -57.896123, -37.686791)
plNext = AddPolyLine_Arc_XY(plNext, -57.796466, -37.461096, -57.740514, -37.220806)
plNext = AddPolyLine_Line_XY(plNext, -57.706801, -36.97309)
plNext = AddPolyLine_Line_XY(plNext, -56.479658, -27.95621)
plNext = AddPolyLine_Line_XY(plNext, -56.188621, -25.817711)
plNext = AddPolyLine_Arc_XY(plNext, -56.66922, -24.646616, -57.924084, -24.480018)
plNext = AddPolyLine_Line_XY(plNext, -59.160073, -24.991981)
plNext = AddPolyLine_Arc_XY(plNext, -59.774083, -25.462064, -60.072346, -26.175524)
plNext = AddPolyLine_Line_XY(plNext, -60.244948, -27.443777)
plNext = AddPolyLine_Line_XY(plNext, -60.312374, -27.93921)
plNext = AddPolyLine_Arc_XY(plNext, -60.119588, -27.608634, -59.749515, -27.511202)
plNext = AddPolyLine_Line_XY(plNext, -57.074177, -27.8753)
plNext = AddPolyLine_Arc_XY(plNext, -56.743602, -28.068086, -56.64617, -28.438158)
plNext = AddPolyLine_Line_XY(plNext, -57.805888, -36.959605)
plNext = AddPolyLine_Arc_XY(plNext, -57.998674, -37.29018, -58.368746, -37.387612)
plNext = AddPolyLine_Line_XY(plNext, -61.044084, -37.023515)
ClosePolyLine_Arc_XY(plNext, -61.37466, -36.830729, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_11


# Create new component fluid_rotor_pocket_12
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_12", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-41.889858, 60.274635)
plNext = AddPolyLine_Arc_XY(plStart, -41.814979, 60.209438, -41.73184, 60.155165)
plNext = AddPolyLine_Line_XY(plNext, -37.686791, 57.896123)
plNext = AddPolyLine_Arc_XY(plNext, -37.461096, 57.796466, -37.220806, 57.740514)
plNext = AddPolyLine_Line_XY(plNext, -36.97309, 57.706801)
plNext = AddPolyLine_Line_XY(plNext, -27.95621, 56.479658)
plNext = AddPolyLine_Line_XY(plNext, -25.817711, 56.188621)
plNext = AddPolyLine_Arc_XY(plNext, -24.646616, 56.66922, -24.480018, 57.924084)
plNext = AddPolyLine_Line_XY(plNext, -24.991981, 59.160073)
plNext = AddPolyLine_Arc_XY(plNext, -25.462064, 59.774083, -26.175524, 60.072346)
plNext = AddPolyLine_Line_XY(plNext, -27.443777, 60.244948)
plNext = AddPolyLine_Line_XY(plNext, -27.93921, 60.312374)
plNext = AddPolyLine_Arc_XY(plNext, -27.608634, 60.119588, -27.511202, 59.749515)
plNext = AddPolyLine_Line_XY(plNext, -27.8753, 57.074177)
plNext = AddPolyLine_Arc_XY(plNext, -28.068086, 56.743602, -28.438158, 56.64617)
plNext = AddPolyLine_Line_XY(plNext, -36.959605, 57.805888)
plNext = AddPolyLine_Arc_XY(plNext, -37.29018, 57.998674, -37.387612, 58.368746)
plNext = AddPolyLine_Line_XY(plNext, -37.023515, 61.044084)
plNext = AddPolyLine_Arc_XY(plNext, -36.830729, 61.37466, -36.460656, 61.472092)
plNext = AddPolyLine_Line_XY(plNext, -39.370404, 61.868091)
plNext = AddPolyLine_Arc_XY(plNext, -39.617293, 61.857767, -39.845284, 61.762475)
plNext = AddPolyLine_Arc_XY(plNext, -40.884206, 61.079716, -41.911432, 60.379482)
plNext = AddPolyLine_Arc_XY(plNext, -41.932721, 60.342867, -41.918276, 60.303052)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_12


# Create new component fluid_rotor_pocket_13
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_13", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-23.648526, -58.268499)
plNext = AddPolyLine_Line_XY(plStart, -24.160489, -59.504488)
plNext = AddPolyLine_Arc_XY(plNext, -24.262261, -60.271057, -23.968673, -60.986454)
plNext = AddPolyLine_Line_XY(plNext, -23.193931, -62.005292)
plNext = AddPolyLine_Line_XY(plNext, -22.891284, -62.403293)
plNext = AddPolyLine_Arc_XY(plNext, -22.988716, -62.03322, -22.79593, -61.702645)
plNext = AddPolyLine_Line_XY(plNext, -20.646724, -60.068351)
plNext = AddPolyLine_Arc_XY(plNext, -20.276652, -59.970919, -19.946076, -60.163705)
plNext = AddPolyLine_Line_XY(plNext, -14.740548, -67.009322)
plNext = AddPolyLine_Arc_XY(plNext, -14.643116, -67.379395, -14.835902, -67.70997)
plNext = AddPolyLine_Line_XY(plNext, -16.985108, -69.344264)
plNext = AddPolyLine_Arc_XY(plNext, -17.35518, -69.441696, -17.685755, -69.24891)
plNext = AddPolyLine_Line_XY(plNext, -15.908267, -71.586427)
plNext = AddPolyLine_Arc_XY(plNext, -15.72639, -71.753703, -15.497795, -71.847535)
plNext = AddPolyLine_Arc_XY(plNext, -14.280382, -72.099381, -13.058884, -72.330599)
plNext = AddPolyLine_Arc_XY(plNext, -13.017939, -72.319762, -13, -72.281395)
plNext = AddPolyLine_Line_XY(plNext, -13, -72.241206)
plNext = AddPolyLine_Arc_XY(plNext, -13.006847, -72.142157, -13.027258, -72.044993)
plNext = AddPolyLine_Line_XY(plNext, -14.290156, -67.587327)
plNext = AddPolyLine_Arc_XY(plNext, -14.379279, -67.357268, -14.509625, -67.147793)
plNext = AddPolyLine_Line_XY(plNext, -14.660948, -66.948793)
plNext = AddPolyLine_Line_XY(plNext, -20.169123, -59.705175)
plNext = AddPolyLine_Line_XY(plNext, -21.475476, -57.987233)
ClosePolyLine_Arc_XY(plNext, -22.6434, -57.498979, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_13


# Create new component fluid_rotor_pocket_14
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_14", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(13, 72.281395)
plNext = AddPolyLine_Line_XY(plStart, 13, 72.241206)
plNext = AddPolyLine_Arc_XY(plNext, 13.006847, 72.142157, 13.027258, 72.044993)
plNext = AddPolyLine_Line_XY(plNext, 14.290156, 67.587327)
plNext = AddPolyLine_Arc_XY(plNext, 14.379279, 67.357268, 14.509625, 67.147793)
plNext = AddPolyLine_Line_XY(plNext, 14.660948, 66.948793)
plNext = AddPolyLine_Line_XY(plNext, 20.169123, 59.705175)
plNext = AddPolyLine_Line_XY(plNext, 21.475476, 57.987233)
plNext = AddPolyLine_Arc_XY(plNext, 22.6434, 57.498979, 23.648526, 58.268499)
plNext = AddPolyLine_Line_XY(plNext, 24.160489, 59.504488)
plNext = AddPolyLine_Arc_XY(plNext, 24.262261, 60.271057, 23.968673, 60.986454)
plNext = AddPolyLine_Line_XY(plNext, 23.193931, 62.005292)
plNext = AddPolyLine_Line_XY(plNext, 22.891284, 62.403293)
plNext = AddPolyLine_Arc_XY(plNext, 22.988716, 62.03322, 22.79593, 61.702645)
plNext = AddPolyLine_Line_XY(plNext, 20.646724, 60.068351)
plNext = AddPolyLine_Arc_XY(plNext, 20.276652, 59.970919, 19.946076, 60.163705)
plNext = AddPolyLine_Line_XY(plNext, 14.740548, 67.009322)
plNext = AddPolyLine_Arc_XY(plNext, 14.643116, 67.379395, 14.835902, 67.70997)
plNext = AddPolyLine_Line_XY(plNext, 16.985108, 69.344264)
plNext = AddPolyLine_Arc_XY(plNext, 17.35518, 69.441696, 17.685755, 69.24891)
plNext = AddPolyLine_Line_XY(plNext, 15.908267, 71.586427)
plNext = AddPolyLine_Arc_XY(plNext, 15.72639, 71.753703, 15.497795, 71.847535)
plNext = AddPolyLine_Arc_XY(plNext, 14.280382, 72.099381, 13.058884, 72.330599)
ClosePolyLine_Arc_XY(plNext, 13.017939, 72.319762, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_14


# Create new component fluid_rotor_pocket_15
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_15", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(24.991981, -59.160073)
plNext = AddPolyLine_Arc_XY(plStart, 25.462064, -59.774083, 26.175524, -60.072346)
plNext = AddPolyLine_Line_XY(plNext, 27.443777, -60.244948)
plNext = AddPolyLine_Line_XY(plNext, 27.93921, -60.312374)
plNext = AddPolyLine_Arc_XY(plNext, 27.608634, -60.119588, 27.511202, -59.749515)
plNext = AddPolyLine_Line_XY(plNext, 27.8753, -57.074177)
plNext = AddPolyLine_Arc_XY(plNext, 28.068086, -56.743602, 28.438158, -56.64617)
plNext = AddPolyLine_Line_XY(plNext, 36.959605, -57.805888)
plNext = AddPolyLine_Arc_XY(plNext, 37.29018, -57.998674, 37.387612, -58.368746)
plNext = AddPolyLine_Line_XY(plNext, 37.023515, -61.044084)
plNext = AddPolyLine_Arc_XY(plNext, 36.830729, -61.37466, 36.460656, -61.472092)
plNext = AddPolyLine_Line_XY(plNext, 39.370404, -61.868091)
plNext = AddPolyLine_Arc_XY(plNext, 39.617293, -61.857767, 39.845284, -61.762475)
plNext = AddPolyLine_Arc_XY(plNext, 40.884206, -61.079716, 41.911432, -60.379482)
plNext = AddPolyLine_Arc_XY(plNext, 41.932721, -60.342867, 41.918276, -60.303052)
plNext = AddPolyLine_Line_XY(plNext, 41.889858, -60.274635)
plNext = AddPolyLine_Arc_XY(plNext, 41.814979, -60.209438, 41.73184, -60.155165)
plNext = AddPolyLine_Line_XY(plNext, 37.686791, -57.896123)
plNext = AddPolyLine_Arc_XY(plNext, 37.461096, -57.796466, 37.220806, -57.740514)
plNext = AddPolyLine_Line_XY(plNext, 36.97309, -57.706801)
plNext = AddPolyLine_Line_XY(plNext, 27.95621, -56.479658)
plNext = AddPolyLine_Line_XY(plNext, 25.817711, -56.188621)
plNext = AddPolyLine_Arc_XY(plNext, 24.646616, -56.66922, 24.480018, -57.924084)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_15


# Create new component fluid_rotor_pocket_16
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_16", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(56.479658, 27.95621)
plNext = AddPolyLine_Line_XY(plStart, 56.188621, 25.817711)
plNext = AddPolyLine_Arc_XY(plNext, 56.66922, 24.646616, 57.924084, 24.480018)
plNext = AddPolyLine_Line_XY(plNext, 59.160073, 24.991981)
plNext = AddPolyLine_Arc_XY(plNext, 59.774083, 25.462064, 60.072346, 26.175524)
plNext = AddPolyLine_Line_XY(plNext, 60.244948, 27.443777)
plNext = AddPolyLine_Line_XY(plNext, 60.312374, 27.93921)
plNext = AddPolyLine_Arc_XY(plNext, 60.119588, 27.608634, 59.749515, 27.511202)
plNext = AddPolyLine_Line_XY(plNext, 57.074177, 27.8753)
plNext = AddPolyLine_Arc_XY(plNext, 56.743602, 28.068086, 56.64617, 28.438158)
plNext = AddPolyLine_Line_XY(plNext, 57.805888, 36.959605)
plNext = AddPolyLine_Arc_XY(plNext, 57.998674, 37.29018, 58.368746, 37.387612)
plNext = AddPolyLine_Line_XY(plNext, 61.044084, 37.023515)
plNext = AddPolyLine_Arc_XY(plNext, 61.37466, 36.830729, 61.472092, 36.460656)
plNext = AddPolyLine_Line_XY(plNext, 61.868091, 39.370404)
plNext = AddPolyLine_Arc_XY(plNext, 61.857767, 39.617293, 61.762475, 39.845284)
plNext = AddPolyLine_Arc_XY(plNext, 61.079716, 40.884206, 60.379482, 41.911432)
plNext = AddPolyLine_Arc_XY(plNext, 60.342867, 41.932721, 60.303052, 41.918276)
plNext = AddPolyLine_Line_XY(plNext, 60.274635, 41.889858)
plNext = AddPolyLine_Arc_XY(plNext, 60.209438, 41.814979, 60.155165, 41.73184)
plNext = AddPolyLine_Line_XY(plNext, 57.896123, 37.686791)
plNext = AddPolyLine_Arc_XY(plNext, 57.796466, 37.461096, 57.740514, 37.220806)
plNext = AddPolyLine_Line_XY(plNext, 57.706801, 36.97309)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_16


# Create new component fluid_rotor_pocket_17
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_17", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(59.705175, -20.169123)
plNext = AddPolyLine_Line_XY(plStart, 57.987233, -21.475476)
plNext = AddPolyLine_Arc_XY(plNext, 57.498979, -22.6434, 58.268499, -23.648526)
plNext = AddPolyLine_Line_XY(plNext, 59.504488, -24.160489)
plNext = AddPolyLine_Arc_XY(plNext, 60.271057, -24.262261, 60.986454, -23.968673)
plNext = AddPolyLine_Line_XY(plNext, 62.005292, -23.193931)
plNext = AddPolyLine_Line_XY(plNext, 62.403293, -22.891284)
plNext = AddPolyLine_Arc_XY(plNext, 62.03322, -22.988716, 61.702645, -22.79593)
plNext = AddPolyLine_Line_XY(plNext, 60.068351, -20.646724)
plNext = AddPolyLine_Arc_XY(plNext, 59.970919, -20.276652, 60.163705, -19.946076)
plNext = AddPolyLine_Line_XY(plNext, 67.009322, -14.740548)
plNext = AddPolyLine_Arc_XY(plNext, 67.379395, -14.643116, 67.70997, -14.835902)
plNext = AddPolyLine_Line_XY(plNext, 69.344264, -16.985108)
plNext = AddPolyLine_Arc_XY(plNext, 69.441696, -17.35518, 69.24891, -17.685755)
plNext = AddPolyLine_Line_XY(plNext, 71.586427, -15.908267)
plNext = AddPolyLine_Arc_XY(plNext, 71.753703, -15.72639, 71.847535, -15.497795)
plNext = AddPolyLine_Arc_XY(plNext, 72.099381, -14.280382, 72.330599, -13.058884)
plNext = AddPolyLine_Arc_XY(plNext, 72.319762, -13.017939, 72.281395, -13)
plNext = AddPolyLine_Line_XY(plNext, 72.241206, -13)
plNext = AddPolyLine_Arc_XY(plNext, 72.142157, -13.006847, 72.044993, -13.027258)
plNext = AddPolyLine_Line_XY(plNext, 67.587327, -14.290156)
plNext = AddPolyLine_Arc_XY(plNext, 67.357268, -14.379279, 67.147793, -14.509625)
plNext = AddPolyLine_Line_XY(plNext, 66.948793, -14.660948)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_17


# Create new component magnet_p4_l1_m0_s0
newComp = CreateNamedComponentWithColour_Radial("magnet_p4_l1_m0_s0", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(16.985108, 69.344264)
plNext = AddPolyLine_Line_XY(plStart, 14.835902, 67.70997)
plNext = AddPolyLine_Arc_XY(plNext, 14.643116, 67.379395, 14.740548, 67.009322)
plNext = AddPolyLine_Line_XY(plNext, 19.946076, 60.163705)
plNext = AddPolyLine_Arc_XY(plNext, 20.276652, 59.970919, 20.646724, 60.068351)
plNext = AddPolyLine_Line_XY(plNext, 22.79593, 61.702645)
plNext = AddPolyLine_Arc_XY(plNext, 22.988716, 62.03322, 22.891284, 62.403293)
plNext = AddPolyLine_Line_XY(plNext, 17.685755, 69.24891)
ClosePolyLine_Arc_XY(plNext, 17.35518, 69.441696, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p4_l1_m0_s0


# Create new component magnet_p3_l1_m0_s0
newComp = CreateNamedComponentWithColour_Radial("magnet_p3_l1_m0_s0", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-37.023515, 61.044084)
plNext = AddPolyLine_Line_XY(plStart, -37.387612, 58.368746)
plNext = AddPolyLine_Arc_XY(plNext, -37.29018, 57.998674, -36.959605, 57.805888)
plNext = AddPolyLine_Line_XY(plNext, -28.438158, 56.64617)
plNext = AddPolyLine_Arc_XY(plNext, -28.068086, 56.743602, -27.8753, 57.074177)
plNext = AddPolyLine_Line_XY(plNext, -27.511202, 59.749515)
plNext = AddPolyLine_Arc_XY(plNext, -27.608634, 60.119588, -27.93921, 60.312374)
plNext = AddPolyLine_Line_XY(plNext, -36.460656, 61.472092)
ClosePolyLine_Arc_XY(plNext, -36.830729, 61.37466, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p3_l1_m0_s0


# Create new component magnet_p6_l1_m0_s0
newComp = CreateNamedComponentWithColour_Radial("magnet_p6_l1_m0_s0", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-69.344264, 16.985108)
plNext = AddPolyLine_Line_XY(plStart, -67.70997, 14.835902)
plNext = AddPolyLine_Arc_XY(plNext, -67.379395, 14.643116, -67.009322, 14.740548)
plNext = AddPolyLine_Line_XY(plNext, -60.163705, 19.946076)
plNext = AddPolyLine_Arc_XY(plNext, -59.970919, 20.276652, -60.068351, 20.646724)
plNext = AddPolyLine_Line_XY(plNext, -61.702645, 22.79593)
plNext = AddPolyLine_Arc_XY(plNext, -62.03322, 22.988716, -62.403293, 22.891284)
plNext = AddPolyLine_Line_XY(plNext, -69.24891, 17.685755)
ClosePolyLine_Arc_XY(plNext, -69.441696, 17.35518, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p6_l1_m0_s0


# Create new component magnet_p5_l1_m0_s0
newComp = CreateNamedComponentWithColour_Radial("magnet_p5_l1_m0_s0", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-61.044084, -37.023515)
plNext = AddPolyLine_Line_XY(plStart, -58.368746, -37.387612)
plNext = AddPolyLine_Arc_XY(plNext, -57.998674, -37.29018, -57.805888, -36.959605)
plNext = AddPolyLine_Line_XY(plNext, -56.64617, -28.438158)
plNext = AddPolyLine_Arc_XY(plNext, -56.743602, -28.068086, -57.074177, -27.8753)
plNext = AddPolyLine_Line_XY(plNext, -59.749515, -27.511202)
plNext = AddPolyLine_Arc_XY(plNext, -60.119588, -27.608634, -60.312374, -27.93921)
plNext = AddPolyLine_Line_XY(plNext, -61.472092, -36.460656)
ClosePolyLine_Arc_XY(plNext, -61.37466, -36.830729, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p5_l1_m0_s0


# Create new component magnet_p8_l1_m0_s0
newComp = CreateNamedComponentWithColour_Radial("magnet_p8_l1_m0_s0", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-16.985108, -69.344264)
plNext = AddPolyLine_Line_XY(plStart, -14.835902, -67.70997)
plNext = AddPolyLine_Arc_XY(plNext, -14.643116, -67.379395, -14.740548, -67.009322)
plNext = AddPolyLine_Line_XY(plNext, -19.946076, -60.163705)
plNext = AddPolyLine_Arc_XY(plNext, -20.276652, -59.970919, -20.646724, -60.068351)
plNext = AddPolyLine_Line_XY(plNext, -22.79593, -61.702645)
plNext = AddPolyLine_Arc_XY(plNext, -22.988716, -62.03322, -22.891284, -62.403293)
plNext = AddPolyLine_Line_XY(plNext, -17.685755, -69.24891)
ClosePolyLine_Arc_XY(plNext, -17.35518, -69.441696, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p8_l1_m0_s0


# Create new component magnet_p7_l1_m0_s0
newComp = CreateNamedComponentWithColour_Radial("magnet_p7_l1_m0_s0", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(37.023515, -61.044084)
plNext = AddPolyLine_Line_XY(plStart, 37.387612, -58.368746)
plNext = AddPolyLine_Arc_XY(plNext, 37.29018, -57.998674, 36.959605, -57.805888)
plNext = AddPolyLine_Line_XY(plNext, 28.438158, -56.64617)
plNext = AddPolyLine_Arc_XY(plNext, 28.068086, -56.743602, 27.8753, -57.074177)
plNext = AddPolyLine_Line_XY(plNext, 27.511202, -59.749515)
plNext = AddPolyLine_Arc_XY(plNext, 27.608634, -60.119588, 27.93921, -60.312374)
plNext = AddPolyLine_Line_XY(plNext, 36.460656, -61.472092)
ClosePolyLine_Arc_XY(plNext, 36.830729, -61.37466, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p7_l1_m0_s0


# Create new component magnet_p2_l1_m0_s0
newComp = CreateNamedComponentWithColour_Radial("magnet_p2_l1_m0_s0", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(69.344264, -16.985108)
plNext = AddPolyLine_Line_XY(plStart, 67.70997, -14.835902)
plNext = AddPolyLine_Arc_XY(plNext, 67.379395, -14.643116, 67.009322, -14.740548)
plNext = AddPolyLine_Line_XY(plNext, 60.163705, -19.946076)
plNext = AddPolyLine_Arc_XY(plNext, 59.970919, -20.276652, 60.068351, -20.646724)
plNext = AddPolyLine_Line_XY(plNext, 61.702645, -22.79593)
plNext = AddPolyLine_Arc_XY(plNext, 62.03322, -22.988716, 62.403293, -22.891284)
plNext = AddPolyLine_Line_XY(plNext, 69.24891, -17.685755)
ClosePolyLine_Arc_XY(plNext, 69.441696, -17.35518, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p2_l1_m0_s0


# Create new component magnet_p4_l1_m0_s_1
newComp = CreateNamedComponentWithColour_Radial("magnet_p4_l1_m0_s_1", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(37.387612, 58.368746)
plNext = AddPolyLine_Line_XY(plStart, 37.023515, 61.044084)
plNext = AddPolyLine_Arc_XY(plNext, 36.830729, 61.37466, 36.460656, 61.472092)
plNext = AddPolyLine_Line_XY(plNext, 27.93921, 60.312374)
plNext = AddPolyLine_Arc_XY(plNext, 27.608634, 60.119588, 27.511202, 59.749515)
plNext = AddPolyLine_Line_XY(plNext, 27.8753, 57.074177)
plNext = AddPolyLine_Arc_XY(plNext, 28.068086, 56.743602, 28.438158, 56.64617)
plNext = AddPolyLine_Line_XY(plNext, 36.959605, 57.805888)
ClosePolyLine_Arc_XY(plNext, 37.29018, 57.998674, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p4_l1_m0_s_1


# Create new component magnet_p3_l1_m0_s_1
newComp = CreateNamedComponentWithColour_Radial("magnet_p3_l1_m0_s_1", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-14.835902, 67.70997)
plNext = AddPolyLine_Line_XY(plStart, -16.985108, 69.344264)
plNext = AddPolyLine_Arc_XY(plNext, -17.35518, 69.441696, -17.685756, 69.24891)
plNext = AddPolyLine_Line_XY(plNext, -22.891284, 62.403293)
plNext = AddPolyLine_Arc_XY(plNext, -22.988716, 62.03322, -22.79593, 61.702645)
plNext = AddPolyLine_Line_XY(plNext, -20.646724, 60.068351)
plNext = AddPolyLine_Arc_XY(plNext, -20.276652, 59.970919, -19.946076, 60.163705)
plNext = AddPolyLine_Line_XY(plNext, -14.740548, 67.009322)
ClosePolyLine_Arc_XY(plNext, -14.643116, 67.379395, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p3_l1_m0_s_1


# Create new component magnet_p6_l1_m0_s_1
newComp = CreateNamedComponentWithColour_Radial("magnet_p6_l1_m0_s_1", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-58.368746, 37.387612)
plNext = AddPolyLine_Line_XY(plStart, -61.044084, 37.023515)
plNext = AddPolyLine_Arc_XY(plNext, -61.37466, 36.830729, -61.472092, 36.460656)
plNext = AddPolyLine_Line_XY(plNext, -60.312374, 27.93921)
plNext = AddPolyLine_Arc_XY(plNext, -60.119588, 27.608634, -59.749515, 27.511202)
plNext = AddPolyLine_Line_XY(plNext, -57.074177, 27.8753)
plNext = AddPolyLine_Arc_XY(plNext, -56.743602, 28.068086, -56.64617, 28.438158)
plNext = AddPolyLine_Line_XY(plNext, -57.805888, 36.959605)
ClosePolyLine_Arc_XY(plNext, -57.998674, 37.29018, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p6_l1_m0_s_1


# Create new component magnet_p5_l1_m0_s_1
newComp = CreateNamedComponentWithColour_Radial("magnet_p5_l1_m0_s_1", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-67.70997, -14.835902)
plNext = AddPolyLine_Line_XY(plStart, -69.344264, -16.985108)
plNext = AddPolyLine_Arc_XY(plNext, -69.441696, -17.35518, -69.24891, -17.685756)
plNext = AddPolyLine_Line_XY(plNext, -62.403293, -22.891284)
plNext = AddPolyLine_Arc_XY(plNext, -62.03322, -22.988716, -61.702645, -22.79593)
plNext = AddPolyLine_Line_XY(plNext, -60.068351, -20.646724)
plNext = AddPolyLine_Arc_XY(plNext, -59.970919, -20.276652, -60.163705, -19.946076)
plNext = AddPolyLine_Line_XY(plNext, -67.009322, -14.740548)
ClosePolyLine_Arc_XY(plNext, -67.379395, -14.643116, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p5_l1_m0_s_1


# Create new component magnet_p8_l1_m0_s_1
newComp = CreateNamedComponentWithColour_Radial("magnet_p8_l1_m0_s_1", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-37.387612, -58.368746)
plNext = AddPolyLine_Line_XY(plStart, -37.023515, -61.044084)
plNext = AddPolyLine_Arc_XY(plNext, -36.830729, -61.37466, -36.460656, -61.472092)
plNext = AddPolyLine_Line_XY(plNext, -27.93921, -60.312374)
plNext = AddPolyLine_Arc_XY(plNext, -27.608634, -60.119588, -27.511202, -59.749515)
plNext = AddPolyLine_Line_XY(plNext, -27.8753, -57.074177)
plNext = AddPolyLine_Arc_XY(plNext, -28.068086, -56.743602, -28.438158, -56.64617)
plNext = AddPolyLine_Line_XY(plNext, -36.959605, -57.805888)
ClosePolyLine_Arc_XY(plNext, -37.29018, -57.998674, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p8_l1_m0_s_1


# Create new component magnet_p7_l1_m0_s_1
newComp = CreateNamedComponentWithColour_Radial("magnet_p7_l1_m0_s_1", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(14.835902, -67.70997)
plNext = AddPolyLine_Line_XY(plStart, 16.985108, -69.344264)
plNext = AddPolyLine_Arc_XY(plNext, 17.35518, -69.441696, 17.685756, -69.24891)
plNext = AddPolyLine_Line_XY(plNext, 22.891284, -62.403293)
plNext = AddPolyLine_Arc_XY(plNext, 22.988716, -62.03322, 22.79593, -61.702645)
plNext = AddPolyLine_Line_XY(plNext, 20.646724, -60.068351)
plNext = AddPolyLine_Arc_XY(plNext, 20.276652, -59.970919, 19.946076, -60.163705)
plNext = AddPolyLine_Line_XY(plNext, 14.740548, -67.009322)
ClosePolyLine_Arc_XY(plNext, 14.643116, -67.379395, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p7_l1_m0_s_1


# Create new component magnet_p2_l1_m0_s_1
newComp = CreateNamedComponentWithColour_Radial("magnet_p2_l1_m0_s_1", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(58.368746, -37.387612)
plNext = AddPolyLine_Line_XY(plStart, 61.044084, -37.023515)
plNext = AddPolyLine_Arc_XY(plNext, 61.37466, -36.830729, 61.472092, -36.460656)
plNext = AddPolyLine_Line_XY(plNext, 60.312374, -27.93921)
plNext = AddPolyLine_Arc_XY(plNext, 60.119588, -27.608634, 59.749515, -27.511202)
plNext = AddPolyLine_Line_XY(plNext, 57.074177, -27.8753)
plNext = AddPolyLine_Arc_XY(plNext, 56.743602, -28.068086, 56.64617, -28.438158)
plNext = AddPolyLine_Line_XY(plNext, 57.805888, -36.959605)
ClosePolyLine_Arc_XY(plNext, 57.998674, -37.29018, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p2_l1_m0_s_1


# Create new component fluid_rotor_pocket_18
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_18", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-55.53541, 41.070243)
plNext = AddPolyLine_Arc_XY(plStart, -55.53541, 41.452926, -55.264812, 41.723524)
plNext = AddPolyLine_Line_XY(plNext, -51.75407, 43.177721)
plNext = AddPolyLine_Arc_XY(plNext, -51.371386, 43.177721, -51.100788, 42.907123)
plNext = AddPolyLine_Line_XY(plNext, -44.212486, 26.277292)
plNext = AddPolyLine_Arc_XY(plNext, -44.212486, 25.894608, -44.483084, 25.62401)
plNext = AddPolyLine_Line_XY(plNext, -47.993827, 24.169813)
plNext = AddPolyLine_Arc_XY(plNext, -48.37651, 24.169813, -48.647108, 24.440411)
plNext = AddPolyLine_Line_XY(plNext, -48.455766, 23.978471)
plNext = AddPolyLine_Line_XY(plNext, -47.551612, 21.795649)
plNext = AddPolyLine_Arc_XY(plNext, -47.226453, 21.309014, -46.739818, 20.983855)
plNext = AddPolyLine_Line_XY(plNext, -44.112763, 19.895693)
plNext = AddPolyLine_Arc_XY(plNext, -42.548721, 20.2068, -42.237614, 21.770842)
plNext = AddPolyLine_Line_XY(plNext, -43.928757, 25.85362)
plNext = AddPolyLine_Line_XY(plNext, -51.0084, 42.945392)
plNext = AddPolyLine_Line_XY(plNext, -51.151482, 43.290822)
plNext = AddPolyLine_Arc_XY(plNext, -51.1947, 43.408939, -51.227871, 43.530261)
plNext = AddPolyLine_Line_XY(plNext, -51.62381, 45.260592)
plNext = AddPolyLine_Arc_XY(plNext, -51.773383, 45.651946, -52.025358, 45.986666)
plNext = AddPolyLine_Line_XY(plNext, -53.2755, 47.236808)
plNext = AddPolyLine_Arc_XY(plNext, -53.832268, 47.456012, -54.372208, 47.198125)
plNext = AddPolyLine_Arc_XY(plNext, -55.403224, 45.983505, -56.407113, 44.74637)
plNext = AddPolyLine_Arc_XY(plNext, -56.649229, 44.181281, -56.571444, 43.57145)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_18


# Create new component fluid_rotor_pocket_19
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_19", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-45.986666, -52.025358)
plNext = AddPolyLine_Line_XY(plStart, -47.236808, -53.2755)
plNext = AddPolyLine_Arc_XY(plNext, -47.456012, -53.832268, -47.198125, -54.372208)
plNext = AddPolyLine_Arc_XY(plNext, -45.983505, -55.403224, -44.74637, -56.407113)
plNext = AddPolyLine_Arc_XY(plNext, -44.181281, -56.649229, -43.57145, -56.571444)
plNext = AddPolyLine_Line_XY(plNext, -41.070243, -55.53541)
plNext = AddPolyLine_Arc_XY(plNext, -41.452926, -55.53541, -41.723524, -55.264812)
plNext = AddPolyLine_Line_XY(plNext, -43.177721, -51.75407)
plNext = AddPolyLine_Arc_XY(plNext, -43.177721, -51.371386, -42.907123, -51.100788)
plNext = AddPolyLine_Line_XY(plNext, -26.277292, -44.212486)
plNext = AddPolyLine_Arc_XY(plNext, -25.894608, -44.212486, -25.62401, -44.483084)
plNext = AddPolyLine_Line_XY(plNext, -24.169813, -47.993827)
plNext = AddPolyLine_Arc_XY(plNext, -24.169813, -48.37651, -24.440411, -48.647108)
plNext = AddPolyLine_Line_XY(plNext, -23.978471, -48.455766)
plNext = AddPolyLine_Line_XY(plNext, -21.795649, -47.551612)
plNext = AddPolyLine_Arc_XY(plNext, -21.309014, -47.226453, -20.983855, -46.739818)
plNext = AddPolyLine_Line_XY(plNext, -19.895693, -44.112763)
plNext = AddPolyLine_Arc_XY(plNext, -20.2068, -42.548721, -21.770842, -42.237614)
plNext = AddPolyLine_Line_XY(plNext, -25.85362, -43.928757)
plNext = AddPolyLine_Line_XY(plNext, -42.945392, -51.0084)
plNext = AddPolyLine_Line_XY(plNext, -43.290822, -51.151482)
plNext = AddPolyLine_Arc_XY(plNext, -43.408939, -51.1947, -43.530261, -51.227871)
plNext = AddPolyLine_Line_XY(plNext, -45.260592, -51.62381)
ClosePolyLine_Arc_XY(plNext, -45.651946, -51.773383, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_19


# Create new component fluid_rotor_pocket_20
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_20", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-17.124054, 45.260813)
plNext = AddPolyLine_Arc_XY(plStart, -15.798124, 44.374855, -14.472194, 45.260813)
plNext = AddPolyLine_Line_XY(plNext, -12.781051, 49.343592)
plNext = AddPolyLine_Line_XY(plNext, -5.701408, 66.435363)
plNext = AddPolyLine_Line_XY(plNext, -5.558326, 66.780794)
plNext = AddPolyLine_Arc_XY(plNext, -5.505365, 66.894874, -5.443032, 67.004117)
plNext = AddPolyLine_Line_XY(plNext, -4.499474, 68.507618)
plNext = AddPolyLine_Arc_XY(plNext, -4.32851, 68.89011, -4.27, 69.304967)
plNext = AddPolyLine_Line_XY(plNext, -4.27, 71.072935)
plNext = AddPolyLine_Arc_XY(plNext, -4.508694, 71.62163, -5.072842, 71.821071)
plNext = AddPolyLine_Arc_XY(plNext, -6.660747, 71.691244, -8.24539, 71.526314)
plNext = AddPolyLine_Arc_XY(plNext, -8.81617, 71.297938, -9.192384, 70.811719)
plNext = AddPolyLine_Line_XY(plNext, -10.228418, 68.310512)
plNext = AddPolyLine_Arc_XY(plNext, -9.95782, 68.58111, -9.575136, 68.58111)
plNext = AddPolyLine_Line_XY(plNext, -6.064394, 67.126913)
plNext = AddPolyLine_Arc_XY(plNext, -5.793796, 66.856315, -5.793796, 66.473632)
plNext = AddPolyLine_Line_XY(plNext, -12.682098, 49.8438)
plNext = AddPolyLine_Arc_XY(plNext, -12.952696, 49.573202, -13.335379, 49.573202)
plNext = AddPolyLine_Line_XY(plNext, -16.846121, 51.027399)
plNext = AddPolyLine_Arc_XY(plNext, -17.116719, 51.297997, -17.11672, 51.68068)
plNext = AddPolyLine_Line_XY(plNext, -17.308061, 51.218741)
plNext = AddPolyLine_Line_XY(plNext, -18.212216, 49.035918)
plNext = AddPolyLine_Arc_XY(plNext, -18.326397, 48.461893, -18.212216, 47.887868)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_20


# Create new component fluid_rotor_pocket_21
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_21", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(4.27, -69.304967)
plNext = AddPolyLine_Line_XY(plStart, 4.27, -71.072935)
plNext = AddPolyLine_Arc_XY(plNext, 4.508694, -71.62163, 5.072842, -71.821071)
plNext = AddPolyLine_Arc_XY(plNext, 6.660747, -71.691244, 8.24539, -71.526314)
plNext = AddPolyLine_Arc_XY(plNext, 8.81617, -71.297938, 9.192384, -70.811719)
plNext = AddPolyLine_Line_XY(plNext, 10.228418, -68.310512)
plNext = AddPolyLine_Arc_XY(plNext, 9.95782, -68.58111, 9.575136, -68.58111)
plNext = AddPolyLine_Line_XY(plNext, 6.064394, -67.126913)
plNext = AddPolyLine_Arc_XY(plNext, 5.793796, -66.856315, 5.793796, -66.473632)
plNext = AddPolyLine_Line_XY(plNext, 12.682098, -49.8438)
plNext = AddPolyLine_Arc_XY(plNext, 12.952696, -49.573202, 13.335379, -49.573202)
plNext = AddPolyLine_Line_XY(plNext, 16.846121, -51.027399)
plNext = AddPolyLine_Arc_XY(plNext, 17.116719, -51.297997, 17.11672, -51.68068)
plNext = AddPolyLine_Line_XY(plNext, 17.308061, -51.218741)
plNext = AddPolyLine_Line_XY(plNext, 18.212216, -49.035918)
plNext = AddPolyLine_Arc_XY(plNext, 18.326397, -48.461893, 18.212216, -47.887868)
plNext = AddPolyLine_Line_XY(plNext, 17.124054, -45.260813)
plNext = AddPolyLine_Arc_XY(plNext, 15.798124, -44.374855, 14.472194, -45.260813)
plNext = AddPolyLine_Line_XY(plNext, 12.781051, -49.343592)
plNext = AddPolyLine_Line_XY(plNext, 5.701408, -66.435363)
plNext = AddPolyLine_Line_XY(plNext, 5.558326, -66.780794)
plNext = AddPolyLine_Arc_XY(plNext, 5.505365, -66.894874, 5.443032, -67.004117)
plNext = AddPolyLine_Line_XY(plNext, 4.499474, -68.507618)
ClosePolyLine_Arc_XY(plNext, 4.32851, -68.89011, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_21


# Create new component fluid_rotor_pocket_22
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_22", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(20.983855, 46.739818)
plNext = AddPolyLine_Line_XY(plStart, 19.895693, 44.112763)
plNext = AddPolyLine_Arc_XY(plNext, 20.2068, 42.548721, 21.770842, 42.237614)
plNext = AddPolyLine_Line_XY(plNext, 25.85362, 43.928757)
plNext = AddPolyLine_Line_XY(plNext, 42.945392, 51.0084)
plNext = AddPolyLine_Line_XY(plNext, 43.290822, 51.151482)
plNext = AddPolyLine_Arc_XY(plNext, 43.408939, 51.1947, 43.530261, 51.227871)
plNext = AddPolyLine_Line_XY(plNext, 45.260592, 51.62381)
plNext = AddPolyLine_Arc_XY(plNext, 45.651946, 51.773383, 45.986666, 52.025358)
plNext = AddPolyLine_Line_XY(plNext, 47.236808, 53.2755)
plNext = AddPolyLine_Arc_XY(plNext, 47.456012, 53.832268, 47.198125, 54.372208)
plNext = AddPolyLine_Arc_XY(plNext, 45.983505, 55.403224, 44.74637, 56.407113)
plNext = AddPolyLine_Arc_XY(plNext, 44.181281, 56.649229, 43.57145, 56.571444)
plNext = AddPolyLine_Line_XY(plNext, 41.070243, 55.53541)
plNext = AddPolyLine_Arc_XY(plNext, 41.452926, 55.53541, 41.723524, 55.264812)
plNext = AddPolyLine_Line_XY(plNext, 43.177721, 51.75407)
plNext = AddPolyLine_Arc_XY(plNext, 43.177721, 51.371386, 42.907123, 51.100788)
plNext = AddPolyLine_Line_XY(plNext, 26.277292, 44.212486)
plNext = AddPolyLine_Arc_XY(plNext, 25.894608, 44.212486, 25.62401, 44.483084)
plNext = AddPolyLine_Line_XY(plNext, 24.169813, 47.993827)
plNext = AddPolyLine_Arc_XY(plNext, 24.169813, 48.37651, 24.440411, 48.647108)
plNext = AddPolyLine_Line_XY(plNext, 23.978471, 48.455766)
plNext = AddPolyLine_Line_XY(plNext, 21.795649, 47.551612)
ClosePolyLine_Arc_XY(plNext, 21.309014, 47.226453, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_22


# Create new component fluid_rotor_pocket_23
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_23", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(43.928757, -25.85362)
plNext = AddPolyLine_Line_XY(plStart, 51.0084, -42.945392)
plNext = AddPolyLine_Line_XY(plNext, 51.151482, -43.290822)
plNext = AddPolyLine_Arc_XY(plNext, 51.1947, -43.408939, 51.227871, -43.530261)
plNext = AddPolyLine_Line_XY(plNext, 51.62381, -45.260592)
plNext = AddPolyLine_Arc_XY(plNext, 51.773383, -45.651946, 52.025358, -45.986666)
plNext = AddPolyLine_Line_XY(plNext, 53.2755, -47.236808)
plNext = AddPolyLine_Arc_XY(plNext, 53.832268, -47.456012, 54.372208, -47.198125)
plNext = AddPolyLine_Arc_XY(plNext, 55.403224, -45.983505, 56.407113, -44.74637)
plNext = AddPolyLine_Arc_XY(plNext, 56.649229, -44.181281, 56.571444, -43.57145)
plNext = AddPolyLine_Line_XY(plNext, 55.53541, -41.070243)
plNext = AddPolyLine_Arc_XY(plNext, 55.53541, -41.452926, 55.264812, -41.723524)
plNext = AddPolyLine_Line_XY(plNext, 51.75407, -43.177721)
plNext = AddPolyLine_Arc_XY(plNext, 51.371386, -43.177721, 51.100788, -42.907123)
plNext = AddPolyLine_Line_XY(plNext, 44.212486, -26.277292)
plNext = AddPolyLine_Arc_XY(plNext, 44.212486, -25.894608, 44.483084, -25.62401)
plNext = AddPolyLine_Line_XY(plNext, 47.993827, -24.169813)
plNext = AddPolyLine_Arc_XY(plNext, 48.37651, -24.169813, 48.647108, -24.440411)
plNext = AddPolyLine_Line_XY(plNext, 48.455766, -23.978471)
plNext = AddPolyLine_Line_XY(plNext, 47.551612, -21.795649)
plNext = AddPolyLine_Arc_XY(plNext, 47.226453, -21.309014, 46.739818, -20.983855)
plNext = AddPolyLine_Line_XY(plNext, 44.112763, -19.895693)
plNext = AddPolyLine_Arc_XY(plNext, 42.548721, -20.2068, 42.237614, -21.770842)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_23


# Create new component fluid_rotor_pocket_24
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_24", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(47.887868, 18.212216)
plNext = AddPolyLine_Line_XY(plStart, 45.260813, 17.124054)
plNext = AddPolyLine_Arc_XY(plNext, 44.374855, 15.798124, 45.260813, 14.472194)
plNext = AddPolyLine_Line_XY(plNext, 49.343592, 12.781051)
plNext = AddPolyLine_Line_XY(plNext, 66.435363, 5.701408)
plNext = AddPolyLine_Line_XY(plNext, 66.780794, 5.558326)
plNext = AddPolyLine_Arc_XY(plNext, 66.894874, 5.505365, 67.004117, 5.443032)
plNext = AddPolyLine_Line_XY(plNext, 68.507618, 4.499474)
plNext = AddPolyLine_Arc_XY(plNext, 68.89011, 4.32851, 69.304967, 4.27)
plNext = AddPolyLine_Line_XY(plNext, 71.072935, 4.27)
plNext = AddPolyLine_Arc_XY(plNext, 71.62163, 4.508694, 71.821071, 5.072842)
plNext = AddPolyLine_Arc_XY(plNext, 71.691244, 6.660747, 71.526314, 8.24539)
plNext = AddPolyLine_Arc_XY(plNext, 71.297938, 8.81617, 70.811719, 9.192384)
plNext = AddPolyLine_Line_XY(plNext, 68.310512, 10.228418)
plNext = AddPolyLine_Arc_XY(plNext, 68.58111, 9.95782, 68.58111, 9.575136)
plNext = AddPolyLine_Line_XY(plNext, 67.126913, 6.064394)
plNext = AddPolyLine_Arc_XY(plNext, 66.856315, 5.793796, 66.473632, 5.793796)
plNext = AddPolyLine_Line_XY(plNext, 49.8438, 12.682098)
plNext = AddPolyLine_Arc_XY(plNext, 49.573202, 12.952696, 49.573202, 13.335379)
plNext = AddPolyLine_Line_XY(plNext, 51.027399, 16.846121)
plNext = AddPolyLine_Arc_XY(plNext, 51.297997, 17.116719, 51.68068, 17.11672)
plNext = AddPolyLine_Line_XY(plNext, 51.218741, 17.308061)
plNext = AddPolyLine_Line_XY(plNext, 49.035918, 18.212216)
ClosePolyLine_Arc_XY(plNext, 48.461893, 18.326397, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_24


# Create new component fluid_rotor_pocket_25
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_25", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-55.53541, -41.070243)
plNext = AddPolyLine_Line_XY(plStart, -56.571444, -43.57145)
plNext = AddPolyLine_Arc_XY(plNext, -56.649229, -44.181281, -56.407113, -44.74637)
plNext = AddPolyLine_Arc_XY(plNext, -55.403224, -45.983505, -54.372208, -47.198125)
plNext = AddPolyLine_Arc_XY(plNext, -53.832268, -47.456012, -53.2755, -47.236808)
plNext = AddPolyLine_Line_XY(plNext, -52.025358, -45.986666)
plNext = AddPolyLine_Arc_XY(plNext, -51.773383, -45.651946, -51.62381, -45.260592)
plNext = AddPolyLine_Line_XY(plNext, -51.227871, -43.530261)
plNext = AddPolyLine_Arc_XY(plNext, -51.1947, -43.408939, -51.151482, -43.290822)
plNext = AddPolyLine_Line_XY(plNext, -51.0084, -42.945392)
plNext = AddPolyLine_Line_XY(plNext, -43.928757, -25.85362)
plNext = AddPolyLine_Line_XY(plNext, -42.237614, -21.770842)
plNext = AddPolyLine_Arc_XY(plNext, -42.548721, -20.2068, -44.112763, -19.895693)
plNext = AddPolyLine_Line_XY(plNext, -46.739818, -20.983855)
plNext = AddPolyLine_Arc_XY(plNext, -47.226453, -21.309014, -47.551612, -21.795649)
plNext = AddPolyLine_Line_XY(plNext, -48.455766, -23.978471)
plNext = AddPolyLine_Line_XY(plNext, -48.647108, -24.440411)
plNext = AddPolyLine_Arc_XY(plNext, -48.37651, -24.169813, -47.993827, -24.169813)
plNext = AddPolyLine_Line_XY(plNext, -44.483084, -25.62401)
plNext = AddPolyLine_Arc_XY(plNext, -44.212486, -25.894608, -44.212486, -26.277292)
plNext = AddPolyLine_Line_XY(plNext, -51.100788, -42.907123)
plNext = AddPolyLine_Arc_XY(plNext, -51.371386, -43.177721, -51.75407, -43.177721)
plNext = AddPolyLine_Line_XY(plNext, -55.264812, -41.723524)
ClosePolyLine_Arc_XY(plNext, -55.53541, -41.452926, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_25


# Create new component fluid_rotor_pocket_26
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_26", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-45.986666, 52.025358)
plNext = AddPolyLine_Arc_XY(plStart, -45.651946, 51.773383, -45.260592, 51.62381)
plNext = AddPolyLine_Line_XY(plNext, -43.530261, 51.227871)
plNext = AddPolyLine_Arc_XY(plNext, -43.408939, 51.1947, -43.290822, 51.151482)
plNext = AddPolyLine_Line_XY(plNext, -42.945392, 51.0084)
plNext = AddPolyLine_Line_XY(plNext, -25.85362, 43.928757)
plNext = AddPolyLine_Line_XY(plNext, -21.770842, 42.237614)
plNext = AddPolyLine_Arc_XY(plNext, -20.2068, 42.548721, -19.895693, 44.112763)
plNext = AddPolyLine_Line_XY(plNext, -20.983855, 46.739818)
plNext = AddPolyLine_Arc_XY(plNext, -21.309014, 47.226453, -21.795649, 47.551612)
plNext = AddPolyLine_Line_XY(plNext, -23.978471, 48.455766)
plNext = AddPolyLine_Line_XY(plNext, -24.440411, 48.647108)
plNext = AddPolyLine_Arc_XY(plNext, -24.169813, 48.37651, -24.169813, 47.993827)
plNext = AddPolyLine_Line_XY(plNext, -25.62401, 44.483084)
plNext = AddPolyLine_Arc_XY(plNext, -25.894608, 44.212486, -26.277292, 44.212486)
plNext = AddPolyLine_Line_XY(plNext, -42.907123, 51.100788)
plNext = AddPolyLine_Arc_XY(plNext, -43.177721, 51.371386, -43.177721, 51.75407)
plNext = AddPolyLine_Line_XY(plNext, -41.723524, 55.264812)
plNext = AddPolyLine_Arc_XY(plNext, -41.452926, 55.53541, -41.070243, 55.53541)
plNext = AddPolyLine_Line_XY(plNext, -43.57145, 56.571444)
plNext = AddPolyLine_Arc_XY(plNext, -44.181281, 56.649229, -44.74637, 56.407113)
plNext = AddPolyLine_Arc_XY(plNext, -45.983505, 55.403224, -47.198125, 54.372208)
plNext = AddPolyLine_Arc_XY(plNext, -47.456012, 53.832268, -47.236808, 53.2755)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_26


# Create new component fluid_rotor_pocket_27
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_27", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-17.124054, -45.260813)
plNext = AddPolyLine_Line_XY(plStart, -18.212216, -47.887868)
plNext = AddPolyLine_Arc_XY(plNext, -18.326397, -48.461893, -18.212216, -49.035918)
plNext = AddPolyLine_Line_XY(plNext, -17.308061, -51.218741)
plNext = AddPolyLine_Line_XY(plNext, -17.116719, -51.68068)
plNext = AddPolyLine_Arc_XY(plNext, -17.11672, -51.297997, -16.846121, -51.027399)
plNext = AddPolyLine_Line_XY(plNext, -13.335379, -49.573202)
plNext = AddPolyLine_Arc_XY(plNext, -12.952696, -49.573202, -12.682098, -49.8438)
plNext = AddPolyLine_Line_XY(plNext, -5.793796, -66.473632)
plNext = AddPolyLine_Arc_XY(plNext, -5.793796, -66.856315, -6.064394, -67.126913)
plNext = AddPolyLine_Line_XY(plNext, -9.575136, -68.58111)
plNext = AddPolyLine_Arc_XY(plNext, -9.95782, -68.58111, -10.228418, -68.310512)
plNext = AddPolyLine_Line_XY(plNext, -9.192384, -70.811719)
plNext = AddPolyLine_Arc_XY(plNext, -8.81617, -71.297938, -8.24539, -71.526314)
plNext = AddPolyLine_Arc_XY(plNext, -6.660747, -71.691244, -5.072842, -71.821071)
plNext = AddPolyLine_Arc_XY(plNext, -4.508694, -71.62163, -4.27, -71.072935)
plNext = AddPolyLine_Line_XY(plNext, -4.27, -69.304967)
plNext = AddPolyLine_Arc_XY(plNext, -4.32851, -68.89011, -4.499474, -68.507618)
plNext = AddPolyLine_Line_XY(plNext, -5.443032, -67.004117)
plNext = AddPolyLine_Arc_XY(plNext, -5.505365, -66.894874, -5.558326, -66.780794)
plNext = AddPolyLine_Line_XY(plNext, -5.701408, -66.435363)
plNext = AddPolyLine_Line_XY(plNext, -12.781051, -49.343592)
plNext = AddPolyLine_Line_XY(plNext, -14.472194, -45.260813)
ClosePolyLine_Arc_XY(plNext, -15.798124, -44.374855, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_27


# Create new component fluid_rotor_pocket_28
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_28", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(4.27, 71.072935)
plNext = AddPolyLine_Line_XY(plStart, 4.27, 69.304967)
plNext = AddPolyLine_Arc_XY(plNext, 4.32851, 68.89011, 4.499474, 68.507618)
plNext = AddPolyLine_Line_XY(plNext, 5.443032, 67.004117)
plNext = AddPolyLine_Arc_XY(plNext, 5.505365, 66.894874, 5.558326, 66.780794)
plNext = AddPolyLine_Line_XY(plNext, 5.701408, 66.435363)
plNext = AddPolyLine_Line_XY(plNext, 12.781051, 49.343592)
plNext = AddPolyLine_Line_XY(plNext, 14.472194, 45.260813)
plNext = AddPolyLine_Arc_XY(plNext, 15.798124, 44.374855, 17.124054, 45.260813)
plNext = AddPolyLine_Line_XY(plNext, 18.212216, 47.887868)
plNext = AddPolyLine_Arc_XY(plNext, 18.326397, 48.461893, 18.212216, 49.035918)
plNext = AddPolyLine_Line_XY(plNext, 17.308061, 51.218741)
plNext = AddPolyLine_Line_XY(plNext, 17.116719, 51.68068)
plNext = AddPolyLine_Arc_XY(plNext, 17.11672, 51.297997, 16.846121, 51.027399)
plNext = AddPolyLine_Line_XY(plNext, 13.335379, 49.573202)
plNext = AddPolyLine_Arc_XY(plNext, 12.952696, 49.573202, 12.682098, 49.8438)
plNext = AddPolyLine_Line_XY(plNext, 5.793796, 66.473632)
plNext = AddPolyLine_Arc_XY(plNext, 5.793796, 66.856315, 6.064394, 67.126913)
plNext = AddPolyLine_Line_XY(plNext, 9.575136, 68.58111)
plNext = AddPolyLine_Arc_XY(plNext, 9.95782, 68.58111, 10.228418, 68.310512)
plNext = AddPolyLine_Line_XY(plNext, 9.192384, 70.811719)
plNext = AddPolyLine_Arc_XY(plNext, 8.81617, 71.297938, 8.24539, 71.526314)
plNext = AddPolyLine_Arc_XY(plNext, 6.660747, 71.691244, 5.072842, 71.821071)
ClosePolyLine_Arc_XY(plNext, 4.508694, 71.62163, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_28


# Create new component fluid_rotor_pocket_29
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_29", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(20.983855, -46.739818)
plNext = AddPolyLine_Arc_XY(plStart, 21.309014, -47.226453, 21.795649, -47.551612)
plNext = AddPolyLine_Line_XY(plNext, 23.978471, -48.455766)
plNext = AddPolyLine_Line_XY(plNext, 24.440411, -48.647108)
plNext = AddPolyLine_Arc_XY(plNext, 24.169813, -48.37651, 24.169813, -47.993827)
plNext = AddPolyLine_Line_XY(plNext, 25.62401, -44.483084)
plNext = AddPolyLine_Arc_XY(plNext, 25.894608, -44.212486, 26.277292, -44.212486)
plNext = AddPolyLine_Line_XY(plNext, 42.907123, -51.100788)
plNext = AddPolyLine_Arc_XY(plNext, 43.177721, -51.371386, 43.177721, -51.75407)
plNext = AddPolyLine_Line_XY(plNext, 41.723524, -55.264812)
plNext = AddPolyLine_Arc_XY(plNext, 41.452926, -55.53541, 41.070243, -55.53541)
plNext = AddPolyLine_Line_XY(plNext, 43.57145, -56.571444)
plNext = AddPolyLine_Arc_XY(plNext, 44.181281, -56.649229, 44.74637, -56.407113)
plNext = AddPolyLine_Arc_XY(plNext, 45.983505, -55.403224, 47.198125, -54.372208)
plNext = AddPolyLine_Arc_XY(plNext, 47.456012, -53.832268, 47.236808, -53.2755)
plNext = AddPolyLine_Line_XY(plNext, 45.986666, -52.025358)
plNext = AddPolyLine_Arc_XY(plNext, 45.651946, -51.773383, 45.260592, -51.62381)
plNext = AddPolyLine_Line_XY(plNext, 43.530261, -51.227871)
plNext = AddPolyLine_Arc_XY(plNext, 43.408939, -51.1947, 43.290822, -51.151482)
plNext = AddPolyLine_Line_XY(plNext, 42.945392, -51.0084)
plNext = AddPolyLine_Line_XY(plNext, 25.85362, -43.928757)
plNext = AddPolyLine_Line_XY(plNext, 21.770842, -42.237614)
plNext = AddPolyLine_Arc_XY(plNext, 20.2068, -42.548721, 19.895693, -44.112763)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_29


# Create new component fluid_rotor_pocket_30
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_30", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(43.928757, 25.85362)
plNext = AddPolyLine_Line_XY(plStart, 42.237614, 21.770842)
plNext = AddPolyLine_Arc_XY(plNext, 42.548721, 20.2068, 44.112763, 19.895693)
plNext = AddPolyLine_Line_XY(plNext, 46.739818, 20.983855)
plNext = AddPolyLine_Arc_XY(plNext, 47.226453, 21.309014, 47.551612, 21.795649)
plNext = AddPolyLine_Line_XY(plNext, 48.455766, 23.978471)
plNext = AddPolyLine_Line_XY(plNext, 48.647108, 24.440411)
plNext = AddPolyLine_Arc_XY(plNext, 48.37651, 24.169813, 47.993827, 24.169813)
plNext = AddPolyLine_Line_XY(plNext, 44.483084, 25.62401)
plNext = AddPolyLine_Arc_XY(plNext, 44.212486, 25.894608, 44.212486, 26.277292)
plNext = AddPolyLine_Line_XY(plNext, 51.100788, 42.907123)
plNext = AddPolyLine_Arc_XY(plNext, 51.371386, 43.177721, 51.75407, 43.177721)
plNext = AddPolyLine_Line_XY(plNext, 55.264812, 41.723524)
plNext = AddPolyLine_Arc_XY(plNext, 55.53541, 41.452926, 55.53541, 41.070243)
plNext = AddPolyLine_Line_XY(plNext, 56.571444, 43.57145)
plNext = AddPolyLine_Arc_XY(plNext, 56.649229, 44.181281, 56.407113, 44.74637)
plNext = AddPolyLine_Arc_XY(plNext, 55.403224, 45.983505, 54.372208, 47.198125)
plNext = AddPolyLine_Arc_XY(plNext, 53.832268, 47.456012, 53.2755, 47.236808)
plNext = AddPolyLine_Line_XY(plNext, 52.025358, 45.986666)
plNext = AddPolyLine_Arc_XY(plNext, 51.773383, 45.651946, 51.62381, 45.260592)
plNext = AddPolyLine_Line_XY(plNext, 51.227871, 43.530261)
plNext = AddPolyLine_Arc_XY(plNext, 51.1947, 43.408939, 51.151482, 43.290822)
plNext = AddPolyLine_Line_XY(plNext, 51.0084, 42.945392)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_30


# Create new component fluid_rotor_pocket_31
newComp = CreateNamedComponentWithColour_Radial("fluid_rotor_pocket_31", -54.5, -96, 241, 241, 240, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(47.887868, -18.212216)
plNext = AddPolyLine_Arc_XY(plStart, 48.461893, -18.326397, 49.035918, -18.212216)
plNext = AddPolyLine_Line_XY(plNext, 51.218741, -17.308061)
plNext = AddPolyLine_Line_XY(plNext, 51.68068, -17.116719)
plNext = AddPolyLine_Arc_XY(plNext, 51.297997, -17.11672, 51.027399, -16.846121)
plNext = AddPolyLine_Line_XY(plNext, 49.573202, -13.335379)
plNext = AddPolyLine_Arc_XY(plNext, 49.573202, -12.952696, 49.8438, -12.682098)
plNext = AddPolyLine_Line_XY(plNext, 66.473632, -5.793796)
plNext = AddPolyLine_Arc_XY(plNext, 66.856315, -5.793796, 67.126913, -6.064394)
plNext = AddPolyLine_Line_XY(plNext, 68.58111, -9.575136)
plNext = AddPolyLine_Arc_XY(plNext, 68.58111, -9.95782, 68.310512, -10.228418)
plNext = AddPolyLine_Line_XY(plNext, 70.811719, -9.192384)
plNext = AddPolyLine_Arc_XY(plNext, 71.297938, -8.81617, 71.526314, -8.24539)
plNext = AddPolyLine_Arc_XY(plNext, 71.691244, -6.660747, 71.821071, -5.072842)
plNext = AddPolyLine_Arc_XY(plNext, 71.62163, -4.508694, 71.072935, -4.27)
plNext = AddPolyLine_Line_XY(plNext, 69.304967, -4.27)
plNext = AddPolyLine_Arc_XY(plNext, 68.89011, -4.32851, 68.507618, -4.499474)
plNext = AddPolyLine_Line_XY(plNext, 67.004117, -5.443032)
plNext = AddPolyLine_Arc_XY(plNext, 66.894874, -5.505365, 66.780794, -5.558326)
plNext = AddPolyLine_Line_XY(plNext, 66.435363, -5.701408)
plNext = AddPolyLine_Line_XY(plNext, 49.343592, -12.781051)
plNext = AddPolyLine_Line_XY(plNext, 45.260813, -14.472194)
plNext = AddPolyLine_Arc_XY(plNext, 44.374855, -15.798124, 45.260813, -17.124054)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component fluid_rotor_pocket_31


# Create new component magnet_p4_l1_m0_s_2
newComp = CreateNamedComponentWithColour_Radial("magnet_p4_l1_m0_s_2", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(9.575136, 68.58111)
plNext = AddPolyLine_Line_XY(plStart, 6.064394, 67.126913)
plNext = AddPolyLine_Arc_XY(plNext, 5.793796, 66.856315, 5.793796, 66.473632)
plNext = AddPolyLine_Line_XY(plNext, 12.682098, 49.8438)
plNext = AddPolyLine_Arc_XY(plNext, 12.952696, 49.573202, 13.335379, 49.573202)
plNext = AddPolyLine_Line_XY(plNext, 16.846121, 51.027399)
plNext = AddPolyLine_Arc_XY(plNext, 17.11672, 51.297997, 17.116719, 51.68068)
plNext = AddPolyLine_Line_XY(plNext, 10.228418, 68.310512)
ClosePolyLine_Arc_XY(plNext, 9.95782, 68.58111, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p4_l1_m0_s_2


# Create new component magnet_p3_l1_m0_s_2
newComp = CreateNamedComponentWithColour_Radial("magnet_p3_l1_m0_s_2", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-41.723524, 55.264812)
plNext = AddPolyLine_Line_XY(plStart, -43.177721, 51.75407)
plNext = AddPolyLine_Arc_XY(plNext, -43.177721, 51.371386, -42.907123, 51.100788)
plNext = AddPolyLine_Line_XY(plNext, -26.277292, 44.212486)
plNext = AddPolyLine_Arc_XY(plNext, -25.894608, 44.212486, -25.62401, 44.483084)
plNext = AddPolyLine_Line_XY(plNext, -24.169813, 47.993827)
plNext = AddPolyLine_Arc_XY(plNext, -24.169813, 48.37651, -24.440411, 48.647108)
plNext = AddPolyLine_Line_XY(plNext, -41.070243, 55.53541)
ClosePolyLine_Arc_XY(plNext, -41.452926, 55.53541, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p3_l1_m0_s_2


# Create new component magnet_p6_l1_m0_s_2
newComp = CreateNamedComponentWithColour_Radial("magnet_p6_l1_m0_s_2", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-68.58111, 9.575136)
plNext = AddPolyLine_Line_XY(plStart, -67.126913, 6.064394)
plNext = AddPolyLine_Arc_XY(plNext, -66.856315, 5.793796, -66.473632, 5.793796)
plNext = AddPolyLine_Line_XY(plNext, -49.8438, 12.682098)
plNext = AddPolyLine_Arc_XY(plNext, -49.573202, 12.952696, -49.573202, 13.335379)
plNext = AddPolyLine_Line_XY(plNext, -51.027399, 16.846121)
plNext = AddPolyLine_Arc_XY(plNext, -51.297997, 17.11672, -51.68068, 17.116719)
plNext = AddPolyLine_Line_XY(plNext, -68.310512, 10.228418)
ClosePolyLine_Arc_XY(plNext, -68.58111, 9.95782, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p6_l1_m0_s_2


# Create new component magnet_p5_l1_m0_s_2
newComp = CreateNamedComponentWithColour_Radial("magnet_p5_l1_m0_s_2", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-55.264812, -41.723524)
plNext = AddPolyLine_Line_XY(plStart, -51.75407, -43.177721)
plNext = AddPolyLine_Arc_XY(plNext, -51.371386, -43.177721, -51.100788, -42.907123)
plNext = AddPolyLine_Line_XY(plNext, -44.212486, -26.277292)
plNext = AddPolyLine_Arc_XY(plNext, -44.212486, -25.894608, -44.483084, -25.62401)
plNext = AddPolyLine_Line_XY(plNext, -47.993827, -24.169813)
plNext = AddPolyLine_Arc_XY(plNext, -48.37651, -24.169813, -48.647108, -24.440411)
plNext = AddPolyLine_Line_XY(plNext, -55.53541, -41.070243)
ClosePolyLine_Arc_XY(plNext, -55.53541, -41.452926, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p5_l1_m0_s_2


# Create new component magnet_p8_l1_m0_s_2
newComp = CreateNamedComponentWithColour_Radial("magnet_p8_l1_m0_s_2", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-9.575136, -68.58111)
plNext = AddPolyLine_Line_XY(plStart, -6.064394, -67.126913)
plNext = AddPolyLine_Arc_XY(plNext, -5.793796, -66.856315, -5.793796, -66.473632)
plNext = AddPolyLine_Line_XY(plNext, -12.682098, -49.8438)
plNext = AddPolyLine_Arc_XY(plNext, -12.952696, -49.573202, -13.335379, -49.573202)
plNext = AddPolyLine_Line_XY(plNext, -16.846121, -51.027399)
plNext = AddPolyLine_Arc_XY(plNext, -17.11672, -51.297997, -17.116719, -51.68068)
plNext = AddPolyLine_Line_XY(plNext, -10.228418, -68.310512)
ClosePolyLine_Arc_XY(plNext, -9.95782, -68.58111, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p8_l1_m0_s_2


# Create new component magnet_p7_l1_m0_s_2
newComp = CreateNamedComponentWithColour_Radial("magnet_p7_l1_m0_s_2", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(41.723524, -55.264812)
plNext = AddPolyLine_Line_XY(plStart, 43.177721, -51.75407)
plNext = AddPolyLine_Arc_XY(plNext, 43.177721, -51.371386, 42.907123, -51.100788)
plNext = AddPolyLine_Line_XY(plNext, 26.277292, -44.212486)
plNext = AddPolyLine_Arc_XY(plNext, 25.894608, -44.212486, 25.62401, -44.483084)
plNext = AddPolyLine_Line_XY(plNext, 24.169813, -47.993827)
plNext = AddPolyLine_Arc_XY(plNext, 24.169813, -48.37651, 24.440411, -48.647108)
plNext = AddPolyLine_Line_XY(plNext, 41.070243, -55.53541)
ClosePolyLine_Arc_XY(plNext, 41.452926, -55.53541, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p7_l1_m0_s_2


# Create new component magnet_p2_l1_m0_s_2
newComp = CreateNamedComponentWithColour_Radial("magnet_p2_l1_m0_s_2", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(68.58111, -9.575136)
plNext = AddPolyLine_Line_XY(plStart, 67.126913, -6.064394)
plNext = AddPolyLine_Arc_XY(plNext, 66.856315, -5.793796, 66.473632, -5.793796)
plNext = AddPolyLine_Line_XY(plNext, 49.8438, -12.682098)
plNext = AddPolyLine_Arc_XY(plNext, 49.573202, -12.952696, 49.573202, -13.335379)
plNext = AddPolyLine_Line_XY(plNext, 51.027399, -16.846121)
plNext = AddPolyLine_Arc_XY(plNext, 51.297997, -17.11672, 51.68068, -17.116719)
plNext = AddPolyLine_Line_XY(plNext, 68.310512, -10.228418)
ClosePolyLine_Arc_XY(plNext, 68.58111, -9.95782, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p2_l1_m0_s_2


# Create new component magnet_p4_l1_m0_s_3
newComp = CreateNamedComponentWithColour_Radial("magnet_p4_l1_m0_s_3", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(43.177721, 51.75407)
plNext = AddPolyLine_Line_XY(plStart, 41.723524, 55.264812)
plNext = AddPolyLine_Arc_XY(plNext, 41.452926, 55.53541, 41.070243, 55.53541)
plNext = AddPolyLine_Line_XY(plNext, 24.440411, 48.647108)
plNext = AddPolyLine_Arc_XY(plNext, 24.169813, 48.37651, 24.169813, 47.993827)
plNext = AddPolyLine_Line_XY(plNext, 25.62401, 44.483084)
plNext = AddPolyLine_Arc_XY(plNext, 25.894608, 44.212486, 26.277292, 44.212486)
plNext = AddPolyLine_Line_XY(plNext, 42.907123, 51.100788)
ClosePolyLine_Arc_XY(plNext, 43.177721, 51.371386, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p4_l1_m0_s_3


# Create new component magnet_p3_l1_m0_s_3
newComp = CreateNamedComponentWithColour_Radial("magnet_p3_l1_m0_s_3", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-6.064394, 67.126913)
plNext = AddPolyLine_Line_XY(plStart, -9.575136, 68.58111)
plNext = AddPolyLine_Arc_XY(plNext, -9.95782, 68.58111, -10.228418, 68.310512)
plNext = AddPolyLine_Line_XY(plNext, -17.11672, 51.68068)
plNext = AddPolyLine_Arc_XY(plNext, -17.116719, 51.297997, -16.846121, 51.027399)
plNext = AddPolyLine_Line_XY(plNext, -13.335379, 49.573202)
plNext = AddPolyLine_Arc_XY(plNext, -12.952696, 49.573202, -12.682098, 49.8438)
plNext = AddPolyLine_Line_XY(plNext, -5.793796, 66.473632)
ClosePolyLine_Arc_XY(plNext, -5.793796, 66.856315, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p3_l1_m0_s_3


# Create new component magnet_p6_l1_m0_s_3
newComp = CreateNamedComponentWithColour_Radial("magnet_p6_l1_m0_s_3", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-51.75407, 43.177721)
plNext = AddPolyLine_Line_XY(plStart, -55.264812, 41.723524)
plNext = AddPolyLine_Arc_XY(plNext, -55.53541, 41.452926, -55.53541, 41.070243)
plNext = AddPolyLine_Line_XY(plNext, -48.647108, 24.440411)
plNext = AddPolyLine_Arc_XY(plNext, -48.37651, 24.169813, -47.993827, 24.169813)
plNext = AddPolyLine_Line_XY(plNext, -44.483084, 25.62401)
plNext = AddPolyLine_Arc_XY(plNext, -44.212486, 25.894608, -44.212486, 26.277292)
plNext = AddPolyLine_Line_XY(plNext, -51.100788, 42.907123)
ClosePolyLine_Arc_XY(plNext, -51.371386, 43.177721, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p6_l1_m0_s_3


# Create new component magnet_p5_l1_m0_s_3
newComp = CreateNamedComponentWithColour_Radial("magnet_p5_l1_m0_s_3", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-67.126913, -6.064394)
plNext = AddPolyLine_Line_XY(plStart, -68.58111, -9.575136)
plNext = AddPolyLine_Arc_XY(plNext, -68.58111, -9.95782, -68.310512, -10.228418)
plNext = AddPolyLine_Line_XY(plNext, -51.68068, -17.11672)
plNext = AddPolyLine_Arc_XY(plNext, -51.297997, -17.116719, -51.027399, -16.846121)
plNext = AddPolyLine_Line_XY(plNext, -49.573202, -13.335379)
plNext = AddPolyLine_Arc_XY(plNext, -49.573202, -12.952696, -49.8438, -12.682098)
plNext = AddPolyLine_Line_XY(plNext, -66.473632, -5.793796)
ClosePolyLine_Arc_XY(plNext, -66.856315, -5.793796, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p5_l1_m0_s_3


# Create new component magnet_p8_l1_m0_s_3
newComp = CreateNamedComponentWithColour_Radial("magnet_p8_l1_m0_s_3", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-43.177721, -51.75407)
plNext = AddPolyLine_Line_XY(plStart, -41.723524, -55.264812)
plNext = AddPolyLine_Arc_XY(plNext, -41.452926, -55.53541, -41.070243, -55.53541)
plNext = AddPolyLine_Line_XY(plNext, -24.440411, -48.647108)
plNext = AddPolyLine_Arc_XY(plNext, -24.169813, -48.37651, -24.169813, -47.993827)
plNext = AddPolyLine_Line_XY(plNext, -25.62401, -44.483084)
plNext = AddPolyLine_Arc_XY(plNext, -25.894608, -44.212486, -26.277292, -44.212486)
plNext = AddPolyLine_Line_XY(plNext, -42.907123, -51.100788)
ClosePolyLine_Arc_XY(plNext, -43.177721, -51.371386, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p8_l1_m0_s_3


# Create new component magnet_p7_l1_m0_s_3
newComp = CreateNamedComponentWithColour_Radial("magnet_p7_l1_m0_s_3", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(6.064394, -67.126913)
plNext = AddPolyLine_Line_XY(plStart, 9.575136, -68.58111)
plNext = AddPolyLine_Arc_XY(plNext, 9.95782, -68.58111, 10.228418, -68.310512)
plNext = AddPolyLine_Line_XY(plNext, 17.11672, -51.68068)
plNext = AddPolyLine_Arc_XY(plNext, 17.116719, -51.297997, 16.846121, -51.027399)
plNext = AddPolyLine_Line_XY(plNext, 13.335379, -49.573202)
plNext = AddPolyLine_Arc_XY(plNext, 12.952696, -49.573202, 12.682098, -49.8438)
plNext = AddPolyLine_Line_XY(plNext, 5.793796, -66.473632)
ClosePolyLine_Arc_XY(plNext, 5.793796, -66.856315, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p7_l1_m0_s_3


# Create new component magnet_p2_l1_m0_s_3
newComp = CreateNamedComponentWithColour_Radial("magnet_p2_l1_m0_s_3", -54.5, -96, 0, 212, 0, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(51.75407, -43.177721)
plNext = AddPolyLine_Line_XY(plStart, 55.264812, -41.723524)
plNext = AddPolyLine_Arc_XY(plNext, 55.53541, -41.452926, 55.53541, -41.070243)
plNext = AddPolyLine_Line_XY(plNext, 48.647108, -24.440411)
plNext = AddPolyLine_Arc_XY(plNext, 48.37651, -24.169813, 47.993827, -24.169813)
plNext = AddPolyLine_Line_XY(plNext, 44.483084, -25.62401)
plNext = AddPolyLine_Arc_XY(plNext, 44.212486, -25.894608, 44.212486, -26.277292)
plNext = AddPolyLine_Line_XY(plNext, 51.100788, -42.907123)
ClosePolyLine_Arc_XY(plNext, 51.371386, -43.177721, plStart)
# End of Outline 1 PolyLine

# End of component magnet_p2_l1_m0_s_3


# Create new component shaft_active
newComp = CreateNamedComponentWithColour_Radial("shaft_active", -54.5, -96, 207, 207, 207, comp_Rotor)

# Outline 1 PolyLine
plStart = GetPoint(-35, 0)
plNext = AddPolyLine_Arc_XY(plStart, -32.335784, -13.39392, -24.748737, -24.748737)
plNext = AddPolyLine_Arc_XY(plNext, -13.39392, -32.335784, 0, -35)
plNext = AddPolyLine_Arc_XY(plNext, 13.39392, -32.335784, 24.748737, -24.748737)
plNext = AddPolyLine_Arc_XY(plNext, 32.335784, -13.39392, 35, 0)
plNext = AddPolyLine_Arc_XY(plNext, 32.335784, 13.39392, 24.748737, 24.748737)
plNext = AddPolyLine_Arc_XY(plNext, 13.39392, 32.335784, 0, 35)
plNext = AddPolyLine_Arc_XY(plNext, -13.39392, 32.335784, -24.748737, 24.748737)
ClosePolyLine_Arc_XY(plNext, -32.335784, 13.39392, plStart)
# End of Outline 1 PolyLine

# End of component shaft_active


# Create new component statorwedge_1
newComp = CreateNamedComponentWithColour_Radial("statorwedge_1", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-77.580021, -7.229455)
plNext = AddPolyLine_Line_XY(plStart, -76.793526, -5.634601)
plNext = AddPolyLine_Line_XY(plNext, -76.872009, -4.43717)
plNext = AddPolyLine_Line_XY(plNext, -77.859946, -2.958619)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_1


# Create new component statorwedge_2
newComp = CreateNamedComponentWithColour_Radial("statorwedge_2", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-75.635192, 14.43302)
plNext = AddPolyLine_Line_XY(plStart, -75.401083, 15.609963)
plNext = AddPolyLine_Line_XY(plNext, -75.972679, 17.293831)
plNext = AddPolyLine_Line_XY(plNext, -76.807666, 13.09607)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_2


# Create new component statorwedge_3
newComp = CreateNamedComponentWithColour_Radial("statorwedge_3", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-75.972679, -17.293831)
plNext = AddPolyLine_Line_XY(plStart, -75.401083, -15.609963)
plNext = AddPolyLine_Line_XY(plNext, -75.635192, -14.43302)
plNext = AddPolyLine_Line_XY(plNext, -76.807666, -13.09607)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_3


# Create new component statorwedge_4
newComp = CreateNamedComponentWithColour_Radial("statorwedge_4", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-73.104235, 24.181917)
plNext = AddPolyLine_Line_XY(plStart, -72.718508, 25.318234)
plNext = AddPolyLine_Line_XY(plNext, -73.065425, 27.062304)
plNext = AddPolyLine_Line_XY(plNext, -74.441186, 23.009443)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_4


# Create new component statorwedge_5
newComp = CreateNamedComponentWithColour_Radial("statorwedge_5", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-73.065425, -27.062304)
plNext = AddPolyLine_Line_XY(plStart, -72.718508, -25.318234)
plNext = AddPolyLine_Line_XY(plNext, -73.104235, -24.181917)
plNext = AddPolyLine_Line_XY(plNext, -74.441186, -23.009443)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_5


# Create new component statorwedge_6
newComp = CreateNamedComponentWithColour_Radial("statorwedge_6", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-69.322445, 33.517055)
plNext = AddPolyLine_Line_XY(plStart, -68.791698, 34.593302)
plNext = AddPolyLine_Line_XY(plNext, -68.908, 36.367734)
plNext = AddPolyLine_Line_XY(plNext, -70.800996, 32.529119)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_6


# Create new component statorwedge_7
newComp = CreateNamedComponentWithColour_Radial("statorwedge_7", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-68.908, -36.367734)
plNext = AddPolyLine_Line_XY(plStart, -68.791698, -34.593302)
plNext = AddPolyLine_Line_XY(plNext, -69.322445, -33.517055)
plNext = AddPolyLine_Line_XY(plNext, -70.800996, -32.529119)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_7


# Create new component statorwedge_8
newComp = CreateNamedComponentWithColour_Radial("statorwedge_8", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-64.354528, 42.278707)
plNext = AddPolyLine_Line_XY(plStart, -63.687844, 43.27647)
plNext = AddPolyLine_Line_XY(plNext, -63.571541, 45.050902)
plNext = AddPolyLine_Line_XY(plNext, -65.949382, 41.492212)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_8


# Create new component statorwedge_9
newComp = CreateNamedComponentWithColour_Radial("statorwedge_9", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-63.571541, -45.050902)
plNext = AddPolyLine_Line_XY(plStart, -63.687844, -43.27647)
plNext = AddPolyLine_Line_XY(plNext, -64.354528, -42.278707)
plNext = AddPolyLine_Line_XY(plNext, -65.949382, -41.492212)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_9


# Create new component statorwedge_10
newComp = CreateNamedComponentWithColour_Radial("statorwedge_10", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-58.285487, 50.316958)
plNext = AddPolyLine_Line_XY(plStart, -57.494272, 51.219166)
plNext = AddPolyLine_Line_XY(plNext, -57.147355, 52.963236)
plNext = AddPolyLine_Line_XY(plNext, -59.969355, 49.745362)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_10


# Create new component statorwedge_11
newComp = CreateNamedComponentWithColour_Radial("statorwedge_11", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-57.147355, -52.963236)
plNext = AddPolyLine_Line_XY(plStart, -57.494272, -51.219166)
plNext = AddPolyLine_Line_XY(plNext, -58.285487, -50.316958)
plNext = AddPolyLine_Line_XY(plNext, -59.969355, -49.745362)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_11


# Create new component statorwedge_12
newComp = CreateNamedComponentWithColour_Radial("statorwedge_12", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-51.219166, 57.494272)
plNext = AddPolyLine_Line_XY(plStart, -50.316958, 58.285487)
plNext = AddPolyLine_Line_XY(plNext, -49.745362, 59.969355)
plNext = AddPolyLine_Line_XY(plNext, -52.963236, 57.147355)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_12


# Create new component statorwedge_13
newComp = CreateNamedComponentWithColour_Radial("statorwedge_13", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-49.745362, -59.969355)
plNext = AddPolyLine_Line_XY(plStart, -50.316958, -58.285487)
plNext = AddPolyLine_Line_XY(plNext, -51.219166, -57.494272)
plNext = AddPolyLine_Line_XY(plNext, -52.963236, -57.147355)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_13


# Create new component statorwedge_14
newComp = CreateNamedComponentWithColour_Radial("statorwedge_14", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-43.27647, 63.687844)
plNext = AddPolyLine_Line_XY(plStart, -42.278707, 64.354528)
plNext = AddPolyLine_Line_XY(plNext, -41.492212, 65.949382)
plNext = AddPolyLine_Line_XY(plNext, -45.050902, 63.571541)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_14


# Create new component statorwedge_15
newComp = CreateNamedComponentWithColour_Radial("statorwedge_15", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-41.492212, -65.949382)
plNext = AddPolyLine_Line_XY(plStart, -42.278707, -64.354528)
plNext = AddPolyLine_Line_XY(plNext, -43.27647, -63.687844)
plNext = AddPolyLine_Line_XY(plNext, -45.050902, -63.571541)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_15


# Create new component statorwedge_16
newComp = CreateNamedComponentWithColour_Radial("statorwedge_16", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-34.593302, 68.791698)
plNext = AddPolyLine_Line_XY(plStart, -33.517055, 69.322445)
plNext = AddPolyLine_Line_XY(plNext, -32.529119, 70.800996)
plNext = AddPolyLine_Line_XY(plNext, -36.367734, 68.908)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_16


# Create new component statorwedge_17
newComp = CreateNamedComponentWithColour_Radial("statorwedge_17", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-32.529119, -70.800996)
plNext = AddPolyLine_Line_XY(plStart, -33.517055, -69.322445)
plNext = AddPolyLine_Line_XY(plNext, -34.593302, -68.791698)
plNext = AddPolyLine_Line_XY(plNext, -36.367734, -68.908)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_17


# Create new component statorwedge_18
newComp = CreateNamedComponentWithColour_Radial("statorwedge_18", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-25.318234, 72.718508)
plNext = AddPolyLine_Line_XY(plStart, -24.181917, 73.104235)
plNext = AddPolyLine_Line_XY(plNext, -23.009443, 74.441186)
plNext = AddPolyLine_Line_XY(plNext, -27.062304, 73.065425)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_18


# Create new component statorwedge_19
newComp = CreateNamedComponentWithColour_Radial("statorwedge_19", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-23.009443, -74.441186)
plNext = AddPolyLine_Line_XY(plStart, -24.181917, -73.104235)
plNext = AddPolyLine_Line_XY(plNext, -25.318234, -72.718508)
plNext = AddPolyLine_Line_XY(plNext, -27.062304, -73.065425)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_19


# Create new component statorwedge_20
newComp = CreateNamedComponentWithColour_Radial("statorwedge_20", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-15.609963, 75.401083)
plNext = AddPolyLine_Line_XY(plStart, -14.43302, 75.635192)
plNext = AddPolyLine_Line_XY(plNext, -13.09607, 76.807666)
plNext = AddPolyLine_Line_XY(plNext, -17.293831, 75.972679)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_20


# Create new component statorwedge_21
newComp = CreateNamedComponentWithColour_Radial("statorwedge_21", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-13.09607, -76.807666)
plNext = AddPolyLine_Line_XY(plStart, -14.43302, -75.635192)
plNext = AddPolyLine_Line_XY(plNext, -15.609963, -75.401083)
plNext = AddPolyLine_Line_XY(plNext, -17.293831, -75.972679)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_21


# Create new component statorwedge_22
newComp = CreateNamedComponentWithColour_Radial("statorwedge_22", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-5.634601, 76.793526)
plNext = AddPolyLine_Line_XY(plStart, -4.43717, 76.872009)
plNext = AddPolyLine_Line_XY(plNext, -2.958619, 77.859946)
plNext = AddPolyLine_Line_XY(plNext, -7.229455, 77.580021)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_22


# Create new component statorwedge_23
newComp = CreateNamedComponentWithColour_Radial("statorwedge_23", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-2.958619, -77.859946)
plNext = AddPolyLine_Line_XY(plStart, -4.43717, -76.872009)
plNext = AddPolyLine_Line_XY(plNext, -5.634601, -76.793526)
plNext = AddPolyLine_Line_XY(plNext, -7.229455, -77.580021)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_23


# Create new component statorwedge_24
newComp = CreateNamedComponentWithColour_Radial("statorwedge_24", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(4.43717, 76.872009)
plNext = AddPolyLine_Line_XY(plStart, 5.634601, 76.793526)
plNext = AddPolyLine_Line_XY(plNext, 7.229455, 77.580021)
plNext = AddPolyLine_Line_XY(plNext, 2.958619, 77.859946)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_24


# Create new component statorwedge_25
newComp = CreateNamedComponentWithColour_Radial("statorwedge_25", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(7.229455, -77.580021)
plNext = AddPolyLine_Line_XY(plStart, 5.634601, -76.793526)
plNext = AddPolyLine_Line_XY(plNext, 4.43717, -76.872009)
plNext = AddPolyLine_Line_XY(plNext, 2.958619, -77.859946)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_25


# Create new component statorwedge_26
newComp = CreateNamedComponentWithColour_Radial("statorwedge_26", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(14.43302, 75.635192)
plNext = AddPolyLine_Line_XY(plStart, 15.609963, 75.401083)
plNext = AddPolyLine_Line_XY(plNext, 17.293831, 75.972679)
plNext = AddPolyLine_Line_XY(plNext, 13.09607, 76.807666)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_26


# Create new component statorwedge_27
newComp = CreateNamedComponentWithColour_Radial("statorwedge_27", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(17.293831, -75.972679)
plNext = AddPolyLine_Line_XY(plStart, 15.609963, -75.401083)
plNext = AddPolyLine_Line_XY(plNext, 14.43302, -75.635192)
plNext = AddPolyLine_Line_XY(plNext, 13.09607, -76.807666)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_27


# Create new component statorwedge_28
newComp = CreateNamedComponentWithColour_Radial("statorwedge_28", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(24.181917, 73.104235)
plNext = AddPolyLine_Line_XY(plStart, 25.318234, 72.718508)
plNext = AddPolyLine_Line_XY(plNext, 27.062304, 73.065425)
plNext = AddPolyLine_Line_XY(plNext, 23.009443, 74.441186)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_28


# Create new component statorwedge_29
newComp = CreateNamedComponentWithColour_Radial("statorwedge_29", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(27.062304, -73.065425)
plNext = AddPolyLine_Line_XY(plStart, 25.318234, -72.718508)
plNext = AddPolyLine_Line_XY(plNext, 24.181917, -73.104235)
plNext = AddPolyLine_Line_XY(plNext, 23.009443, -74.441186)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_29


# Create new component statorwedge_30
newComp = CreateNamedComponentWithColour_Radial("statorwedge_30", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(33.517055, 69.322445)
plNext = AddPolyLine_Line_XY(plStart, 34.593302, 68.791698)
plNext = AddPolyLine_Line_XY(plNext, 36.367734, 68.908)
plNext = AddPolyLine_Line_XY(plNext, 32.529119, 70.800996)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_30


# Create new component statorwedge_31
newComp = CreateNamedComponentWithColour_Radial("statorwedge_31", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(36.367734, -68.908)
plNext = AddPolyLine_Line_XY(plStart, 34.593302, -68.791698)
plNext = AddPolyLine_Line_XY(plNext, 33.517055, -69.322445)
plNext = AddPolyLine_Line_XY(plNext, 32.529119, -70.800996)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_31


# Create new component statorwedge_32
newComp = CreateNamedComponentWithColour_Radial("statorwedge_32", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(42.278707, 64.354528)
plNext = AddPolyLine_Line_XY(plStart, 43.27647, 63.687844)
plNext = AddPolyLine_Line_XY(plNext, 45.050902, 63.571541)
plNext = AddPolyLine_Line_XY(plNext, 41.492212, 65.949382)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_32


# Create new component statorwedge_33
newComp = CreateNamedComponentWithColour_Radial("statorwedge_33", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(45.050902, -63.571541)
plNext = AddPolyLine_Line_XY(plStart, 43.27647, -63.687844)
plNext = AddPolyLine_Line_XY(plNext, 42.278707, -64.354528)
plNext = AddPolyLine_Line_XY(plNext, 41.492212, -65.949382)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_33


# Create new component statorwedge_34
newComp = CreateNamedComponentWithColour_Radial("statorwedge_34", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(50.316958, 58.285487)
plNext = AddPolyLine_Line_XY(plStart, 51.219166, 57.494272)
plNext = AddPolyLine_Line_XY(plNext, 52.963236, 57.147355)
plNext = AddPolyLine_Line_XY(plNext, 49.745362, 59.969355)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_34


# Create new component statorwedge_35
newComp = CreateNamedComponentWithColour_Radial("statorwedge_35", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(52.963236, -57.147355)
plNext = AddPolyLine_Line_XY(plStart, 51.219166, -57.494272)
plNext = AddPolyLine_Line_XY(plNext, 50.316958, -58.285487)
plNext = AddPolyLine_Line_XY(plNext, 49.745362, -59.969355)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_35


# Create new component statorwedge_36
newComp = CreateNamedComponentWithColour_Radial("statorwedge_36", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(57.494272, 51.219166)
plNext = AddPolyLine_Line_XY(plStart, 58.285487, 50.316958)
plNext = AddPolyLine_Line_XY(plNext, 59.969355, 49.745362)
plNext = AddPolyLine_Line_XY(plNext, 57.147355, 52.963236)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_36


# Create new component statorwedge_37
newComp = CreateNamedComponentWithColour_Radial("statorwedge_37", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(59.969355, -49.745362)
plNext = AddPolyLine_Line_XY(plStart, 58.285487, -50.316958)
plNext = AddPolyLine_Line_XY(plNext, 57.494272, -51.219166)
plNext = AddPolyLine_Line_XY(plNext, 57.147355, -52.963236)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_37


# Create new component statorwedge_38
newComp = CreateNamedComponentWithColour_Radial("statorwedge_38", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(63.687844, 43.27647)
plNext = AddPolyLine_Line_XY(plStart, 64.354528, 42.278707)
plNext = AddPolyLine_Line_XY(plNext, 65.949382, 41.492212)
plNext = AddPolyLine_Line_XY(plNext, 63.571541, 45.050902)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_38


# Create new component statorwedge_39
newComp = CreateNamedComponentWithColour_Radial("statorwedge_39", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(65.949382, -41.492212)
plNext = AddPolyLine_Line_XY(plStart, 64.354528, -42.278707)
plNext = AddPolyLine_Line_XY(plNext, 63.687844, -43.27647)
plNext = AddPolyLine_Line_XY(plNext, 63.571541, -45.050902)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_39


# Create new component statorwedge_40
newComp = CreateNamedComponentWithColour_Radial("statorwedge_40", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(69.322445, -33.517055)
plNext = AddPolyLine_Line_XY(plStart, 68.791698, -34.593302)
plNext = AddPolyLine_Line_XY(plNext, 68.908, -36.367734)
plNext = AddPolyLine_Line_XY(plNext, 70.800996, -32.529119)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_40


# Create new component statorwedge_41
newComp = CreateNamedComponentWithColour_Radial("statorwedge_41", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(69.322445, 33.517055)
plNext = AddPolyLine_Line_XY(plStart, 70.800996, 32.529119)
plNext = AddPolyLine_Line_XY(plNext, 68.908, 36.367734)
plNext = AddPolyLine_Line_XY(plNext, 68.791698, 34.593302)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_41


# Create new component statorwedge_42
newComp = CreateNamedComponentWithColour_Radial("statorwedge_42", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(73.104235, -24.181917)
plNext = AddPolyLine_Line_XY(plStart, 72.718508, -25.318234)
plNext = AddPolyLine_Line_XY(plNext, 73.065425, -27.062304)
plNext = AddPolyLine_Line_XY(plNext, 74.441186, -23.009443)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_42


# Create new component statorwedge_43
newComp = CreateNamedComponentWithColour_Radial("statorwedge_43", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(73.104235, 24.181917)
plNext = AddPolyLine_Line_XY(plStart, 74.441186, 23.009443)
plNext = AddPolyLine_Line_XY(plNext, 73.065425, 27.062304)
plNext = AddPolyLine_Line_XY(plNext, 72.718508, 25.318234)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_43


# Create new component statorwedge_44
newComp = CreateNamedComponentWithColour_Radial("statorwedge_44", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(75.635192, -14.43302)
plNext = AddPolyLine_Line_XY(plStart, 75.401083, -15.609963)
plNext = AddPolyLine_Line_XY(plNext, 75.972679, -17.293831)
plNext = AddPolyLine_Line_XY(plNext, 76.807666, -13.09607)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_44


# Create new component statorwedge_45
newComp = CreateNamedComponentWithColour_Radial("statorwedge_45", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(75.635192, 14.43302)
plNext = AddPolyLine_Line_XY(plStart, 76.807666, 13.09607)
plNext = AddPolyLine_Line_XY(plNext, 75.972679, 17.293831)
plNext = AddPolyLine_Line_XY(plNext, 75.401083, 15.609963)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_45


# Create new component statorwedge_46
newComp = CreateNamedComponentWithColour_Radial("statorwedge_46", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(77.580021, 7.229455)
plNext = AddPolyLine_Line_XY(plStart, 76.793526, 5.634601)
plNext = AddPolyLine_Line_XY(plNext, 76.872009, 4.43717)
plNext = AddPolyLine_Line_XY(plNext, 77.859946, 2.958619)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_46


# Create new component statorwedge_47
newComp = CreateNamedComponentWithColour_Radial("statorwedge_47", -54.5, -96, 207, 223, 223, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(76.872009, -4.43717)
plNext = AddPolyLine_Line_XY(plStart, 76.793526, -5.634601)
plNext = AddPolyLine_Line_XY(plNext, 77.580021, -7.229455)
plNext = AddPolyLine_Line_XY(plNext, 77.859946, -2.958619)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component statorwedge_47


# Create new component armature_winding_active_g48
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g48", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(79.632727, 13.658009)
plNext = AddPolyLine_Line_XY(plStart, 82.457787, 14.219949)
plNext = AddPolyLine_Line_XY(plNext, 81.622801, 18.41771)
plNext = AddPolyLine_Line_XY(plNext, 78.79774, 17.85577)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g48


# Create new component armature_winding_active_g47
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g47", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(77.16873, 23.93532)
plNext = AddPolyLine_Line_XY(plStart, 79.896274, 24.861196)
plNext = AddPolyLine_Line_XY(plNext, 78.520513, 28.914057)
plNext = AddPolyLine_Line_XY(plNext, 75.792969, 27.988181)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g47


# Create new component armature_winding_active_g46
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g46", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(73.384354, 33.80309)
plNext = AddPolyLine_Line_XY(plStart, 75.967713, 35.077061)
plNext = AddPolyLine_Line_XY(plNext, 74.074717, 38.915677)
plNext = AddPolyLine_Line_XY(plNext, 71.491359, 37.641705)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g46


# Create new component armature_winding_active_g45
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g45", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(68.344353, 43.09248)
plNext = AddPolyLine_Line_XY(plStart, 70.739323, 44.692749)
plNext = AddPolyLine_Line_XY(plNext, 68.361483, 48.251439)
plNext = AddPolyLine_Line_XY(plNext, 65.966512, 46.65117)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g45


# Create new component armature_winding_active_g44
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g44", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(62.13496, 51.644546)
plNext = AddPolyLine_Line_XY(plStart, 64.300564, 53.54373)
plNext = AddPolyLine_Line_XY(plNext, 61.478564, 56.761605)
plNext = AddPolyLine_Line_XY(plNext, 59.31296, 54.862421)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g44


# Create new component armature_winding_active_g43
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g43", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(54.862421, 59.31296)
plNext = AddPolyLine_Line_XY(plStart, 56.761605, 61.478564)
plNext = AddPolyLine_Line_XY(plNext, 53.54373, 64.300564)
plNext = AddPolyLine_Line_XY(plNext, 51.644546, 62.13496)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g43


# Create new component armature_winding_active_g42
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g42", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(46.65117, 65.966512)
plNext = AddPolyLine_Line_XY(plStart, 48.251439, 68.361483)
plNext = AddPolyLine_Line_XY(plNext, 44.692749, 70.739323)
plNext = AddPolyLine_Line_XY(plNext, 43.09248, 68.344353)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g42


# Create new component armature_winding_active_g41
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g41", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(37.641705, 71.491359)
plNext = AddPolyLine_Line_XY(plStart, 38.915677, 74.074717)
plNext = AddPolyLine_Line_XY(plNext, 35.077061, 75.967713)
plNext = AddPolyLine_Line_XY(plNext, 33.80309, 73.384354)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g41


# Create new component armature_winding_active_g40
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g40", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(27.988181, 75.792969)
plNext = AddPolyLine_Line_XY(plStart, 28.914057, 78.520513)
plNext = AddPolyLine_Line_XY(plNext, 24.861196, 79.896274)
plNext = AddPolyLine_Line_XY(plNext, 23.93532, 77.16873)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g40


# Create new component armature_winding_active_g39
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g39", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(17.85577, 78.79774)
plNext = AddPolyLine_Line_XY(plStart, 18.41771, 81.622801)
plNext = AddPolyLine_Line_XY(plNext, 14.219949, 82.457787)
plNext = AddPolyLine_Line_XY(plNext, 13.658009, 79.632727)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g39


# Create new component armature_winding_active_g38
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g38", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(7.417843, 80.45426)
plNext = AddPolyLine_Line_XY(plStart, 7.60623, 83.3285)
plNext = AddPolyLine_Line_XY(plNext, 3.335394, 83.608425)
plNext = AddPolyLine_Line_XY(plNext, 3.147006, 80.734186)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g38


# Create new component armature_winding_active_g37
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g37", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-3.147006, 80.734186)
plNext = AddPolyLine_Line_XY(plStart, -3.335394, 83.608425)
plNext = AddPolyLine_Line_XY(plNext, -7.60623, 83.3285)
plNext = AddPolyLine_Line_XY(plNext, -7.417843, 80.45426)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g37


# Create new component armature_winding_active_g36
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g36", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-13.658009, 79.632727)
plNext = AddPolyLine_Line_XY(plStart, -14.219949, 82.457787)
plNext = AddPolyLine_Line_XY(plNext, -18.41771, 81.622801)
plNext = AddPolyLine_Line_XY(plNext, -17.85577, 78.79774)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g36


# Create new component armature_winding_active_g35
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g35", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-23.93532, 77.16873)
plNext = AddPolyLine_Line_XY(plStart, -24.861196, 79.896274)
plNext = AddPolyLine_Line_XY(plNext, -28.914057, 78.520513)
plNext = AddPolyLine_Line_XY(plNext, -27.988181, 75.792969)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g35


# Create new component armature_winding_active_g34
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g34", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-33.80309, 73.384354)
plNext = AddPolyLine_Line_XY(plStart, -35.077061, 75.967713)
plNext = AddPolyLine_Line_XY(plNext, -38.915677, 74.074717)
plNext = AddPolyLine_Line_XY(plNext, -37.641705, 71.491359)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g34


# Create new component armature_winding_active_g33
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g33", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-43.09248, 68.344353)
plNext = AddPolyLine_Line_XY(plStart, -44.692749, 70.739323)
plNext = AddPolyLine_Line_XY(plNext, -48.251439, 68.361483)
plNext = AddPolyLine_Line_XY(plNext, -46.65117, 65.966512)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g33


# Create new component armature_winding_active_g32
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g32", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-51.644546, 62.13496)
plNext = AddPolyLine_Line_XY(plStart, -53.54373, 64.300564)
plNext = AddPolyLine_Line_XY(plNext, -56.761605, 61.478564)
plNext = AddPolyLine_Line_XY(plNext, -54.862421, 59.31296)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g32


# Create new component armature_winding_active_g31
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g31", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-59.31296, 54.862421)
plNext = AddPolyLine_Line_XY(plStart, -61.478564, 56.761605)
plNext = AddPolyLine_Line_XY(plNext, -64.300564, 53.54373)
plNext = AddPolyLine_Line_XY(plNext, -62.13496, 51.644546)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g31


# Create new component armature_winding_active_g30
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g30", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-65.966512, 46.65117)
plNext = AddPolyLine_Line_XY(plStart, -68.361483, 48.251439)
plNext = AddPolyLine_Line_XY(plNext, -70.739323, 44.692749)
plNext = AddPolyLine_Line_XY(plNext, -68.344353, 43.09248)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g30


# Create new component armature_winding_active_g29
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g29", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-71.491359, 37.641705)
plNext = AddPolyLine_Line_XY(plStart, -74.074717, 38.915677)
plNext = AddPolyLine_Line_XY(plNext, -75.967713, 35.077061)
plNext = AddPolyLine_Line_XY(plNext, -73.384354, 33.80309)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g29


# Create new component armature_winding_active_g28
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g28", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-75.792969, 27.988181)
plNext = AddPolyLine_Line_XY(plStart, -78.520513, 28.914057)
plNext = AddPolyLine_Line_XY(plNext, -79.896274, 24.861196)
plNext = AddPolyLine_Line_XY(plNext, -77.16873, 23.93532)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g28


# Create new component armature_winding_active_g27
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g27", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-78.79774, 17.85577)
plNext = AddPolyLine_Line_XY(plStart, -81.622801, 18.41771)
plNext = AddPolyLine_Line_XY(plNext, -82.457787, 14.219949)
plNext = AddPolyLine_Line_XY(plNext, -79.632727, 13.658009)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g27


# Create new component armature_winding_active_g26
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g26", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-80.45426, 7.417843)
plNext = AddPolyLine_Line_XY(plStart, -83.3285, 7.60623)
plNext = AddPolyLine_Line_XY(plNext, -83.608425, 3.335394)
plNext = AddPolyLine_Line_XY(plNext, -80.734186, 3.147006)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g26


# Create new component armature_winding_active_g25
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g25", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-80.734186, -3.147006)
plNext = AddPolyLine_Line_XY(plStart, -83.608425, -3.335394)
plNext = AddPolyLine_Line_XY(plNext, -83.3285, -7.60623)
plNext = AddPolyLine_Line_XY(plNext, -80.45426, -7.417843)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g25


# Create new component armature_winding_active_g24
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g24", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-79.632727, -13.658009)
plNext = AddPolyLine_Line_XY(plStart, -82.457787, -14.219949)
plNext = AddPolyLine_Line_XY(plNext, -81.622801, -18.41771)
plNext = AddPolyLine_Line_XY(plNext, -78.79774, -17.85577)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g24


# Create new component armature_winding_active_g23
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g23", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-77.16873, -23.93532)
plNext = AddPolyLine_Line_XY(plStart, -79.896274, -24.861196)
plNext = AddPolyLine_Line_XY(plNext, -78.520513, -28.914057)
plNext = AddPolyLine_Line_XY(plNext, -75.792969, -27.988181)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g23


# Create new component armature_winding_active_g22
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g22", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-73.384354, -33.80309)
plNext = AddPolyLine_Line_XY(plStart, -75.967713, -35.077061)
plNext = AddPolyLine_Line_XY(plNext, -74.074717, -38.915677)
plNext = AddPolyLine_Line_XY(plNext, -71.491359, -37.641705)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g22


# Create new component armature_winding_active_g21
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g21", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-68.344353, -43.09248)
plNext = AddPolyLine_Line_XY(plStart, -70.739323, -44.692749)
plNext = AddPolyLine_Line_XY(plNext, -68.361483, -48.251439)
plNext = AddPolyLine_Line_XY(plNext, -65.966512, -46.65117)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g21


# Create new component armature_winding_active_g20
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g20", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-62.13496, -51.644546)
plNext = AddPolyLine_Line_XY(plStart, -64.300564, -53.54373)
plNext = AddPolyLine_Line_XY(plNext, -61.478564, -56.761605)
plNext = AddPolyLine_Line_XY(plNext, -59.31296, -54.862421)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g20


# Create new component armature_winding_active_g19
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g19", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-54.862421, -59.31296)
plNext = AddPolyLine_Line_XY(plStart, -56.761605, -61.478564)
plNext = AddPolyLine_Line_XY(plNext, -53.54373, -64.300564)
plNext = AddPolyLine_Line_XY(plNext, -51.644546, -62.13496)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g19


# Create new component armature_winding_active_g18
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g18", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-46.65117, -65.966512)
plNext = AddPolyLine_Line_XY(plStart, -48.251439, -68.361483)
plNext = AddPolyLine_Line_XY(plNext, -44.692749, -70.739323)
plNext = AddPolyLine_Line_XY(plNext, -43.09248, -68.344353)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g18


# Create new component armature_winding_active_g17
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g17", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-37.641705, -71.491359)
plNext = AddPolyLine_Line_XY(plStart, -38.915677, -74.074717)
plNext = AddPolyLine_Line_XY(plNext, -35.077061, -75.967713)
plNext = AddPolyLine_Line_XY(plNext, -33.80309, -73.384354)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g17


# Create new component armature_winding_active_g16
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g16", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-27.988181, -75.792969)
plNext = AddPolyLine_Line_XY(plStart, -28.914057, -78.520513)
plNext = AddPolyLine_Line_XY(plNext, -24.861196, -79.896274)
plNext = AddPolyLine_Line_XY(plNext, -23.93532, -77.16873)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g16


# Create new component armature_winding_active_g15
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g15", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-17.85577, -78.79774)
plNext = AddPolyLine_Line_XY(plStart, -18.41771, -81.622801)
plNext = AddPolyLine_Line_XY(plNext, -14.219949, -82.457787)
plNext = AddPolyLine_Line_XY(plNext, -13.658009, -79.632727)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g15


# Create new component armature_winding_active_g14
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g14", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-7.417843, -80.45426)
plNext = AddPolyLine_Line_XY(plStart, -7.60623, -83.3285)
plNext = AddPolyLine_Line_XY(plNext, -3.335394, -83.608425)
plNext = AddPolyLine_Line_XY(plNext, -3.147006, -80.734186)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g14


# Create new component armature_winding_active_g13
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g13", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(3.147006, -80.734186)
plNext = AddPolyLine_Line_XY(plStart, 3.335394, -83.608425)
plNext = AddPolyLine_Line_XY(plNext, 7.60623, -83.3285)
plNext = AddPolyLine_Line_XY(plNext, 7.417843, -80.45426)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g13


# Create new component armature_winding_active_g12
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g12", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(13.658009, -79.632727)
plNext = AddPolyLine_Line_XY(plStart, 14.219949, -82.457787)
plNext = AddPolyLine_Line_XY(plNext, 18.41771, -81.622801)
plNext = AddPolyLine_Line_XY(plNext, 17.85577, -78.79774)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g12


# Create new component armature_winding_active_g11
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g11", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(23.93532, -77.16873)
plNext = AddPolyLine_Line_XY(plStart, 24.861196, -79.896274)
plNext = AddPolyLine_Line_XY(plNext, 28.914057, -78.520513)
plNext = AddPolyLine_Line_XY(plNext, 27.988181, -75.792969)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g11


# Create new component armature_winding_active_g10
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g10", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(33.80309, -73.384354)
plNext = AddPolyLine_Line_XY(plStart, 35.077061, -75.967713)
plNext = AddPolyLine_Line_XY(plNext, 38.915677, -74.074717)
plNext = AddPolyLine_Line_XY(plNext, 37.641705, -71.491359)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g10


# Create new component armature_winding_active_g9
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g9", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(43.09248, -68.344353)
plNext = AddPolyLine_Line_XY(plStart, 44.692749, -70.739323)
plNext = AddPolyLine_Line_XY(plNext, 48.251439, -68.361483)
plNext = AddPolyLine_Line_XY(plNext, 46.65117, -65.966512)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g9


# Create new component armature_winding_active_g8
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g8", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(51.644546, -62.13496)
plNext = AddPolyLine_Line_XY(plStart, 53.54373, -64.300564)
plNext = AddPolyLine_Line_XY(plNext, 56.761605, -61.478564)
plNext = AddPolyLine_Line_XY(plNext, 54.862421, -59.31296)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g8


# Create new component armature_winding_active_g7
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g7", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(59.31296, -54.862421)
plNext = AddPolyLine_Line_XY(plStart, 61.478564, -56.761605)
plNext = AddPolyLine_Line_XY(plNext, 64.300564, -53.54373)
plNext = AddPolyLine_Line_XY(plNext, 62.13496, -51.644546)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g7


# Create new component armature_winding_active_g6
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g6", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(65.966512, -46.65117)
plNext = AddPolyLine_Line_XY(plStart, 68.361483, -48.251439)
plNext = AddPolyLine_Line_XY(plNext, 70.739323, -44.692749)
plNext = AddPolyLine_Line_XY(plNext, 68.344353, -43.09248)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g6


# Create new component armature_winding_active_g5
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g5", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(71.491359, -37.641705)
plNext = AddPolyLine_Line_XY(plStart, 74.074717, -38.915677)
plNext = AddPolyLine_Line_XY(plNext, 75.967713, -35.077061)
plNext = AddPolyLine_Line_XY(plNext, 73.384354, -33.80309)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g5


# Create new component armature_winding_active_g4
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g4", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(75.792969, -27.988181)
plNext = AddPolyLine_Line_XY(plStart, 78.520513, -28.914057)
plNext = AddPolyLine_Line_XY(plNext, 79.896274, -24.861196)
plNext = AddPolyLine_Line_XY(plNext, 77.16873, -23.93532)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g4


# Create new component armature_winding_active_g3
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g3", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(78.79774, -17.85577)
plNext = AddPolyLine_Line_XY(plStart, 81.622801, -18.41771)
plNext = AddPolyLine_Line_XY(plNext, 82.457787, -14.219949)
plNext = AddPolyLine_Line_XY(plNext, 79.632727, -13.658009)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g3


# Create new component armature_winding_active_g2
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_g2", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(80.45426, -7.417843)
plNext = AddPolyLine_Line_XY(plStart, 83.3285, -7.60623)
plNext = AddPolyLine_Line_XY(plNext, 83.608425, -3.335394)
plNext = AddPolyLine_Line_XY(plNext, 80.734186, -3.147006)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_g2


# Create new component armature_winding_active_f48
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f48", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(82.457787, 14.219949)
plNext = AddPolyLine_Line_XY(plStart, 85.282848, 14.781888)
plNext = AddPolyLine_Line_XY(plNext, 84.447862, 18.979649)
plNext = AddPolyLine_Line_XY(plNext, 81.622801, 18.41771)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f48


# Create new component armature_winding_active_f47
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f47", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(79.896274, 24.861196)
plNext = AddPolyLine_Line_XY(plStart, 82.623818, 25.787072)
plNext = AddPolyLine_Line_XY(plNext, 81.248057, 29.839933)
plNext = AddPolyLine_Line_XY(plNext, 78.520513, 28.914057)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f47


# Create new component armature_winding_active_f46
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f46", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(75.967713, 35.077061)
plNext = AddPolyLine_Line_XY(plStart, 78.551071, 36.351033)
plNext = AddPolyLine_Line_XY(plNext, 76.658076, 40.189648)
plNext = AddPolyLine_Line_XY(plNext, 74.074717, 38.915677)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f46


# Create new component armature_winding_active_f45
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f45", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(70.739323, 44.692749)
plNext = AddPolyLine_Line_XY(plStart, 73.134294, 46.293017)
plNext = AddPolyLine_Line_XY(plNext, 70.756454, 49.851707)
plNext = AddPolyLine_Line_XY(plNext, 68.361483, 48.251439)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f45


# Create new component armature_winding_active_f44
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f44", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(64.300564, 53.54373)
plNext = AddPolyLine_Line_XY(plStart, 66.466169, 55.442915)
plNext = AddPolyLine_Line_XY(plNext, 63.644169, 58.660789)
plNext = AddPolyLine_Line_XY(plNext, 61.478564, 56.761605)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f44


# Create new component armature_winding_active_f43
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f43", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(56.761605, 61.478564)
plNext = AddPolyLine_Line_XY(plStart, 58.660789, 63.644169)
plNext = AddPolyLine_Line_XY(plNext, 55.442915, 66.466169)
plNext = AddPolyLine_Line_XY(plNext, 53.54373, 64.300564)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f43


# Create new component armature_winding_active_f42
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f42", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(48.251439, 68.361483)
plNext = AddPolyLine_Line_XY(plStart, 49.851707, 70.756454)
plNext = AddPolyLine_Line_XY(plNext, 46.293017, 73.134294)
plNext = AddPolyLine_Line_XY(plNext, 44.692749, 70.739323)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f42


# Create new component armature_winding_active_f41
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f41", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(38.915677, 74.074717)
plNext = AddPolyLine_Line_XY(plStart, 40.189648, 76.658076)
plNext = AddPolyLine_Line_XY(plNext, 36.351033, 78.551071)
plNext = AddPolyLine_Line_XY(plNext, 35.077061, 75.967713)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f41


# Create new component armature_winding_active_f40
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f40", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(28.914057, 78.520513)
plNext = AddPolyLine_Line_XY(plStart, 29.839933, 81.248057)
plNext = AddPolyLine_Line_XY(plNext, 25.787072, 82.623818)
plNext = AddPolyLine_Line_XY(plNext, 24.861196, 79.896274)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f40


# Create new component armature_winding_active_f39
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f39", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(18.41771, 81.622801)
plNext = AddPolyLine_Line_XY(plStart, 18.979649, 84.447862)
plNext = AddPolyLine_Line_XY(plNext, 14.781888, 85.282848)
plNext = AddPolyLine_Line_XY(plNext, 14.219949, 82.457787)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f39


# Create new component armature_winding_active_f38
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f38", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(7.60623, 83.3285)
plNext = AddPolyLine_Line_XY(plStart, 7.794618, 86.20274)
plNext = AddPolyLine_Line_XY(plNext, 3.523782, 86.482665)
plNext = AddPolyLine_Line_XY(plNext, 3.335394, 83.608425)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f38


# Create new component armature_winding_active_f37
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f37", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-3.335394, 83.608425)
plNext = AddPolyLine_Line_XY(plStart, -3.523782, 86.482665)
plNext = AddPolyLine_Line_XY(plNext, -7.794618, 86.20274)
plNext = AddPolyLine_Line_XY(plNext, -7.60623, 83.3285)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f37


# Create new component armature_winding_active_f36
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f36", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-14.219949, 82.457787)
plNext = AddPolyLine_Line_XY(plStart, -14.781888, 85.282848)
plNext = AddPolyLine_Line_XY(plNext, -18.979649, 84.447862)
plNext = AddPolyLine_Line_XY(plNext, -18.41771, 81.622801)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f36


# Create new component armature_winding_active_f35
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f35", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-24.861196, 79.896274)
plNext = AddPolyLine_Line_XY(plStart, -25.787072, 82.623818)
plNext = AddPolyLine_Line_XY(plNext, -29.839933, 81.248057)
plNext = AddPolyLine_Line_XY(plNext, -28.914057, 78.520513)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f35


# Create new component armature_winding_active_f34
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f34", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-35.077061, 75.967713)
plNext = AddPolyLine_Line_XY(plStart, -36.351033, 78.551071)
plNext = AddPolyLine_Line_XY(plNext, -40.189648, 76.658076)
plNext = AddPolyLine_Line_XY(plNext, -38.915677, 74.074717)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f34


# Create new component armature_winding_active_f33
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f33", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-44.692749, 70.739323)
plNext = AddPolyLine_Line_XY(plStart, -46.293017, 73.134294)
plNext = AddPolyLine_Line_XY(plNext, -49.851707, 70.756454)
plNext = AddPolyLine_Line_XY(plNext, -48.251439, 68.361483)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f33


# Create new component armature_winding_active_f32
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f32", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-53.54373, 64.300564)
plNext = AddPolyLine_Line_XY(plStart, -55.442915, 66.466169)
plNext = AddPolyLine_Line_XY(plNext, -58.660789, 63.644169)
plNext = AddPolyLine_Line_XY(plNext, -56.761605, 61.478564)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f32


# Create new component armature_winding_active_f31
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f31", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-61.478564, 56.761605)
plNext = AddPolyLine_Line_XY(plStart, -63.644169, 58.660789)
plNext = AddPolyLine_Line_XY(plNext, -66.466169, 55.442915)
plNext = AddPolyLine_Line_XY(plNext, -64.300564, 53.54373)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f31


# Create new component armature_winding_active_f30
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f30", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-68.361483, 48.251439)
plNext = AddPolyLine_Line_XY(plStart, -70.756454, 49.851707)
plNext = AddPolyLine_Line_XY(plNext, -73.134294, 46.293017)
plNext = AddPolyLine_Line_XY(plNext, -70.739323, 44.692749)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f30


# Create new component armature_winding_active_f29
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f29", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-74.074717, 38.915677)
plNext = AddPolyLine_Line_XY(plStart, -76.658076, 40.189648)
plNext = AddPolyLine_Line_XY(plNext, -78.551071, 36.351033)
plNext = AddPolyLine_Line_XY(plNext, -75.967713, 35.077061)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f29


# Create new component armature_winding_active_f28
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f28", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-78.520513, 28.914057)
plNext = AddPolyLine_Line_XY(plStart, -81.248057, 29.839933)
plNext = AddPolyLine_Line_XY(plNext, -82.623818, 25.787072)
plNext = AddPolyLine_Line_XY(plNext, -79.896274, 24.861196)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f28


# Create new component armature_winding_active_f27
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f27", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-81.622801, 18.41771)
plNext = AddPolyLine_Line_XY(plStart, -84.447862, 18.979649)
plNext = AddPolyLine_Line_XY(plNext, -85.282848, 14.781888)
plNext = AddPolyLine_Line_XY(plNext, -82.457787, 14.219949)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f27


# Create new component armature_winding_active_f26
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f26", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-83.3285, 7.60623)
plNext = AddPolyLine_Line_XY(plStart, -86.20274, 7.794618)
plNext = AddPolyLine_Line_XY(plNext, -86.482665, 3.523782)
plNext = AddPolyLine_Line_XY(plNext, -83.608425, 3.335394)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f26


# Create new component armature_winding_active_f25
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f25", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-83.608425, -3.335394)
plNext = AddPolyLine_Line_XY(plStart, -86.482665, -3.523782)
plNext = AddPolyLine_Line_XY(plNext, -86.20274, -7.794618)
plNext = AddPolyLine_Line_XY(plNext, -83.3285, -7.60623)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f25


# Create new component armature_winding_active_f24
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f24", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-82.457787, -14.219949)
plNext = AddPolyLine_Line_XY(plStart, -85.282848, -14.781888)
plNext = AddPolyLine_Line_XY(plNext, -84.447862, -18.979649)
plNext = AddPolyLine_Line_XY(plNext, -81.622801, -18.41771)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f24


# Create new component armature_winding_active_f23
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f23", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-79.896274, -24.861196)
plNext = AddPolyLine_Line_XY(plStart, -82.623818, -25.787072)
plNext = AddPolyLine_Line_XY(plNext, -81.248057, -29.839933)
plNext = AddPolyLine_Line_XY(plNext, -78.520513, -28.914057)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f23


# Create new component armature_winding_active_f22
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f22", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-75.967713, -35.077061)
plNext = AddPolyLine_Line_XY(plStart, -78.551071, -36.351033)
plNext = AddPolyLine_Line_XY(plNext, -76.658076, -40.189648)
plNext = AddPolyLine_Line_XY(plNext, -74.074717, -38.915677)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f22


# Create new component armature_winding_active_f21
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f21", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-70.739323, -44.692749)
plNext = AddPolyLine_Line_XY(plStart, -73.134294, -46.293017)
plNext = AddPolyLine_Line_XY(plNext, -70.756454, -49.851707)
plNext = AddPolyLine_Line_XY(plNext, -68.361483, -48.251439)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f21


# Create new component armature_winding_active_f20
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f20", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-64.300564, -53.54373)
plNext = AddPolyLine_Line_XY(plStart, -66.466169, -55.442915)
plNext = AddPolyLine_Line_XY(plNext, -63.644169, -58.660789)
plNext = AddPolyLine_Line_XY(plNext, -61.478564, -56.761605)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f20


# Create new component armature_winding_active_f19
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f19", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-56.761605, -61.478564)
plNext = AddPolyLine_Line_XY(plStart, -58.660789, -63.644169)
plNext = AddPolyLine_Line_XY(plNext, -55.442915, -66.466169)
plNext = AddPolyLine_Line_XY(plNext, -53.54373, -64.300564)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f19


# Create new component armature_winding_active_f18
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f18", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-48.251439, -68.361483)
plNext = AddPolyLine_Line_XY(plStart, -49.851707, -70.756454)
plNext = AddPolyLine_Line_XY(plNext, -46.293017, -73.134294)
plNext = AddPolyLine_Line_XY(plNext, -44.692749, -70.739323)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f18


# Create new component armature_winding_active_f17
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f17", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-38.915677, -74.074717)
plNext = AddPolyLine_Line_XY(plStart, -40.189648, -76.658076)
plNext = AddPolyLine_Line_XY(plNext, -36.351033, -78.551071)
plNext = AddPolyLine_Line_XY(plNext, -35.077061, -75.967713)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f17


# Create new component armature_winding_active_f16
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f16", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-28.914057, -78.520513)
plNext = AddPolyLine_Line_XY(plStart, -29.839933, -81.248057)
plNext = AddPolyLine_Line_XY(plNext, -25.787072, -82.623818)
plNext = AddPolyLine_Line_XY(plNext, -24.861196, -79.896274)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f16


# Create new component armature_winding_active_f15
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f15", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-18.41771, -81.622801)
plNext = AddPolyLine_Line_XY(plStart, -18.979649, -84.447862)
plNext = AddPolyLine_Line_XY(plNext, -14.781888, -85.282848)
plNext = AddPolyLine_Line_XY(plNext, -14.219949, -82.457787)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f15


# Create new component armature_winding_active_f14
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f14", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-7.60623, -83.3285)
plNext = AddPolyLine_Line_XY(plStart, -7.794618, -86.20274)
plNext = AddPolyLine_Line_XY(plNext, -3.523782, -86.482665)
plNext = AddPolyLine_Line_XY(plNext, -3.335394, -83.608425)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f14


# Create new component armature_winding_active_f13
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f13", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(3.335394, -83.608425)
plNext = AddPolyLine_Line_XY(plStart, 3.523782, -86.482665)
plNext = AddPolyLine_Line_XY(plNext, 7.794618, -86.20274)
plNext = AddPolyLine_Line_XY(plNext, 7.60623, -83.3285)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f13


# Create new component armature_winding_active_f12
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f12", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(14.219949, -82.457787)
plNext = AddPolyLine_Line_XY(plStart, 14.781888, -85.282848)
plNext = AddPolyLine_Line_XY(plNext, 18.979649, -84.447862)
plNext = AddPolyLine_Line_XY(plNext, 18.41771, -81.622801)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f12


# Create new component armature_winding_active_f11
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f11", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(24.861196, -79.896274)
plNext = AddPolyLine_Line_XY(plStart, 25.787072, -82.623818)
plNext = AddPolyLine_Line_XY(plNext, 29.839933, -81.248057)
plNext = AddPolyLine_Line_XY(plNext, 28.914057, -78.520513)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f11


# Create new component armature_winding_active_f10
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f10", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(35.077061, -75.967713)
plNext = AddPolyLine_Line_XY(plStart, 36.351033, -78.551071)
plNext = AddPolyLine_Line_XY(plNext, 40.189648, -76.658076)
plNext = AddPolyLine_Line_XY(plNext, 38.915677, -74.074717)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f10


# Create new component armature_winding_active_f9
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f9", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(44.692749, -70.739323)
plNext = AddPolyLine_Line_XY(plStart, 46.293017, -73.134294)
plNext = AddPolyLine_Line_XY(plNext, 49.851707, -70.756454)
plNext = AddPolyLine_Line_XY(plNext, 48.251439, -68.361483)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f9


# Create new component armature_winding_active_f8
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f8", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(53.54373, -64.300564)
plNext = AddPolyLine_Line_XY(plStart, 55.442915, -66.466169)
plNext = AddPolyLine_Line_XY(plNext, 58.660789, -63.644169)
plNext = AddPolyLine_Line_XY(plNext, 56.761605, -61.478564)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f8


# Create new component armature_winding_active_f7
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f7", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(61.478564, -56.761605)
plNext = AddPolyLine_Line_XY(plStart, 63.644169, -58.660789)
plNext = AddPolyLine_Line_XY(plNext, 66.466169, -55.442915)
plNext = AddPolyLine_Line_XY(plNext, 64.300564, -53.54373)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f7


# Create new component armature_winding_active_f6
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f6", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(68.361483, -48.251439)
plNext = AddPolyLine_Line_XY(plStart, 70.756454, -49.851707)
plNext = AddPolyLine_Line_XY(plNext, 73.134294, -46.293017)
plNext = AddPolyLine_Line_XY(plNext, 70.739323, -44.692749)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f6


# Create new component armature_winding_active_f5
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f5", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(74.074717, -38.915677)
plNext = AddPolyLine_Line_XY(plStart, 76.658076, -40.189648)
plNext = AddPolyLine_Line_XY(plNext, 78.551071, -36.351033)
plNext = AddPolyLine_Line_XY(plNext, 75.967713, -35.077061)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f5


# Create new component armature_winding_active_f4
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f4", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(78.520513, -28.914057)
plNext = AddPolyLine_Line_XY(plStart, 81.248057, -29.839933)
plNext = AddPolyLine_Line_XY(plNext, 82.623818, -25.787072)
plNext = AddPolyLine_Line_XY(plNext, 79.896274, -24.861196)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f4


# Create new component armature_winding_active_f3
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f3", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(81.622801, -18.41771)
plNext = AddPolyLine_Line_XY(plStart, 84.447862, -18.979649)
plNext = AddPolyLine_Line_XY(plNext, 85.282848, -14.781888)
plNext = AddPolyLine_Line_XY(plNext, 82.457787, -14.219949)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f3


# Create new component armature_winding_active_f2
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_f2", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(83.3285, -7.60623)
plNext = AddPolyLine_Line_XY(plStart, 86.20274, -7.794618)
plNext = AddPolyLine_Line_XY(plNext, 86.482665, -3.523782)
plNext = AddPolyLine_Line_XY(plNext, 83.608425, -3.335394)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_f2


# Create new component armature_winding_active_e48
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e48", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(85.282848, 14.781888)
plNext = AddPolyLine_Line_XY(plStart, 88.107909, 15.343828)
plNext = AddPolyLine_Line_XY(plNext, 87.272922, 19.541589)
plNext = AddPolyLine_Line_XY(plNext, 84.447862, 18.979649)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e48


# Create new component armature_winding_active_e47
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e47", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(82.623818, 25.787072)
plNext = AddPolyLine_Line_XY(plStart, 85.351362, 26.712949)
plNext = AddPolyLine_Line_XY(plNext, 83.975601, 30.76581)
plNext = AddPolyLine_Line_XY(plNext, 81.248057, 29.839933)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e47


# Create new component armature_winding_active_e46
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e46", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(78.551071, 36.351033)
plNext = AddPolyLine_Line_XY(plStart, 81.13443, 37.625004)
plNext = AddPolyLine_Line_XY(plNext, 79.241434, 41.46362)
plNext = AddPolyLine_Line_XY(plNext, 76.658076, 40.189648)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e46


# Create new component armature_winding_active_e45
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e45", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(73.134294, 46.293017)
plNext = AddPolyLine_Line_XY(plStart, 75.529265, 47.893285)
plNext = AddPolyLine_Line_XY(plNext, 73.151424, 51.451975)
plNext = AddPolyLine_Line_XY(plNext, 70.756454, 49.851707)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e45


# Create new component armature_winding_active_e44
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e44", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(66.466169, 55.442915)
plNext = AddPolyLine_Line_XY(plStart, 68.631774, 57.342099)
plNext = AddPolyLine_Line_XY(plNext, 65.809773, 60.559973)
plNext = AddPolyLine_Line_XY(plNext, 63.644169, 58.660789)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e44


# Create new component armature_winding_active_e43
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e43", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(58.660789, 63.644169)
plNext = AddPolyLine_Line_XY(plStart, 60.559973, 65.809773)
plNext = AddPolyLine_Line_XY(plNext, 57.342099, 68.631774)
plNext = AddPolyLine_Line_XY(plNext, 55.442915, 66.466169)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e43


# Create new component armature_winding_active_e42
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e42", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(49.851707, 70.756454)
plNext = AddPolyLine_Line_XY(plStart, 51.451975, 73.151424)
plNext = AddPolyLine_Line_XY(plNext, 47.893285, 75.529265)
plNext = AddPolyLine_Line_XY(plNext, 46.293017, 73.134294)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e42


# Create new component armature_winding_active_e41
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e41", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(40.189648, 76.658076)
plNext = AddPolyLine_Line_XY(plStart, 41.46362, 79.241434)
plNext = AddPolyLine_Line_XY(plNext, 37.625004, 81.13443)
plNext = AddPolyLine_Line_XY(plNext, 36.351033, 78.551071)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e41


# Create new component armature_winding_active_e40
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e40", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(29.839933, 81.248057)
plNext = AddPolyLine_Line_XY(plStart, 30.76581, 83.975601)
plNext = AddPolyLine_Line_XY(plNext, 26.712949, 85.351362)
plNext = AddPolyLine_Line_XY(plNext, 25.787072, 82.623818)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e40


# Create new component armature_winding_active_e39
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e39", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(18.979649, 84.447862)
plNext = AddPolyLine_Line_XY(plStart, 19.541589, 87.272922)
plNext = AddPolyLine_Line_XY(plNext, 15.343828, 88.107909)
plNext = AddPolyLine_Line_XY(plNext, 14.781888, 85.282848)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e39


# Create new component armature_winding_active_e38
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e38", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(7.794618, 86.20274)
plNext = AddPolyLine_Line_XY(plStart, 7.983005, 89.076979)
plNext = AddPolyLine_Line_XY(plNext, 3.712169, 89.356905)
plNext = AddPolyLine_Line_XY(plNext, 3.523782, 86.482665)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e38


# Create new component armature_winding_active_e37
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e37", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-3.523782, 86.482665)
plNext = AddPolyLine_Line_XY(plStart, -3.712169, 89.356905)
plNext = AddPolyLine_Line_XY(plNext, -7.983005, 89.076979)
plNext = AddPolyLine_Line_XY(plNext, -7.794618, 86.20274)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e37


# Create new component armature_winding_active_e36
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e36", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-14.781888, 85.282848)
plNext = AddPolyLine_Line_XY(plStart, -15.343828, 88.107909)
plNext = AddPolyLine_Line_XY(plNext, -19.541589, 87.272922)
plNext = AddPolyLine_Line_XY(plNext, -18.979649, 84.447862)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e36


# Create new component armature_winding_active_e35
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e35", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-25.787072, 82.623818)
plNext = AddPolyLine_Line_XY(plStart, -26.712949, 85.351362)
plNext = AddPolyLine_Line_XY(plNext, -30.76581, 83.975601)
plNext = AddPolyLine_Line_XY(plNext, -29.839933, 81.248057)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e35


# Create new component armature_winding_active_e34
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e34", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-36.351033, 78.551071)
plNext = AddPolyLine_Line_XY(plStart, -37.625004, 81.13443)
plNext = AddPolyLine_Line_XY(plNext, -41.46362, 79.241434)
plNext = AddPolyLine_Line_XY(plNext, -40.189648, 76.658076)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e34


# Create new component armature_winding_active_e33
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e33", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-46.293017, 73.134294)
plNext = AddPolyLine_Line_XY(plStart, -47.893285, 75.529265)
plNext = AddPolyLine_Line_XY(plNext, -51.451975, 73.151424)
plNext = AddPolyLine_Line_XY(plNext, -49.851707, 70.756454)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e33


# Create new component armature_winding_active_e32
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e32", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-55.442915, 66.466169)
plNext = AddPolyLine_Line_XY(plStart, -57.342099, 68.631774)
plNext = AddPolyLine_Line_XY(plNext, -60.559973, 65.809773)
plNext = AddPolyLine_Line_XY(plNext, -58.660789, 63.644169)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e32


# Create new component armature_winding_active_e31
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e31", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-63.644169, 58.660789)
plNext = AddPolyLine_Line_XY(plStart, -65.809773, 60.559973)
plNext = AddPolyLine_Line_XY(plNext, -68.631774, 57.342099)
plNext = AddPolyLine_Line_XY(plNext, -66.466169, 55.442915)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e31


# Create new component armature_winding_active_e30
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e30", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-70.756454, 49.851707)
plNext = AddPolyLine_Line_XY(plStart, -73.151424, 51.451975)
plNext = AddPolyLine_Line_XY(plNext, -75.529265, 47.893285)
plNext = AddPolyLine_Line_XY(plNext, -73.134294, 46.293017)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e30


# Create new component armature_winding_active_e29
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e29", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-76.658076, 40.189648)
plNext = AddPolyLine_Line_XY(plStart, -79.241434, 41.46362)
plNext = AddPolyLine_Line_XY(plNext, -81.13443, 37.625004)
plNext = AddPolyLine_Line_XY(plNext, -78.551071, 36.351033)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e29


# Create new component armature_winding_active_e28
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e28", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-81.248057, 29.839933)
plNext = AddPolyLine_Line_XY(plStart, -83.975601, 30.76581)
plNext = AddPolyLine_Line_XY(plNext, -85.351362, 26.712949)
plNext = AddPolyLine_Line_XY(plNext, -82.623818, 25.787072)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e28


# Create new component armature_winding_active_e27
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e27", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-84.447862, 18.979649)
plNext = AddPolyLine_Line_XY(plStart, -87.272922, 19.541589)
plNext = AddPolyLine_Line_XY(plNext, -88.107909, 15.343828)
plNext = AddPolyLine_Line_XY(plNext, -85.282848, 14.781888)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e27


# Create new component armature_winding_active_e26
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e26", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-86.20274, 7.794618)
plNext = AddPolyLine_Line_XY(plStart, -89.076979, 7.983005)
plNext = AddPolyLine_Line_XY(plNext, -89.356905, 3.712169)
plNext = AddPolyLine_Line_XY(plNext, -86.482665, 3.523782)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e26


# Create new component armature_winding_active_e25
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e25", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-86.482665, -3.523782)
plNext = AddPolyLine_Line_XY(plStart, -89.356905, -3.712169)
plNext = AddPolyLine_Line_XY(plNext, -89.076979, -7.983005)
plNext = AddPolyLine_Line_XY(plNext, -86.20274, -7.794618)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e25


# Create new component armature_winding_active_e24
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e24", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-85.282848, -14.781888)
plNext = AddPolyLine_Line_XY(plStart, -88.107909, -15.343828)
plNext = AddPolyLine_Line_XY(plNext, -87.272922, -19.541589)
plNext = AddPolyLine_Line_XY(plNext, -84.447862, -18.979649)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e24


# Create new component armature_winding_active_e23
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e23", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-82.623818, -25.787072)
plNext = AddPolyLine_Line_XY(plStart, -85.351362, -26.712949)
plNext = AddPolyLine_Line_XY(plNext, -83.975601, -30.76581)
plNext = AddPolyLine_Line_XY(plNext, -81.248057, -29.839933)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e23


# Create new component armature_winding_active_e22
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e22", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-78.551071, -36.351033)
plNext = AddPolyLine_Line_XY(plStart, -81.13443, -37.625004)
plNext = AddPolyLine_Line_XY(plNext, -79.241434, -41.46362)
plNext = AddPolyLine_Line_XY(plNext, -76.658076, -40.189648)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e22


# Create new component armature_winding_active_e21
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e21", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-73.134294, -46.293017)
plNext = AddPolyLine_Line_XY(plStart, -75.529265, -47.893285)
plNext = AddPolyLine_Line_XY(plNext, -73.151424, -51.451975)
plNext = AddPolyLine_Line_XY(plNext, -70.756454, -49.851707)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e21


# Create new component armature_winding_active_e20
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e20", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-66.466169, -55.442915)
plNext = AddPolyLine_Line_XY(plStart, -68.631774, -57.342099)
plNext = AddPolyLine_Line_XY(plNext, -65.809773, -60.559973)
plNext = AddPolyLine_Line_XY(plNext, -63.644169, -58.660789)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e20


# Create new component armature_winding_active_e19
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e19", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-58.660789, -63.644169)
plNext = AddPolyLine_Line_XY(plStart, -60.559973, -65.809773)
plNext = AddPolyLine_Line_XY(plNext, -57.342099, -68.631774)
plNext = AddPolyLine_Line_XY(plNext, -55.442915, -66.466169)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e19


# Create new component armature_winding_active_e18
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e18", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-49.851707, -70.756454)
plNext = AddPolyLine_Line_XY(plStart, -51.451975, -73.151424)
plNext = AddPolyLine_Line_XY(plNext, -47.893285, -75.529265)
plNext = AddPolyLine_Line_XY(plNext, -46.293017, -73.134294)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e18


# Create new component armature_winding_active_e17
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e17", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-40.189648, -76.658076)
plNext = AddPolyLine_Line_XY(plStart, -41.46362, -79.241434)
plNext = AddPolyLine_Line_XY(plNext, -37.625004, -81.13443)
plNext = AddPolyLine_Line_XY(plNext, -36.351033, -78.551071)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e17


# Create new component armature_winding_active_e16
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e16", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-29.839933, -81.248057)
plNext = AddPolyLine_Line_XY(plStart, -30.76581, -83.975601)
plNext = AddPolyLine_Line_XY(plNext, -26.712949, -85.351362)
plNext = AddPolyLine_Line_XY(plNext, -25.787072, -82.623818)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e16


# Create new component armature_winding_active_e15
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e15", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-18.979649, -84.447862)
plNext = AddPolyLine_Line_XY(plStart, -19.541589, -87.272922)
plNext = AddPolyLine_Line_XY(plNext, -15.343828, -88.107909)
plNext = AddPolyLine_Line_XY(plNext, -14.781888, -85.282848)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e15


# Create new component armature_winding_active_e14
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e14", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-7.794618, -86.20274)
plNext = AddPolyLine_Line_XY(plStart, -7.983005, -89.076979)
plNext = AddPolyLine_Line_XY(plNext, -3.712169, -89.356905)
plNext = AddPolyLine_Line_XY(plNext, -3.523782, -86.482665)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e14


# Create new component armature_winding_active_e13
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e13", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(3.523782, -86.482665)
plNext = AddPolyLine_Line_XY(plStart, 3.712169, -89.356905)
plNext = AddPolyLine_Line_XY(plNext, 7.983005, -89.076979)
plNext = AddPolyLine_Line_XY(plNext, 7.794618, -86.20274)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e13


# Create new component armature_winding_active_e12
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e12", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(14.781888, -85.282848)
plNext = AddPolyLine_Line_XY(plStart, 15.343828, -88.107909)
plNext = AddPolyLine_Line_XY(plNext, 19.541589, -87.272922)
plNext = AddPolyLine_Line_XY(plNext, 18.979649, -84.447862)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e12


# Create new component armature_winding_active_e11
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e11", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(25.787072, -82.623818)
plNext = AddPolyLine_Line_XY(plStart, 26.712949, -85.351362)
plNext = AddPolyLine_Line_XY(plNext, 30.76581, -83.975601)
plNext = AddPolyLine_Line_XY(plNext, 29.839933, -81.248057)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e11


# Create new component armature_winding_active_e10
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e10", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(36.351033, -78.551071)
plNext = AddPolyLine_Line_XY(plStart, 37.625004, -81.13443)
plNext = AddPolyLine_Line_XY(plNext, 41.46362, -79.241434)
plNext = AddPolyLine_Line_XY(plNext, 40.189648, -76.658076)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e10


# Create new component armature_winding_active_e9
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e9", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(46.293017, -73.134294)
plNext = AddPolyLine_Line_XY(plStart, 47.893285, -75.529265)
plNext = AddPolyLine_Line_XY(plNext, 51.451975, -73.151424)
plNext = AddPolyLine_Line_XY(plNext, 49.851707, -70.756454)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e9


# Create new component armature_winding_active_e8
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e8", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(55.442915, -66.466169)
plNext = AddPolyLine_Line_XY(plStart, 57.342099, -68.631774)
plNext = AddPolyLine_Line_XY(plNext, 60.559973, -65.809773)
plNext = AddPolyLine_Line_XY(plNext, 58.660789, -63.644169)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e8


# Create new component armature_winding_active_e7
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e7", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(63.644169, -58.660789)
plNext = AddPolyLine_Line_XY(plStart, 65.809773, -60.559973)
plNext = AddPolyLine_Line_XY(plNext, 68.631774, -57.342099)
plNext = AddPolyLine_Line_XY(plNext, 66.466169, -55.442915)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e7


# Create new component armature_winding_active_e6
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e6", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(70.756454, -49.851707)
plNext = AddPolyLine_Line_XY(plStart, 73.151424, -51.451975)
plNext = AddPolyLine_Line_XY(plNext, 75.529265, -47.893285)
plNext = AddPolyLine_Line_XY(plNext, 73.134294, -46.293017)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e6


# Create new component armature_winding_active_e5
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e5", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(76.658076, -40.189648)
plNext = AddPolyLine_Line_XY(plStart, 79.241434, -41.46362)
plNext = AddPolyLine_Line_XY(plNext, 81.13443, -37.625004)
plNext = AddPolyLine_Line_XY(plNext, 78.551071, -36.351033)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e5


# Create new component armature_winding_active_e4
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e4", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(81.248057, -29.839933)
plNext = AddPolyLine_Line_XY(plStart, 83.975601, -30.76581)
plNext = AddPolyLine_Line_XY(plNext, 85.351362, -26.712949)
plNext = AddPolyLine_Line_XY(plNext, 82.623818, -25.787072)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e4


# Create new component armature_winding_active_e3
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e3", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(84.447862, -18.979649)
plNext = AddPolyLine_Line_XY(plStart, 87.272922, -19.541589)
plNext = AddPolyLine_Line_XY(plNext, 88.107909, -15.343828)
plNext = AddPolyLine_Line_XY(plNext, 85.282848, -14.781888)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e3


# Create new component armature_winding_active_e2
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_e2", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(86.20274, -7.794618)
plNext = AddPolyLine_Line_XY(plStart, 89.076979, -7.983005)
plNext = AddPolyLine_Line_XY(plNext, 89.356905, -3.712169)
plNext = AddPolyLine_Line_XY(plNext, 86.482665, -3.523782)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_e2


# Create new component armature_winding_active_d48
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d48", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(88.107909, 15.343828)
plNext = AddPolyLine_Line_XY(plStart, 90.93297, 15.905767)
plNext = AddPolyLine_Line_XY(plNext, 90.097983, 20.103528)
plNext = AddPolyLine_Line_XY(plNext, 87.272922, 19.541589)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d48


# Create new component armature_winding_active_d47
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d47", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(85.351362, 26.712949)
plNext = AddPolyLine_Line_XY(plStart, 88.078906, 27.638825)
plNext = AddPolyLine_Line_XY(plNext, 86.703145, 31.691686)
plNext = AddPolyLine_Line_XY(plNext, 83.975601, 30.76581)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d47


# Create new component armature_winding_active_d46
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d46", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(81.13443, 37.625004)
plNext = AddPolyLine_Line_XY(plStart, 83.717788, 38.898976)
plNext = AddPolyLine_Line_XY(plNext, 81.824793, 42.737591)
plNext = AddPolyLine_Line_XY(plNext, 79.241434, 41.46362)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d46


# Create new component armature_winding_active_d45
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d45", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(75.529265, 47.893285)
plNext = AddPolyLine_Line_XY(plStart, 77.924236, 49.493554)
plNext = AddPolyLine_Line_XY(plNext, 75.546395, 53.052244)
plNext = AddPolyLine_Line_XY(plNext, 73.151424, 51.451975)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d45


# Create new component armature_winding_active_d44
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d44", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(68.631774, 57.342099)
plNext = AddPolyLine_Line_XY(plStart, 70.797378, 59.241283)
plNext = AddPolyLine_Line_XY(plNext, 67.975378, 62.459158)
plNext = AddPolyLine_Line_XY(plNext, 65.809773, 60.559973)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d44


# Create new component armature_winding_active_d43
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d43", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(60.559973, 65.809773)
plNext = AddPolyLine_Line_XY(plStart, 62.459158, 67.975378)
plNext = AddPolyLine_Line_XY(plNext, 59.241283, 70.797378)
plNext = AddPolyLine_Line_XY(plNext, 57.342099, 68.631774)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d43


# Create new component armature_winding_active_d42
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d42", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(51.451975, 73.151424)
plNext = AddPolyLine_Line_XY(plStart, 53.052244, 75.546395)
plNext = AddPolyLine_Line_XY(plNext, 49.493554, 77.924236)
plNext = AddPolyLine_Line_XY(plNext, 47.893285, 75.529265)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d42


# Create new component armature_winding_active_d41
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d41", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(41.46362, 79.241434)
plNext = AddPolyLine_Line_XY(plStart, 42.737591, 81.824793)
plNext = AddPolyLine_Line_XY(plNext, 38.898976, 83.717788)
plNext = AddPolyLine_Line_XY(plNext, 37.625004, 81.13443)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d41


# Create new component armature_winding_active_d40
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d40", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(30.76581, 83.975601)
plNext = AddPolyLine_Line_XY(plStart, 31.691686, 86.703145)
plNext = AddPolyLine_Line_XY(plNext, 27.638825, 88.078906)
plNext = AddPolyLine_Line_XY(plNext, 26.712949, 85.351362)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d40


# Create new component armature_winding_active_d39
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d39", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(19.541589, 87.272922)
plNext = AddPolyLine_Line_XY(plStart, 20.103528, 90.097983)
plNext = AddPolyLine_Line_XY(plNext, 15.905767, 90.93297)
plNext = AddPolyLine_Line_XY(plNext, 15.343828, 88.107909)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d39


# Create new component armature_winding_active_d38
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d38", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(7.983005, 89.076979)
plNext = AddPolyLine_Line_XY(plStart, 8.171393, 91.951219)
plNext = AddPolyLine_Line_XY(plNext, 3.900557, 92.231145)
plNext = AddPolyLine_Line_XY(plNext, 3.712169, 89.356905)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d38


# Create new component armature_winding_active_d37
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d37", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-3.712169, 89.356905)
plNext = AddPolyLine_Line_XY(plStart, -3.900557, 92.231145)
plNext = AddPolyLine_Line_XY(plNext, -8.171393, 91.951219)
plNext = AddPolyLine_Line_XY(plNext, -7.983005, 89.076979)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d37


# Create new component armature_winding_active_d36
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d36", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-15.343828, 88.107909)
plNext = AddPolyLine_Line_XY(plStart, -15.905767, 90.93297)
plNext = AddPolyLine_Line_XY(plNext, -20.103528, 90.097983)
plNext = AddPolyLine_Line_XY(plNext, -19.541589, 87.272922)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d36


# Create new component armature_winding_active_d35
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d35", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-26.712949, 85.351362)
plNext = AddPolyLine_Line_XY(plStart, -27.638825, 88.078906)
plNext = AddPolyLine_Line_XY(plNext, -31.691686, 86.703145)
plNext = AddPolyLine_Line_XY(plNext, -30.76581, 83.975601)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d35


# Create new component armature_winding_active_d34
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d34", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-37.625004, 81.13443)
plNext = AddPolyLine_Line_XY(plStart, -38.898976, 83.717788)
plNext = AddPolyLine_Line_XY(plNext, -42.737591, 81.824793)
plNext = AddPolyLine_Line_XY(plNext, -41.46362, 79.241434)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d34


# Create new component armature_winding_active_d33
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d33", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-47.893285, 75.529265)
plNext = AddPolyLine_Line_XY(plStart, -49.493554, 77.924236)
plNext = AddPolyLine_Line_XY(plNext, -53.052244, 75.546395)
plNext = AddPolyLine_Line_XY(plNext, -51.451975, 73.151424)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d33


# Create new component armature_winding_active_d32
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d32", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-57.342099, 68.631774)
plNext = AddPolyLine_Line_XY(plStart, -59.241283, 70.797378)
plNext = AddPolyLine_Line_XY(plNext, -62.459158, 67.975378)
plNext = AddPolyLine_Line_XY(plNext, -60.559973, 65.809773)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d32


# Create new component armature_winding_active_d31
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d31", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-65.809773, 60.559973)
plNext = AddPolyLine_Line_XY(plStart, -67.975378, 62.459158)
plNext = AddPolyLine_Line_XY(plNext, -70.797378, 59.241283)
plNext = AddPolyLine_Line_XY(plNext, -68.631774, 57.342099)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d31


# Create new component armature_winding_active_d30
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d30", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-73.151424, 51.451975)
plNext = AddPolyLine_Line_XY(plStart, -75.546395, 53.052244)
plNext = AddPolyLine_Line_XY(plNext, -77.924236, 49.493554)
plNext = AddPolyLine_Line_XY(plNext, -75.529265, 47.893285)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d30


# Create new component armature_winding_active_d29
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d29", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-79.241434, 41.46362)
plNext = AddPolyLine_Line_XY(plStart, -81.824793, 42.737591)
plNext = AddPolyLine_Line_XY(plNext, -83.717788, 38.898976)
plNext = AddPolyLine_Line_XY(plNext, -81.13443, 37.625004)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d29


# Create new component armature_winding_active_d28
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d28", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-83.975601, 30.76581)
plNext = AddPolyLine_Line_XY(plStart, -86.703145, 31.691686)
plNext = AddPolyLine_Line_XY(plNext, -88.078906, 27.638825)
plNext = AddPolyLine_Line_XY(plNext, -85.351362, 26.712949)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d28


# Create new component armature_winding_active_d27
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d27", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-87.272922, 19.541589)
plNext = AddPolyLine_Line_XY(plStart, -90.097983, 20.103528)
plNext = AddPolyLine_Line_XY(plNext, -90.93297, 15.905767)
plNext = AddPolyLine_Line_XY(plNext, -88.107909, 15.343828)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d27


# Create new component armature_winding_active_d26
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d26", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-89.076979, 7.983005)
plNext = AddPolyLine_Line_XY(plStart, -91.951219, 8.171393)
plNext = AddPolyLine_Line_XY(plNext, -92.231145, 3.900557)
plNext = AddPolyLine_Line_XY(plNext, -89.356905, 3.712169)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d26


# Create new component armature_winding_active_d25
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d25", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-89.356905, -3.712169)
plNext = AddPolyLine_Line_XY(plStart, -92.231145, -3.900557)
plNext = AddPolyLine_Line_XY(plNext, -91.951219, -8.171393)
plNext = AddPolyLine_Line_XY(plNext, -89.076979, -7.983005)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d25


# Create new component armature_winding_active_d24
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d24", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-88.107909, -15.343828)
plNext = AddPolyLine_Line_XY(plStart, -90.93297, -15.905767)
plNext = AddPolyLine_Line_XY(plNext, -90.097983, -20.103528)
plNext = AddPolyLine_Line_XY(plNext, -87.272922, -19.541589)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d24


# Create new component armature_winding_active_d23
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d23", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-85.351362, -26.712949)
plNext = AddPolyLine_Line_XY(plStart, -88.078906, -27.638825)
plNext = AddPolyLine_Line_XY(plNext, -86.703145, -31.691686)
plNext = AddPolyLine_Line_XY(plNext, -83.975601, -30.76581)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d23


# Create new component armature_winding_active_d22
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d22", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-81.13443, -37.625004)
plNext = AddPolyLine_Line_XY(plStart, -83.717788, -38.898976)
plNext = AddPolyLine_Line_XY(plNext, -81.824793, -42.737591)
plNext = AddPolyLine_Line_XY(plNext, -79.241434, -41.46362)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d22


# Create new component armature_winding_active_d21
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d21", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-75.529265, -47.893285)
plNext = AddPolyLine_Line_XY(plStart, -77.924236, -49.493554)
plNext = AddPolyLine_Line_XY(plNext, -75.546395, -53.052244)
plNext = AddPolyLine_Line_XY(plNext, -73.151424, -51.451975)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d21


# Create new component armature_winding_active_d20
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d20", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-68.631774, -57.342099)
plNext = AddPolyLine_Line_XY(plStart, -70.797378, -59.241283)
plNext = AddPolyLine_Line_XY(plNext, -67.975378, -62.459158)
plNext = AddPolyLine_Line_XY(plNext, -65.809773, -60.559973)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d20


# Create new component armature_winding_active_d19
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d19", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-60.559973, -65.809773)
plNext = AddPolyLine_Line_XY(plStart, -62.459158, -67.975378)
plNext = AddPolyLine_Line_XY(plNext, -59.241283, -70.797378)
plNext = AddPolyLine_Line_XY(plNext, -57.342099, -68.631774)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d19


# Create new component armature_winding_active_d18
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d18", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-51.451975, -73.151424)
plNext = AddPolyLine_Line_XY(plStart, -53.052244, -75.546395)
plNext = AddPolyLine_Line_XY(plNext, -49.493554, -77.924236)
plNext = AddPolyLine_Line_XY(plNext, -47.893285, -75.529265)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d18


# Create new component armature_winding_active_d17
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d17", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-41.46362, -79.241434)
plNext = AddPolyLine_Line_XY(plStart, -42.737591, -81.824793)
plNext = AddPolyLine_Line_XY(plNext, -38.898976, -83.717788)
plNext = AddPolyLine_Line_XY(plNext, -37.625004, -81.13443)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d17


# Create new component armature_winding_active_d16
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d16", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-30.76581, -83.975601)
plNext = AddPolyLine_Line_XY(plStart, -31.691686, -86.703145)
plNext = AddPolyLine_Line_XY(plNext, -27.638825, -88.078906)
plNext = AddPolyLine_Line_XY(plNext, -26.712949, -85.351362)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d16


# Create new component armature_winding_active_d15
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d15", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-19.541589, -87.272922)
plNext = AddPolyLine_Line_XY(plStart, -20.103528, -90.097983)
plNext = AddPolyLine_Line_XY(plNext, -15.905767, -90.93297)
plNext = AddPolyLine_Line_XY(plNext, -15.343828, -88.107909)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d15


# Create new component armature_winding_active_d14
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d14", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-7.983005, -89.076979)
plNext = AddPolyLine_Line_XY(plStart, -8.171393, -91.951219)
plNext = AddPolyLine_Line_XY(plNext, -3.900557, -92.231145)
plNext = AddPolyLine_Line_XY(plNext, -3.712169, -89.356905)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d14


# Create new component armature_winding_active_d13
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d13", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(3.712169, -89.356905)
plNext = AddPolyLine_Line_XY(plStart, 3.900557, -92.231145)
plNext = AddPolyLine_Line_XY(plNext, 8.171393, -91.951219)
plNext = AddPolyLine_Line_XY(plNext, 7.983005, -89.076979)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d13


# Create new component armature_winding_active_d12
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d12", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(15.343828, -88.107909)
plNext = AddPolyLine_Line_XY(plStart, 15.905767, -90.93297)
plNext = AddPolyLine_Line_XY(plNext, 20.103528, -90.097983)
plNext = AddPolyLine_Line_XY(plNext, 19.541589, -87.272922)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d12


# Create new component armature_winding_active_d11
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d11", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(26.712949, -85.351362)
plNext = AddPolyLine_Line_XY(plStart, 27.638825, -88.078906)
plNext = AddPolyLine_Line_XY(plNext, 31.691686, -86.703145)
plNext = AddPolyLine_Line_XY(plNext, 30.76581, -83.975601)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d11


# Create new component armature_winding_active_d10
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d10", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(37.625004, -81.13443)
plNext = AddPolyLine_Line_XY(plStart, 38.898976, -83.717788)
plNext = AddPolyLine_Line_XY(plNext, 42.737591, -81.824793)
plNext = AddPolyLine_Line_XY(plNext, 41.46362, -79.241434)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d10


# Create new component armature_winding_active_d9
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d9", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(47.893285, -75.529265)
plNext = AddPolyLine_Line_XY(plStart, 49.493554, -77.924236)
plNext = AddPolyLine_Line_XY(plNext, 53.052244, -75.546395)
plNext = AddPolyLine_Line_XY(plNext, 51.451975, -73.151424)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d9


# Create new component armature_winding_active_d8
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d8", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(57.342099, -68.631774)
plNext = AddPolyLine_Line_XY(plStart, 59.241283, -70.797378)
plNext = AddPolyLine_Line_XY(plNext, 62.459158, -67.975378)
plNext = AddPolyLine_Line_XY(plNext, 60.559973, -65.809773)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d8


# Create new component armature_winding_active_d7
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d7", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(65.809773, -60.559973)
plNext = AddPolyLine_Line_XY(plStart, 67.975378, -62.459158)
plNext = AddPolyLine_Line_XY(plNext, 70.797378, -59.241283)
plNext = AddPolyLine_Line_XY(plNext, 68.631774, -57.342099)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d7


# Create new component armature_winding_active_d6
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d6", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(73.151424, -51.451975)
plNext = AddPolyLine_Line_XY(plStart, 75.546395, -53.052244)
plNext = AddPolyLine_Line_XY(plNext, 77.924236, -49.493554)
plNext = AddPolyLine_Line_XY(plNext, 75.529265, -47.893285)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d6


# Create new component armature_winding_active_d5
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d5", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(79.241434, -41.46362)
plNext = AddPolyLine_Line_XY(plStart, 81.824793, -42.737591)
plNext = AddPolyLine_Line_XY(plNext, 83.717788, -38.898976)
plNext = AddPolyLine_Line_XY(plNext, 81.13443, -37.625004)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d5


# Create new component armature_winding_active_d4
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d4", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(83.975601, -30.76581)
plNext = AddPolyLine_Line_XY(plStart, 86.703145, -31.691686)
plNext = AddPolyLine_Line_XY(plNext, 88.078906, -27.638825)
plNext = AddPolyLine_Line_XY(plNext, 85.351362, -26.712949)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d4


# Create new component armature_winding_active_d3
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d3", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(87.272922, -19.541589)
plNext = AddPolyLine_Line_XY(plStart, 90.097983, -20.103528)
plNext = AddPolyLine_Line_XY(plNext, 90.93297, -15.905767)
plNext = AddPolyLine_Line_XY(plNext, 88.107909, -15.343828)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d3


# Create new component armature_winding_active_d2
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_d2", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(89.076979, -7.983005)
plNext = AddPolyLine_Line_XY(plStart, 91.951219, -8.171393)
plNext = AddPolyLine_Line_XY(plNext, 92.231145, -3.900557)
plNext = AddPolyLine_Line_XY(plNext, 89.356905, -3.712169)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_d2


# Create new component armature_winding_active_c48
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c48", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(90.93297, 15.905767)
plNext = AddPolyLine_Line_XY(plStart, 93.75803, 16.467707)
plNext = AddPolyLine_Line_XY(plNext, 92.923044, 20.665468)
plNext = AddPolyLine_Line_XY(plNext, 90.097983, 20.103528)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c48


# Create new component armature_winding_active_c47
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c47", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(88.078906, 27.638825)
plNext = AddPolyLine_Line_XY(plStart, 90.80645, 28.564702)
plNext = AddPolyLine_Line_XY(plNext, 89.430689, 32.617563)
plNext = AddPolyLine_Line_XY(plNext, 86.703145, 31.691686)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c47


# Create new component armature_winding_active_c46
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c46", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(83.717788, 38.898976)
plNext = AddPolyLine_Line_XY(plStart, 86.301147, 40.172947)
plNext = AddPolyLine_Line_XY(plNext, 84.408151, 44.011562)
plNext = AddPolyLine_Line_XY(plNext, 81.824793, 42.737591)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c46


# Create new component armature_winding_active_c45
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c45", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(77.924236, 49.493554)
plNext = AddPolyLine_Line_XY(plStart, 80.319207, 51.093822)
plNext = AddPolyLine_Line_XY(plNext, 77.941366, 54.652512)
plNext = AddPolyLine_Line_XY(plNext, 75.546395, 53.052244)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c45


# Create new component armature_winding_active_c44
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c44", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(70.797378, 59.241283)
plNext = AddPolyLine_Line_XY(plStart, 72.962983, 61.140467)
plNext = AddPolyLine_Line_XY(plNext, 70.140983, 64.358342)
plNext = AddPolyLine_Line_XY(plNext, 67.975378, 62.459158)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c44


# Create new component armature_winding_active_c43
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c43", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(62.459158, 67.975378)
plNext = AddPolyLine_Line_XY(plStart, 64.358342, 70.140983)
plNext = AddPolyLine_Line_XY(plNext, 61.140467, 72.962983)
plNext = AddPolyLine_Line_XY(plNext, 59.241283, 70.797378)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c43


# Create new component armature_winding_active_c42
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c42", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(53.052244, 75.546395)
plNext = AddPolyLine_Line_XY(plStart, 54.652512, 77.941366)
plNext = AddPolyLine_Line_XY(plNext, 51.093822, 80.319207)
plNext = AddPolyLine_Line_XY(plNext, 49.493554, 77.924236)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c42


# Create new component armature_winding_active_c41
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c41", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(42.737591, 81.824793)
plNext = AddPolyLine_Line_XY(plStart, 44.011562, 84.408151)
plNext = AddPolyLine_Line_XY(plNext, 40.172947, 86.301147)
plNext = AddPolyLine_Line_XY(plNext, 38.898976, 83.717788)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c41


# Create new component armature_winding_active_c40
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c40", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(31.691686, 86.703145)
plNext = AddPolyLine_Line_XY(plStart, 32.617563, 89.430689)
plNext = AddPolyLine_Line_XY(plNext, 28.564702, 90.80645)
plNext = AddPolyLine_Line_XY(plNext, 27.638825, 88.078906)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c40


# Create new component armature_winding_active_c39
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c39", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(20.103528, 90.097983)
plNext = AddPolyLine_Line_XY(plStart, 20.665468, 92.923044)
plNext = AddPolyLine_Line_XY(plNext, 16.467707, 93.75803)
plNext = AddPolyLine_Line_XY(plNext, 15.905767, 90.93297)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c39


# Create new component armature_winding_active_c38
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c38", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(8.171393, 91.951219)
plNext = AddPolyLine_Line_XY(plStart, 8.359781, 94.825459)
plNext = AddPolyLine_Line_XY(plNext, 4.088944, 95.105384)
plNext = AddPolyLine_Line_XY(plNext, 3.900557, 92.231145)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c38


# Create new component armature_winding_active_c37
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c37", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-3.900557, 92.231145)
plNext = AddPolyLine_Line_XY(plStart, -4.088944, 95.105384)
plNext = AddPolyLine_Line_XY(plNext, -8.359781, 94.825459)
plNext = AddPolyLine_Line_XY(plNext, -8.171393, 91.951219)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c37


# Create new component armature_winding_active_c36
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c36", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-15.905767, 90.93297)
plNext = AddPolyLine_Line_XY(plStart, -16.467707, 93.75803)
plNext = AddPolyLine_Line_XY(plNext, -20.665468, 92.923044)
plNext = AddPolyLine_Line_XY(plNext, -20.103528, 90.097983)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c36


# Create new component armature_winding_active_c35
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c35", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-27.638825, 88.078906)
plNext = AddPolyLine_Line_XY(plStart, -28.564702, 90.80645)
plNext = AddPolyLine_Line_XY(plNext, -32.617563, 89.430689)
plNext = AddPolyLine_Line_XY(plNext, -31.691686, 86.703145)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c35


# Create new component armature_winding_active_c34
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c34", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-38.898976, 83.717788)
plNext = AddPolyLine_Line_XY(plStart, -40.172947, 86.301147)
plNext = AddPolyLine_Line_XY(plNext, -44.011562, 84.408151)
plNext = AddPolyLine_Line_XY(plNext, -42.737591, 81.824793)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c34


# Create new component armature_winding_active_c33
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c33", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-49.493554, 77.924236)
plNext = AddPolyLine_Line_XY(plStart, -51.093822, 80.319207)
plNext = AddPolyLine_Line_XY(plNext, -54.652512, 77.941366)
plNext = AddPolyLine_Line_XY(plNext, -53.052244, 75.546395)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c33


# Create new component armature_winding_active_c32
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c32", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-59.241283, 70.797378)
plNext = AddPolyLine_Line_XY(plStart, -61.140467, 72.962983)
plNext = AddPolyLine_Line_XY(plNext, -64.358342, 70.140983)
plNext = AddPolyLine_Line_XY(plNext, -62.459158, 67.975378)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c32


# Create new component armature_winding_active_c31
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c31", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-67.975378, 62.459158)
plNext = AddPolyLine_Line_XY(plStart, -70.140983, 64.358342)
plNext = AddPolyLine_Line_XY(plNext, -72.962983, 61.140467)
plNext = AddPolyLine_Line_XY(plNext, -70.797378, 59.241283)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c31


# Create new component armature_winding_active_c30
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c30", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-75.546395, 53.052244)
plNext = AddPolyLine_Line_XY(plStart, -77.941366, 54.652512)
plNext = AddPolyLine_Line_XY(plNext, -80.319207, 51.093822)
plNext = AddPolyLine_Line_XY(plNext, -77.924236, 49.493554)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c30


# Create new component armature_winding_active_c29
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c29", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-81.824793, 42.737591)
plNext = AddPolyLine_Line_XY(plStart, -84.408151, 44.011562)
plNext = AddPolyLine_Line_XY(plNext, -86.301147, 40.172947)
plNext = AddPolyLine_Line_XY(plNext, -83.717788, 38.898976)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c29


# Create new component armature_winding_active_c28
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c28", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-86.703145, 31.691686)
plNext = AddPolyLine_Line_XY(plStart, -89.430689, 32.617563)
plNext = AddPolyLine_Line_XY(plNext, -90.80645, 28.564702)
plNext = AddPolyLine_Line_XY(plNext, -88.078906, 27.638825)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c28


# Create new component armature_winding_active_c27
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c27", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-90.097983, 20.103528)
plNext = AddPolyLine_Line_XY(plStart, -92.923044, 20.665468)
plNext = AddPolyLine_Line_XY(plNext, -93.75803, 16.467707)
plNext = AddPolyLine_Line_XY(plNext, -90.93297, 15.905767)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c27


# Create new component armature_winding_active_c26
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c26", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-91.951219, 8.171393)
plNext = AddPolyLine_Line_XY(plStart, -94.825459, 8.359781)
plNext = AddPolyLine_Line_XY(plNext, -95.105384, 4.088944)
plNext = AddPolyLine_Line_XY(plNext, -92.231145, 3.900557)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c26


# Create new component armature_winding_active_c25
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c25", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-92.231145, -3.900557)
plNext = AddPolyLine_Line_XY(plStart, -95.105384, -4.088944)
plNext = AddPolyLine_Line_XY(plNext, -94.825459, -8.359781)
plNext = AddPolyLine_Line_XY(plNext, -91.951219, -8.171393)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c25


# Create new component armature_winding_active_c24
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c24", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-90.93297, -15.905767)
plNext = AddPolyLine_Line_XY(plStart, -93.75803, -16.467707)
plNext = AddPolyLine_Line_XY(plNext, -92.923044, -20.665468)
plNext = AddPolyLine_Line_XY(plNext, -90.097983, -20.103528)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c24


# Create new component armature_winding_active_c23
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c23", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-88.078906, -27.638825)
plNext = AddPolyLine_Line_XY(plStart, -90.80645, -28.564702)
plNext = AddPolyLine_Line_XY(plNext, -89.430689, -32.617563)
plNext = AddPolyLine_Line_XY(plNext, -86.703145, -31.691686)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c23


# Create new component armature_winding_active_c22
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c22", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-83.717788, -38.898976)
plNext = AddPolyLine_Line_XY(plStart, -86.301147, -40.172947)
plNext = AddPolyLine_Line_XY(plNext, -84.408151, -44.011562)
plNext = AddPolyLine_Line_XY(plNext, -81.824793, -42.737591)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c22


# Create new component armature_winding_active_c21
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c21", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-77.924236, -49.493554)
plNext = AddPolyLine_Line_XY(plStart, -80.319207, -51.093822)
plNext = AddPolyLine_Line_XY(plNext, -77.941366, -54.652512)
plNext = AddPolyLine_Line_XY(plNext, -75.546395, -53.052244)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c21


# Create new component armature_winding_active_c20
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c20", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-70.797378, -59.241283)
plNext = AddPolyLine_Line_XY(plStart, -72.962983, -61.140467)
plNext = AddPolyLine_Line_XY(plNext, -70.140983, -64.358342)
plNext = AddPolyLine_Line_XY(plNext, -67.975378, -62.459158)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c20


# Create new component armature_winding_active_c19
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c19", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-62.459158, -67.975378)
plNext = AddPolyLine_Line_XY(plStart, -64.358342, -70.140983)
plNext = AddPolyLine_Line_XY(plNext, -61.140467, -72.962983)
plNext = AddPolyLine_Line_XY(plNext, -59.241283, -70.797378)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c19


# Create new component armature_winding_active_c18
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c18", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-53.052244, -75.546395)
plNext = AddPolyLine_Line_XY(plStart, -54.652512, -77.941366)
plNext = AddPolyLine_Line_XY(plNext, -51.093822, -80.319207)
plNext = AddPolyLine_Line_XY(plNext, -49.493554, -77.924236)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c18


# Create new component armature_winding_active_c17
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c17", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-42.737591, -81.824793)
plNext = AddPolyLine_Line_XY(plStart, -44.011562, -84.408151)
plNext = AddPolyLine_Line_XY(plNext, -40.172947, -86.301147)
plNext = AddPolyLine_Line_XY(plNext, -38.898976, -83.717788)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c17


# Create new component armature_winding_active_c16
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c16", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-31.691686, -86.703145)
plNext = AddPolyLine_Line_XY(plStart, -32.617563, -89.430689)
plNext = AddPolyLine_Line_XY(plNext, -28.564702, -90.80645)
plNext = AddPolyLine_Line_XY(plNext, -27.638825, -88.078906)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c16


# Create new component armature_winding_active_c15
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c15", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-20.103528, -90.097983)
plNext = AddPolyLine_Line_XY(plStart, -20.665468, -92.923044)
plNext = AddPolyLine_Line_XY(plNext, -16.467707, -93.75803)
plNext = AddPolyLine_Line_XY(plNext, -15.905767, -90.93297)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c15


# Create new component armature_winding_active_c14
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c14", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-8.171393, -91.951219)
plNext = AddPolyLine_Line_XY(plStart, -8.359781, -94.825459)
plNext = AddPolyLine_Line_XY(plNext, -4.088944, -95.105384)
plNext = AddPolyLine_Line_XY(plNext, -3.900557, -92.231145)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c14


# Create new component armature_winding_active_c13
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c13", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(3.900557, -92.231145)
plNext = AddPolyLine_Line_XY(plStart, 4.088944, -95.105384)
plNext = AddPolyLine_Line_XY(plNext, 8.359781, -94.825459)
plNext = AddPolyLine_Line_XY(plNext, 8.171393, -91.951219)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c13


# Create new component armature_winding_active_c12
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c12", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(15.905767, -90.93297)
plNext = AddPolyLine_Line_XY(plStart, 16.467707, -93.75803)
plNext = AddPolyLine_Line_XY(plNext, 20.665468, -92.923044)
plNext = AddPolyLine_Line_XY(plNext, 20.103528, -90.097983)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c12


# Create new component armature_winding_active_c11
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c11", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(27.638825, -88.078906)
plNext = AddPolyLine_Line_XY(plStart, 28.564702, -90.80645)
plNext = AddPolyLine_Line_XY(plNext, 32.617563, -89.430689)
plNext = AddPolyLine_Line_XY(plNext, 31.691686, -86.703145)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c11


# Create new component armature_winding_active_c10
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c10", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(38.898976, -83.717788)
plNext = AddPolyLine_Line_XY(plStart, 40.172947, -86.301147)
plNext = AddPolyLine_Line_XY(plNext, 44.011562, -84.408151)
plNext = AddPolyLine_Line_XY(plNext, 42.737591, -81.824793)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c10


# Create new component armature_winding_active_c9
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c9", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(49.493554, -77.924236)
plNext = AddPolyLine_Line_XY(plStart, 51.093822, -80.319207)
plNext = AddPolyLine_Line_XY(plNext, 54.652512, -77.941366)
plNext = AddPolyLine_Line_XY(plNext, 53.052244, -75.546395)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c9


# Create new component armature_winding_active_c8
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c8", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(59.241283, -70.797378)
plNext = AddPolyLine_Line_XY(plStart, 61.140467, -72.962983)
plNext = AddPolyLine_Line_XY(plNext, 64.358342, -70.140983)
plNext = AddPolyLine_Line_XY(plNext, 62.459158, -67.975378)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c8


# Create new component armature_winding_active_c7
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c7", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(67.975378, -62.459158)
plNext = AddPolyLine_Line_XY(plStart, 70.140983, -64.358342)
plNext = AddPolyLine_Line_XY(plNext, 72.962983, -61.140467)
plNext = AddPolyLine_Line_XY(plNext, 70.797378, -59.241283)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c7


# Create new component armature_winding_active_c6
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c6", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(75.546395, -53.052244)
plNext = AddPolyLine_Line_XY(plStart, 77.941366, -54.652512)
plNext = AddPolyLine_Line_XY(plNext, 80.319207, -51.093822)
plNext = AddPolyLine_Line_XY(plNext, 77.924236, -49.493554)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c6


# Create new component armature_winding_active_c5
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c5", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(81.824793, -42.737591)
plNext = AddPolyLine_Line_XY(plStart, 84.408151, -44.011562)
plNext = AddPolyLine_Line_XY(plNext, 86.301147, -40.172947)
plNext = AddPolyLine_Line_XY(plNext, 83.717788, -38.898976)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c5


# Create new component armature_winding_active_c4
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c4", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(86.703145, -31.691686)
plNext = AddPolyLine_Line_XY(plStart, 89.430689, -32.617563)
plNext = AddPolyLine_Line_XY(plNext, 90.80645, -28.564702)
plNext = AddPolyLine_Line_XY(plNext, 88.078906, -27.638825)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c4


# Create new component armature_winding_active_c3
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c3", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(90.097983, -20.103528)
plNext = AddPolyLine_Line_XY(plStart, 92.923044, -20.665468)
plNext = AddPolyLine_Line_XY(plNext, 93.75803, -16.467707)
plNext = AddPolyLine_Line_XY(plNext, 90.93297, -15.905767)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c3


# Create new component armature_winding_active_c2
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_c2", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(91.951219, -8.171393)
plNext = AddPolyLine_Line_XY(plStart, 94.825459, -8.359781)
plNext = AddPolyLine_Line_XY(plNext, 95.105384, -4.088944)
plNext = AddPolyLine_Line_XY(plNext, 92.231145, -3.900557)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_c2


# Create new component armature_winding_active_b48
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b48", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(93.75803, 16.467707)
plNext = AddPolyLine_Line_XY(plStart, 96.583091, 17.029646)
plNext = AddPolyLine_Line_XY(plNext, 95.748104, 21.227407)
plNext = AddPolyLine_Line_XY(plNext, 92.923044, 20.665468)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b48


# Create new component armature_winding_active_b47
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b47", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(90.80645, 28.564702)
plNext = AddPolyLine_Line_XY(plStart, 93.533994, 29.490578)
plNext = AddPolyLine_Line_XY(plNext, 92.158233, 33.543439)
plNext = AddPolyLine_Line_XY(plNext, 89.430689, 32.617563)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b47


# Create new component armature_winding_active_b46
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b46", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(86.301147, 40.172947)
plNext = AddPolyLine_Line_XY(plStart, 88.884505, 41.446918)
plNext = AddPolyLine_Line_XY(plNext, 86.99151, 45.285534)
plNext = AddPolyLine_Line_XY(plNext, 84.408151, 44.011562)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b46


# Create new component armature_winding_active_b45
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b45", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(80.319207, 51.093822)
plNext = AddPolyLine_Line_XY(plStart, 82.714177, 52.69409)
plNext = AddPolyLine_Line_XY(plNext, 80.336337, 56.25278)
plNext = AddPolyLine_Line_XY(plNext, 77.941366, 54.652512)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b45


# Create new component armature_winding_active_b44
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b44", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(72.962983, 61.140467)
plNext = AddPolyLine_Line_XY(plStart, 75.128587, 63.039652)
plNext = AddPolyLine_Line_XY(plNext, 72.306587, 66.257526)
plNext = AddPolyLine_Line_XY(plNext, 70.140983, 64.358342)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b44


# Create new component armature_winding_active_b43
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b43", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(64.358342, 70.140983)
plNext = AddPolyLine_Line_XY(plStart, 66.257526, 72.306587)
plNext = AddPolyLine_Line_XY(plNext, 63.039652, 75.128587)
plNext = AddPolyLine_Line_XY(plNext, 61.140467, 72.962983)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b43


# Create new component armature_winding_active_b42
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b42", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(54.652512, 77.941366)
plNext = AddPolyLine_Line_XY(plStart, 56.25278, 80.336337)
plNext = AddPolyLine_Line_XY(plNext, 52.69409, 82.714177)
plNext = AddPolyLine_Line_XY(plNext, 51.093822, 80.319207)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b42


# Create new component armature_winding_active_b41
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b41", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(44.011562, 84.408151)
plNext = AddPolyLine_Line_XY(plStart, 45.285534, 86.99151)
plNext = AddPolyLine_Line_XY(plNext, 41.446918, 88.884505)
plNext = AddPolyLine_Line_XY(plNext, 40.172947, 86.301147)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b41


# Create new component armature_winding_active_b40
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b40", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(32.617563, 89.430689)
plNext = AddPolyLine_Line_XY(plStart, 33.543439, 92.158233)
plNext = AddPolyLine_Line_XY(plNext, 29.490578, 93.533994)
plNext = AddPolyLine_Line_XY(plNext, 28.564702, 90.80645)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b40


# Create new component armature_winding_active_b39
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b39", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(20.665468, 92.923044)
plNext = AddPolyLine_Line_XY(plStart, 21.227407, 95.748104)
plNext = AddPolyLine_Line_XY(plNext, 17.029646, 96.583091)
plNext = AddPolyLine_Line_XY(plNext, 16.467707, 93.75803)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b39


# Create new component armature_winding_active_b38
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b38", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(8.359781, 94.825459)
plNext = AddPolyLine_Line_XY(plStart, 8.548168, 97.699699)
plNext = AddPolyLine_Line_XY(plNext, 4.277332, 97.979624)
plNext = AddPolyLine_Line_XY(plNext, 4.088944, 95.105384)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b38


# Create new component armature_winding_active_b37
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b37", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-4.088944, 95.105384)
plNext = AddPolyLine_Line_XY(plStart, -4.277332, 97.979624)
plNext = AddPolyLine_Line_XY(plNext, -8.548168, 97.699699)
plNext = AddPolyLine_Line_XY(plNext, -8.359781, 94.825459)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b37


# Create new component armature_winding_active_b36
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b36", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-16.467707, 93.75803)
plNext = AddPolyLine_Line_XY(plStart, -17.029646, 96.583091)
plNext = AddPolyLine_Line_XY(plNext, -21.227407, 95.748104)
plNext = AddPolyLine_Line_XY(plNext, -20.665468, 92.923044)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b36


# Create new component armature_winding_active_b35
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b35", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-28.564702, 90.80645)
plNext = AddPolyLine_Line_XY(plStart, -29.490578, 93.533994)
plNext = AddPolyLine_Line_XY(plNext, -33.543439, 92.158233)
plNext = AddPolyLine_Line_XY(plNext, -32.617563, 89.430689)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b35


# Create new component armature_winding_active_b34
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b34", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-40.172947, 86.301147)
plNext = AddPolyLine_Line_XY(plStart, -41.446918, 88.884505)
plNext = AddPolyLine_Line_XY(plNext, -45.285534, 86.99151)
plNext = AddPolyLine_Line_XY(plNext, -44.011562, 84.408151)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b34


# Create new component armature_winding_active_b33
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b33", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-51.093822, 80.319207)
plNext = AddPolyLine_Line_XY(plStart, -52.69409, 82.714177)
plNext = AddPolyLine_Line_XY(plNext, -56.25278, 80.336337)
plNext = AddPolyLine_Line_XY(plNext, -54.652512, 77.941366)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b33


# Create new component armature_winding_active_b32
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b32", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-61.140467, 72.962983)
plNext = AddPolyLine_Line_XY(plStart, -63.039652, 75.128587)
plNext = AddPolyLine_Line_XY(plNext, -66.257526, 72.306587)
plNext = AddPolyLine_Line_XY(plNext, -64.358342, 70.140983)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b32


# Create new component armature_winding_active_b31
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b31", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-70.140983, 64.358342)
plNext = AddPolyLine_Line_XY(plStart, -72.306587, 66.257526)
plNext = AddPolyLine_Line_XY(plNext, -75.128587, 63.039652)
plNext = AddPolyLine_Line_XY(plNext, -72.962983, 61.140467)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b31


# Create new component armature_winding_active_b30
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b30", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-77.941366, 54.652512)
plNext = AddPolyLine_Line_XY(plStart, -80.336337, 56.25278)
plNext = AddPolyLine_Line_XY(plNext, -82.714177, 52.69409)
plNext = AddPolyLine_Line_XY(plNext, -80.319207, 51.093822)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b30


# Create new component armature_winding_active_b29
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b29", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-84.408151, 44.011562)
plNext = AddPolyLine_Line_XY(plStart, -86.99151, 45.285534)
plNext = AddPolyLine_Line_XY(plNext, -88.884505, 41.446918)
plNext = AddPolyLine_Line_XY(plNext, -86.301147, 40.172947)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b29


# Create new component armature_winding_active_b28
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b28", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-89.430689, 32.617563)
plNext = AddPolyLine_Line_XY(plStart, -92.158233, 33.543439)
plNext = AddPolyLine_Line_XY(plNext, -93.533994, 29.490578)
plNext = AddPolyLine_Line_XY(plNext, -90.80645, 28.564702)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b28


# Create new component armature_winding_active_b27
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b27", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-92.923044, 20.665468)
plNext = AddPolyLine_Line_XY(plStart, -95.748104, 21.227407)
plNext = AddPolyLine_Line_XY(plNext, -96.583091, 17.029646)
plNext = AddPolyLine_Line_XY(plNext, -93.75803, 16.467707)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b27


# Create new component armature_winding_active_b26
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b26", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-94.825459, 8.359781)
plNext = AddPolyLine_Line_XY(plStart, -97.699699, 8.548168)
plNext = AddPolyLine_Line_XY(plNext, -97.979624, 4.277332)
plNext = AddPolyLine_Line_XY(plNext, -95.105384, 4.088944)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b26


# Create new component armature_winding_active_b25
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b25", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-95.105384, -4.088944)
plNext = AddPolyLine_Line_XY(plStart, -97.979624, -4.277332)
plNext = AddPolyLine_Line_XY(plNext, -97.699699, -8.548168)
plNext = AddPolyLine_Line_XY(plNext, -94.825459, -8.359781)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b25


# Create new component armature_winding_active_b24
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b24", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-93.75803, -16.467707)
plNext = AddPolyLine_Line_XY(plStart, -96.583091, -17.029646)
plNext = AddPolyLine_Line_XY(plNext, -95.748104, -21.227407)
plNext = AddPolyLine_Line_XY(plNext, -92.923044, -20.665468)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b24


# Create new component armature_winding_active_b23
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b23", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-90.80645, -28.564702)
plNext = AddPolyLine_Line_XY(plStart, -93.533994, -29.490578)
plNext = AddPolyLine_Line_XY(plNext, -92.158233, -33.543439)
plNext = AddPolyLine_Line_XY(plNext, -89.430689, -32.617563)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b23


# Create new component armature_winding_active_b22
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b22", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-86.301147, -40.172947)
plNext = AddPolyLine_Line_XY(plStart, -88.884505, -41.446918)
plNext = AddPolyLine_Line_XY(plNext, -86.99151, -45.285534)
plNext = AddPolyLine_Line_XY(plNext, -84.408151, -44.011562)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b22


# Create new component armature_winding_active_b21
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b21", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-80.319207, -51.093822)
plNext = AddPolyLine_Line_XY(plStart, -82.714177, -52.69409)
plNext = AddPolyLine_Line_XY(plNext, -80.336337, -56.25278)
plNext = AddPolyLine_Line_XY(plNext, -77.941366, -54.652512)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b21


# Create new component armature_winding_active_b20
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b20", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-72.962983, -61.140467)
plNext = AddPolyLine_Line_XY(plStart, -75.128587, -63.039652)
plNext = AddPolyLine_Line_XY(plNext, -72.306587, -66.257526)
plNext = AddPolyLine_Line_XY(plNext, -70.140983, -64.358342)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b20


# Create new component armature_winding_active_b19
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b19", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-64.358342, -70.140983)
plNext = AddPolyLine_Line_XY(plStart, -66.257526, -72.306587)
plNext = AddPolyLine_Line_XY(plNext, -63.039652, -75.128587)
plNext = AddPolyLine_Line_XY(plNext, -61.140467, -72.962983)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b19


# Create new component armature_winding_active_b18
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b18", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-54.652512, -77.941366)
plNext = AddPolyLine_Line_XY(plStart, -56.25278, -80.336337)
plNext = AddPolyLine_Line_XY(plNext, -52.69409, -82.714177)
plNext = AddPolyLine_Line_XY(plNext, -51.093822, -80.319207)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b18


# Create new component armature_winding_active_b17
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b17", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-44.011562, -84.408151)
plNext = AddPolyLine_Line_XY(plStart, -45.285534, -86.99151)
plNext = AddPolyLine_Line_XY(plNext, -41.446918, -88.884505)
plNext = AddPolyLine_Line_XY(plNext, -40.172947, -86.301147)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b17


# Create new component armature_winding_active_b16
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b16", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-32.617563, -89.430689)
plNext = AddPolyLine_Line_XY(plStart, -33.543439, -92.158233)
plNext = AddPolyLine_Line_XY(plNext, -29.490578, -93.533994)
plNext = AddPolyLine_Line_XY(plNext, -28.564702, -90.80645)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b16


# Create new component armature_winding_active_b15
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b15", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-20.665468, -92.923044)
plNext = AddPolyLine_Line_XY(plStart, -21.227407, -95.748104)
plNext = AddPolyLine_Line_XY(plNext, -17.029646, -96.583091)
plNext = AddPolyLine_Line_XY(plNext, -16.467707, -93.75803)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b15


# Create new component armature_winding_active_b14
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b14", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-8.359781, -94.825459)
plNext = AddPolyLine_Line_XY(plStart, -8.548168, -97.699699)
plNext = AddPolyLine_Line_XY(plNext, -4.277332, -97.979624)
plNext = AddPolyLine_Line_XY(plNext, -4.088944, -95.105384)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b14


# Create new component armature_winding_active_b13
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b13", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(4.088944, -95.105384)
plNext = AddPolyLine_Line_XY(plStart, 4.277332, -97.979624)
plNext = AddPolyLine_Line_XY(plNext, 8.548168, -97.699699)
plNext = AddPolyLine_Line_XY(plNext, 8.359781, -94.825459)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b13


# Create new component armature_winding_active_b12
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b12", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(16.467707, -93.75803)
plNext = AddPolyLine_Line_XY(plStart, 17.029646, -96.583091)
plNext = AddPolyLine_Line_XY(plNext, 21.227407, -95.748104)
plNext = AddPolyLine_Line_XY(plNext, 20.665468, -92.923044)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b12


# Create new component armature_winding_active_b11
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b11", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(28.564702, -90.80645)
plNext = AddPolyLine_Line_XY(plStart, 29.490578, -93.533994)
plNext = AddPolyLine_Line_XY(plNext, 33.543439, -92.158233)
plNext = AddPolyLine_Line_XY(plNext, 32.617563, -89.430689)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b11


# Create new component armature_winding_active_b10
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b10", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(40.172947, -86.301147)
plNext = AddPolyLine_Line_XY(plStart, 41.446918, -88.884505)
plNext = AddPolyLine_Line_XY(plNext, 45.285534, -86.99151)
plNext = AddPolyLine_Line_XY(plNext, 44.011562, -84.408151)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b10


# Create new component armature_winding_active_b9
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b9", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(51.093822, -80.319207)
plNext = AddPolyLine_Line_XY(plStart, 52.69409, -82.714177)
plNext = AddPolyLine_Line_XY(plNext, 56.25278, -80.336337)
plNext = AddPolyLine_Line_XY(plNext, 54.652512, -77.941366)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b9


# Create new component armature_winding_active_b8
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b8", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(61.140467, -72.962983)
plNext = AddPolyLine_Line_XY(plStart, 63.039652, -75.128587)
plNext = AddPolyLine_Line_XY(plNext, 66.257526, -72.306587)
plNext = AddPolyLine_Line_XY(plNext, 64.358342, -70.140983)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b8


# Create new component armature_winding_active_b7
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b7", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(70.140983, -64.358342)
plNext = AddPolyLine_Line_XY(plStart, 72.306587, -66.257526)
plNext = AddPolyLine_Line_XY(plNext, 75.128587, -63.039652)
plNext = AddPolyLine_Line_XY(plNext, 72.962983, -61.140467)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b7


# Create new component armature_winding_active_b6
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b6", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(77.941366, -54.652512)
plNext = AddPolyLine_Line_XY(plStart, 80.336337, -56.25278)
plNext = AddPolyLine_Line_XY(plNext, 82.714177, -52.69409)
plNext = AddPolyLine_Line_XY(plNext, 80.319207, -51.093822)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b6


# Create new component armature_winding_active_b5
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b5", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(84.408151, -44.011562)
plNext = AddPolyLine_Line_XY(plStart, 86.99151, -45.285534)
plNext = AddPolyLine_Line_XY(plNext, 88.884505, -41.446918)
plNext = AddPolyLine_Line_XY(plNext, 86.301147, -40.172947)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b5


# Create new component armature_winding_active_b4
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b4", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(89.430689, -32.617563)
plNext = AddPolyLine_Line_XY(plStart, 92.158233, -33.543439)
plNext = AddPolyLine_Line_XY(plNext, 93.533994, -29.490578)
plNext = AddPolyLine_Line_XY(plNext, 90.80645, -28.564702)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b4


# Create new component armature_winding_active_b3
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b3", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(92.923044, -20.665468)
plNext = AddPolyLine_Line_XY(plStart, 95.748104, -21.227407)
plNext = AddPolyLine_Line_XY(plNext, 96.583091, -17.029646)
plNext = AddPolyLine_Line_XY(plNext, 93.75803, -16.467707)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b3


# Create new component armature_winding_active_b2
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_b2", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(94.825459, -8.359781)
plNext = AddPolyLine_Line_XY(plStart, 97.699699, -8.548168)
plNext = AddPolyLine_Line_XY(plNext, 97.979624, -4.277332)
plNext = AddPolyLine_Line_XY(plNext, 95.105384, -4.088944)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_b2


# Create new component armature_winding_active_a48
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a48", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(96.583091, 17.029646)
plNext = AddPolyLine_Line_XY(plStart, 99.408152, 17.591586)
plNext = AddPolyLine_Line_XY(plNext, 98.990658, 19.690466)
plNext = AddPolyLine_Line_XY(plNext, 98.573165, 21.789347)
plNext = AddPolyLine_Line_XY(plNext, 95.748104, 21.227407)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a48


# Create new component armature_winding_active_a47
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a47", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(93.533994, 29.490578)
plNext = AddPolyLine_Line_XY(plStart, 96.261538, 30.416455)
plNext = AddPolyLine_Line_XY(plNext, 95.573658, 32.442885)
plNext = AddPolyLine_Line_XY(plNext, 94.885778, 34.469316)
plNext = AddPolyLine_Line_XY(plNext, 92.158233, 33.543439)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a47


# Create new component armature_winding_active_a46
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a46", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(88.884505, 41.446918)
plNext = AddPolyLine_Line_XY(plStart, 91.467864, 42.72089)
plNext = AddPolyLine_Line_XY(plNext, 90.521366, 44.640198)
plNext = AddPolyLine_Line_XY(plNext, 89.574868, 46.559505)
plNext = AddPolyLine_Line_XY(plNext, 86.99151, 45.285534)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a46


# Create new component armature_winding_active_a45
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a45", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(82.714177, 52.69409)
plNext = AddPolyLine_Line_XY(plStart, 85.109148, 54.294359)
plNext = AddPolyLine_Line_XY(plNext, 83.920228, 56.073704)
plNext = AddPolyLine_Line_XY(plNext, 82.731308, 57.853049)
plNext = AddPolyLine_Line_XY(plNext, 80.336337, 56.25278)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a45


# Create new component armature_winding_active_a44
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a44", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(75.128587, 63.039652)
plNext = AddPolyLine_Line_XY(plStart, 77.294192, 64.938836)
plNext = AddPolyLine_Line_XY(plNext, 75.883192, 66.547773)
plNext = AddPolyLine_Line_XY(plNext, 74.472192, 68.15671)
plNext = AddPolyLine_Line_XY(plNext, 72.306587, 66.257526)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a44


# Create new component armature_winding_active_a43
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a43", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(66.257526, 72.306587)
plNext = AddPolyLine_Line_XY(plStart, 68.15671, 74.472192)
plNext = AddPolyLine_Line_XY(plNext, 66.547773, 75.883192)
plNext = AddPolyLine_Line_XY(plNext, 64.938836, 77.294192)
plNext = AddPolyLine_Line_XY(plNext, 63.039652, 75.128587)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a43


# Create new component armature_winding_active_a42
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a42", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(56.25278, 80.336337)
plNext = AddPolyLine_Line_XY(plStart, 57.853049, 82.731308)
plNext = AddPolyLine_Line_XY(plNext, 56.073704, 83.920228)
plNext = AddPolyLine_Line_XY(plNext, 54.294359, 85.109148)
plNext = AddPolyLine_Line_XY(plNext, 52.69409, 82.714177)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a42


# Create new component armature_winding_active_a41
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a41", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(45.285534, 86.99151)
plNext = AddPolyLine_Line_XY(plStart, 46.559505, 89.574868)
plNext = AddPolyLine_Line_XY(plNext, 44.640198, 90.521366)
plNext = AddPolyLine_Line_XY(plNext, 42.72089, 91.467864)
plNext = AddPolyLine_Line_XY(plNext, 41.446918, 88.884505)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a41


# Create new component armature_winding_active_a40
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a40", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(33.543439, 92.158233)
plNext = AddPolyLine_Line_XY(plStart, 34.469316, 94.885778)
plNext = AddPolyLine_Line_XY(plNext, 32.442885, 95.573658)
plNext = AddPolyLine_Line_XY(plNext, 30.416455, 96.261538)
plNext = AddPolyLine_Line_XY(plNext, 29.490578, 93.533994)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a40


# Create new component armature_winding_active_a39
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a39", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(21.227407, 95.748104)
plNext = AddPolyLine_Line_XY(plStart, 21.789347, 98.573165)
plNext = AddPolyLine_Line_XY(plNext, 19.690466, 98.990658)
plNext = AddPolyLine_Line_XY(plNext, 17.591586, 99.408152)
plNext = AddPolyLine_Line_XY(plNext, 17.029646, 96.583091)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a39


# Create new component armature_winding_active_a38
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a38", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(8.548168, 97.699699)
plNext = AddPolyLine_Line_XY(plStart, 8.736556, 100.573938)
plNext = AddPolyLine_Line_XY(plNext, 6.601138, 100.713901)
plNext = AddPolyLine_Line_XY(plNext, 4.46572, 100.853864)
plNext = AddPolyLine_Line_XY(plNext, 4.277332, 97.979624)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a38


# Create new component armature_winding_active_a37
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a37", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-4.277332, 97.979624)
plNext = AddPolyLine_Line_XY(plStart, -4.46572, 100.853864)
plNext = AddPolyLine_Line_XY(plNext, -6.601138, 100.713901)
plNext = AddPolyLine_Line_XY(plNext, -8.736556, 100.573938)
plNext = AddPolyLine_Line_XY(plNext, -8.548168, 97.699699)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a37


# Create new component armature_winding_active_a36
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a36", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-17.029646, 96.583091)
plNext = AddPolyLine_Line_XY(plStart, -17.591586, 99.408152)
plNext = AddPolyLine_Line_XY(plNext, -19.690466, 98.990658)
plNext = AddPolyLine_Line_XY(plNext, -21.789347, 98.573165)
plNext = AddPolyLine_Line_XY(plNext, -21.227407, 95.748104)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a36


# Create new component armature_winding_active_a35
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a35", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-29.490578, 93.533994)
plNext = AddPolyLine_Line_XY(plStart, -30.416455, 96.261538)
plNext = AddPolyLine_Line_XY(plNext, -32.442885, 95.573658)
plNext = AddPolyLine_Line_XY(plNext, -34.469316, 94.885778)
plNext = AddPolyLine_Line_XY(plNext, -33.543439, 92.158233)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a35


# Create new component armature_winding_active_a34
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a34", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-41.446918, 88.884505)
plNext = AddPolyLine_Line_XY(plStart, -42.72089, 91.467864)
plNext = AddPolyLine_Line_XY(plNext, -44.640198, 90.521366)
plNext = AddPolyLine_Line_XY(plNext, -46.559505, 89.574868)
plNext = AddPolyLine_Line_XY(plNext, -45.285534, 86.99151)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a34


# Create new component armature_winding_active_a33
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a33", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-52.69409, 82.714177)
plNext = AddPolyLine_Line_XY(plStart, -54.294359, 85.109148)
plNext = AddPolyLine_Line_XY(plNext, -56.073704, 83.920228)
plNext = AddPolyLine_Line_XY(plNext, -57.853049, 82.731308)
plNext = AddPolyLine_Line_XY(plNext, -56.25278, 80.336337)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a33


# Create new component armature_winding_active_a32
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a32", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-63.039652, 75.128587)
plNext = AddPolyLine_Line_XY(plStart, -64.938836, 77.294192)
plNext = AddPolyLine_Line_XY(plNext, -66.547773, 75.883192)
plNext = AddPolyLine_Line_XY(plNext, -68.15671, 74.472192)
plNext = AddPolyLine_Line_XY(plNext, -66.257526, 72.306587)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a32


# Create new component armature_winding_active_a31
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a31", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-72.306587, 66.257526)
plNext = AddPolyLine_Line_XY(plStart, -74.472192, 68.15671)
plNext = AddPolyLine_Line_XY(plNext, -75.883192, 66.547773)
plNext = AddPolyLine_Line_XY(plNext, -77.294192, 64.938836)
plNext = AddPolyLine_Line_XY(plNext, -75.128587, 63.039652)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a31


# Create new component armature_winding_active_a30
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a30", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-80.336337, 56.25278)
plNext = AddPolyLine_Line_XY(plStart, -82.731308, 57.853049)
plNext = AddPolyLine_Line_XY(plNext, -83.920228, 56.073704)
plNext = AddPolyLine_Line_XY(plNext, -85.109148, 54.294359)
plNext = AddPolyLine_Line_XY(plNext, -82.714177, 52.69409)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a30


# Create new component armature_winding_active_a29
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a29", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-86.99151, 45.285534)
plNext = AddPolyLine_Line_XY(plStart, -89.574868, 46.559505)
plNext = AddPolyLine_Line_XY(plNext, -90.521366, 44.640198)
plNext = AddPolyLine_Line_XY(plNext, -91.467864, 42.72089)
plNext = AddPolyLine_Line_XY(plNext, -88.884505, 41.446918)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a29


# Create new component armature_winding_active_a28
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a28", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-92.158233, 33.543439)
plNext = AddPolyLine_Line_XY(plStart, -94.885778, 34.469316)
plNext = AddPolyLine_Line_XY(plNext, -95.573658, 32.442885)
plNext = AddPolyLine_Line_XY(plNext, -96.261538, 30.416455)
plNext = AddPolyLine_Line_XY(plNext, -93.533994, 29.490578)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a28


# Create new component armature_winding_active_a27
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a27", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-95.748104, 21.227407)
plNext = AddPolyLine_Line_XY(plStart, -98.573165, 21.789347)
plNext = AddPolyLine_Line_XY(plNext, -98.990658, 19.690466)
plNext = AddPolyLine_Line_XY(plNext, -99.408152, 17.591586)
plNext = AddPolyLine_Line_XY(plNext, -96.583091, 17.029646)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a27


# Create new component armature_winding_active_a26
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a26", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-97.699699, 8.548168)
plNext = AddPolyLine_Line_XY(plStart, -100.573938, 8.736556)
plNext = AddPolyLine_Line_XY(plNext, -100.713901, 6.601138)
plNext = AddPolyLine_Line_XY(plNext, -100.853864, 4.46572)
plNext = AddPolyLine_Line_XY(plNext, -97.979624, 4.277332)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a26


# Create new component armature_winding_active_a25
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a25", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-97.979624, -4.277332)
plNext = AddPolyLine_Line_XY(plStart, -100.853864, -4.46572)
plNext = AddPolyLine_Line_XY(plNext, -100.713901, -6.601138)
plNext = AddPolyLine_Line_XY(plNext, -100.573938, -8.736556)
plNext = AddPolyLine_Line_XY(plNext, -97.699699, -8.548168)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a25


# Create new component armature_winding_active_a24
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a24", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-96.583091, -17.029646)
plNext = AddPolyLine_Line_XY(plStart, -99.408152, -17.591586)
plNext = AddPolyLine_Line_XY(plNext, -98.990658, -19.690466)
plNext = AddPolyLine_Line_XY(plNext, -98.573165, -21.789347)
plNext = AddPolyLine_Line_XY(plNext, -95.748104, -21.227407)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a24


# Create new component armature_winding_active_a23
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a23", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-93.533994, -29.490578)
plNext = AddPolyLine_Line_XY(plStart, -96.261538, -30.416455)
plNext = AddPolyLine_Line_XY(plNext, -95.573658, -32.442885)
plNext = AddPolyLine_Line_XY(plNext, -94.885778, -34.469316)
plNext = AddPolyLine_Line_XY(plNext, -92.158233, -33.543439)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a23


# Create new component armature_winding_active_a22
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a22", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-88.884505, -41.446918)
plNext = AddPolyLine_Line_XY(plStart, -91.467864, -42.72089)
plNext = AddPolyLine_Line_XY(plNext, -90.521366, -44.640198)
plNext = AddPolyLine_Line_XY(plNext, -89.574868, -46.559505)
plNext = AddPolyLine_Line_XY(plNext, -86.99151, -45.285534)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a22


# Create new component armature_winding_active_a21
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a21", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-82.714177, -52.69409)
plNext = AddPolyLine_Line_XY(plStart, -85.109148, -54.294359)
plNext = AddPolyLine_Line_XY(plNext, -83.920228, -56.073704)
plNext = AddPolyLine_Line_XY(plNext, -82.731308, -57.853049)
plNext = AddPolyLine_Line_XY(plNext, -80.336337, -56.25278)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a21


# Create new component armature_winding_active_a20
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a20", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-75.128587, -63.039652)
plNext = AddPolyLine_Line_XY(plStart, -77.294192, -64.938836)
plNext = AddPolyLine_Line_XY(plNext, -75.883192, -66.547773)
plNext = AddPolyLine_Line_XY(plNext, -74.472192, -68.15671)
plNext = AddPolyLine_Line_XY(plNext, -72.306587, -66.257526)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a20


# Create new component armature_winding_active_a19
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a19", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-66.257526, -72.306587)
plNext = AddPolyLine_Line_XY(plStart, -68.15671, -74.472192)
plNext = AddPolyLine_Line_XY(plNext, -66.547773, -75.883192)
plNext = AddPolyLine_Line_XY(plNext, -64.938836, -77.294192)
plNext = AddPolyLine_Line_XY(plNext, -63.039652, -75.128587)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a19


# Create new component armature_winding_active_a18
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a18", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-56.25278, -80.336337)
plNext = AddPolyLine_Line_XY(plStart, -57.853049, -82.731308)
plNext = AddPolyLine_Line_XY(plNext, -56.073704, -83.920228)
plNext = AddPolyLine_Line_XY(plNext, -54.294359, -85.109148)
plNext = AddPolyLine_Line_XY(plNext, -52.69409, -82.714177)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a18


# Create new component armature_winding_active_a17
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a17", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-45.285534, -86.99151)
plNext = AddPolyLine_Line_XY(plStart, -46.559505, -89.574868)
plNext = AddPolyLine_Line_XY(plNext, -44.640198, -90.521366)
plNext = AddPolyLine_Line_XY(plNext, -42.72089, -91.467864)
plNext = AddPolyLine_Line_XY(plNext, -41.446918, -88.884505)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a17


# Create new component armature_winding_active_a16
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a16", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-33.543439, -92.158233)
plNext = AddPolyLine_Line_XY(plStart, -34.469316, -94.885778)
plNext = AddPolyLine_Line_XY(plNext, -32.442885, -95.573658)
plNext = AddPolyLine_Line_XY(plNext, -30.416455, -96.261538)
plNext = AddPolyLine_Line_XY(plNext, -29.490578, -93.533994)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a16


# Create new component armature_winding_active_a15
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a15", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-21.227407, -95.748104)
plNext = AddPolyLine_Line_XY(plStart, -21.789347, -98.573165)
plNext = AddPolyLine_Line_XY(plNext, -19.690466, -98.990658)
plNext = AddPolyLine_Line_XY(plNext, -17.591586, -99.408152)
plNext = AddPolyLine_Line_XY(plNext, -17.029646, -96.583091)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a15


# Create new component armature_winding_active_a14
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a14", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-8.548168, -97.699699)
plNext = AddPolyLine_Line_XY(plStart, -8.736556, -100.573938)
plNext = AddPolyLine_Line_XY(plNext, -6.601138, -100.713901)
plNext = AddPolyLine_Line_XY(plNext, -4.46572, -100.853864)
plNext = AddPolyLine_Line_XY(plNext, -4.277332, -97.979624)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a14


# Create new component armature_winding_active_a13
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a13", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(4.277332, -97.979624)
plNext = AddPolyLine_Line_XY(plStart, 4.46572, -100.853864)
plNext = AddPolyLine_Line_XY(plNext, 6.601138, -100.713901)
plNext = AddPolyLine_Line_XY(plNext, 8.736556, -100.573938)
plNext = AddPolyLine_Line_XY(plNext, 8.548168, -97.699699)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a13


# Create new component armature_winding_active_a12
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a12", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(17.029646, -96.583091)
plNext = AddPolyLine_Line_XY(plStart, 17.591586, -99.408152)
plNext = AddPolyLine_Line_XY(plNext, 19.690466, -98.990658)
plNext = AddPolyLine_Line_XY(plNext, 21.789347, -98.573165)
plNext = AddPolyLine_Line_XY(plNext, 21.227407, -95.748104)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a12


# Create new component armature_winding_active_a11
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a11", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(29.490578, -93.533994)
plNext = AddPolyLine_Line_XY(plStart, 30.416455, -96.261538)
plNext = AddPolyLine_Line_XY(plNext, 32.442885, -95.573658)
plNext = AddPolyLine_Line_XY(plNext, 34.469316, -94.885778)
plNext = AddPolyLine_Line_XY(plNext, 33.543439, -92.158233)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a11


# Create new component armature_winding_active_a10
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a10", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(41.446918, -88.884505)
plNext = AddPolyLine_Line_XY(plStart, 42.72089, -91.467864)
plNext = AddPolyLine_Line_XY(plNext, 44.640198, -90.521366)
plNext = AddPolyLine_Line_XY(plNext, 46.559505, -89.574868)
plNext = AddPolyLine_Line_XY(plNext, 45.285534, -86.99151)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a10


# Create new component armature_winding_active_a9
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a9", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(52.69409, -82.714177)
plNext = AddPolyLine_Line_XY(plStart, 54.294359, -85.109148)
plNext = AddPolyLine_Line_XY(plNext, 56.073704, -83.920228)
plNext = AddPolyLine_Line_XY(plNext, 57.853049, -82.731308)
plNext = AddPolyLine_Line_XY(plNext, 56.25278, -80.336337)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a9


# Create new component armature_winding_active_a8
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a8", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(63.039652, -75.128587)
plNext = AddPolyLine_Line_XY(plStart, 64.938836, -77.294192)
plNext = AddPolyLine_Line_XY(plNext, 66.547773, -75.883192)
plNext = AddPolyLine_Line_XY(plNext, 68.15671, -74.472192)
plNext = AddPolyLine_Line_XY(plNext, 66.257526, -72.306587)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a8


# Create new component armature_winding_active_a7
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a7", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(72.306587, -66.257526)
plNext = AddPolyLine_Line_XY(plStart, 74.472192, -68.15671)
plNext = AddPolyLine_Line_XY(plNext, 75.883192, -66.547773)
plNext = AddPolyLine_Line_XY(plNext, 77.294192, -64.938836)
plNext = AddPolyLine_Line_XY(plNext, 75.128587, -63.039652)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a7


# Create new component armature_winding_active_a6
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a6", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(80.336337, -56.25278)
plNext = AddPolyLine_Line_XY(plStart, 82.731308, -57.853049)
plNext = AddPolyLine_Line_XY(plNext, 83.920228, -56.073704)
plNext = AddPolyLine_Line_XY(plNext, 85.109148, -54.294359)
plNext = AddPolyLine_Line_XY(plNext, 82.714177, -52.69409)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a6


# Create new component armature_winding_active_a5
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a5", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(86.99151, -45.285534)
plNext = AddPolyLine_Line_XY(plStart, 89.574868, -46.559505)
plNext = AddPolyLine_Line_XY(plNext, 90.521366, -44.640198)
plNext = AddPolyLine_Line_XY(plNext, 91.467864, -42.72089)
plNext = AddPolyLine_Line_XY(plNext, 88.884505, -41.446918)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a5


# Create new component armature_winding_active_a4
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a4", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(92.158233, -33.543439)
plNext = AddPolyLine_Line_XY(plStart, 94.885778, -34.469316)
plNext = AddPolyLine_Line_XY(plNext, 95.573658, -32.442885)
plNext = AddPolyLine_Line_XY(plNext, 96.261538, -30.416455)
plNext = AddPolyLine_Line_XY(plNext, 93.533994, -29.490578)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a4


# Create new component armature_winding_active_a3
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a3", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(95.748104, -21.227407)
plNext = AddPolyLine_Line_XY(plStart, 98.573165, -21.789347)
plNext = AddPolyLine_Line_XY(plNext, 98.990658, -19.690466)
plNext = AddPolyLine_Line_XY(plNext, 99.408152, -17.591586)
plNext = AddPolyLine_Line_XY(plNext, 96.583091, -17.029646)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a3


# Create new component armature_winding_active_a2
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_a2", -54.5, -96, 255, 255, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(97.699699, -8.548168)
plNext = AddPolyLine_Line_XY(plStart, 100.573938, -8.736556)
plNext = AddPolyLine_Line_XY(plNext, 100.713901, -6.601138)
plNext = AddPolyLine_Line_XY(plNext, 100.853864, -4.46572)
plNext = AddPolyLine_Line_XY(plNext, 97.979624, -4.277332)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_a2


# Create new component armature_winding_active_h48
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h48", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(79.632727, 13.658009)
plNext = AddPolyLine_Line_XY(plStart, 78.79774, 17.85577)
plNext = AddPolyLine_Line_XY(plNext, 75.972679, 17.293831)
plNext = AddPolyLine_Line_XY(plNext, 76.807666, 13.09607)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h48


# Create new component armature_winding_active_h47
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h47", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(77.16873, 23.93532)
plNext = AddPolyLine_Line_XY(plStart, 75.792969, 27.988181)
plNext = AddPolyLine_Line_XY(plNext, 73.065425, 27.062304)
plNext = AddPolyLine_Line_XY(plNext, 74.441186, 23.009443)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h47


# Create new component armature_winding_active_h46
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h46", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(73.384354, 33.80309)
plNext = AddPolyLine_Line_XY(plStart, 71.491359, 37.641705)
plNext = AddPolyLine_Line_XY(plNext, 68.908, 36.367734)
plNext = AddPolyLine_Line_XY(plNext, 70.800996, 32.529119)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h46


# Create new component armature_winding_active_h45
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h45", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(68.344353, 43.09248)
plNext = AddPolyLine_Line_XY(plStart, 65.966512, 46.65117)
plNext = AddPolyLine_Line_XY(plNext, 63.571541, 45.050902)
plNext = AddPolyLine_Line_XY(plNext, 65.949382, 41.492212)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h45


# Create new component armature_winding_active_h44
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h44", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(62.13496, 51.644546)
plNext = AddPolyLine_Line_XY(plStart, 59.31296, 54.862421)
plNext = AddPolyLine_Line_XY(plNext, 57.147355, 52.963236)
plNext = AddPolyLine_Line_XY(plNext, 59.969355, 49.745362)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h44


# Create new component armature_winding_active_h43
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h43", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(54.862421, 59.31296)
plNext = AddPolyLine_Line_XY(plStart, 51.644546, 62.13496)
plNext = AddPolyLine_Line_XY(plNext, 49.745362, 59.969355)
plNext = AddPolyLine_Line_XY(plNext, 52.963236, 57.147355)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h43


# Create new component armature_winding_active_h42
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h42", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(46.65117, 65.966512)
plNext = AddPolyLine_Line_XY(plStart, 43.09248, 68.344353)
plNext = AddPolyLine_Line_XY(plNext, 41.492212, 65.949382)
plNext = AddPolyLine_Line_XY(plNext, 45.050902, 63.571541)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h42


# Create new component armature_winding_active_h41
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h41", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(37.641705, 71.491359)
plNext = AddPolyLine_Line_XY(plStart, 33.80309, 73.384354)
plNext = AddPolyLine_Line_XY(plNext, 32.529119, 70.800996)
plNext = AddPolyLine_Line_XY(plNext, 36.367734, 68.908)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h41


# Create new component armature_winding_active_h40
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h40", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(27.988181, 75.792969)
plNext = AddPolyLine_Line_XY(plStart, 23.93532, 77.16873)
plNext = AddPolyLine_Line_XY(plNext, 23.009443, 74.441186)
plNext = AddPolyLine_Line_XY(plNext, 27.062304, 73.065425)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h40


# Create new component armature_winding_active_h39
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h39", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(17.85577, 78.79774)
plNext = AddPolyLine_Line_XY(plStart, 13.658009, 79.632727)
plNext = AddPolyLine_Line_XY(plNext, 13.09607, 76.807666)
plNext = AddPolyLine_Line_XY(plNext, 17.293831, 75.972679)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h39


# Create new component armature_winding_active_h38
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h38", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(7.417843, 80.45426)
plNext = AddPolyLine_Line_XY(plStart, 3.147006, 80.734186)
plNext = AddPolyLine_Line_XY(plNext, 2.958619, 77.859946)
plNext = AddPolyLine_Line_XY(plNext, 7.229455, 77.580021)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h38


# Create new component armature_winding_active_h37
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h37", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-3.147006, 80.734186)
plNext = AddPolyLine_Line_XY(plStart, -7.417843, 80.45426)
plNext = AddPolyLine_Line_XY(plNext, -7.229455, 77.580021)
plNext = AddPolyLine_Line_XY(plNext, -2.958619, 77.859946)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h37


# Create new component armature_winding_active_h36
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h36", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-13.658009, 79.632727)
plNext = AddPolyLine_Line_XY(plStart, -17.85577, 78.79774)
plNext = AddPolyLine_Line_XY(plNext, -17.293831, 75.972679)
plNext = AddPolyLine_Line_XY(plNext, -13.09607, 76.807666)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h36


# Create new component armature_winding_active_h35
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h35", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-23.93532, 77.16873)
plNext = AddPolyLine_Line_XY(plStart, -27.988181, 75.792969)
plNext = AddPolyLine_Line_XY(plNext, -27.062304, 73.065425)
plNext = AddPolyLine_Line_XY(plNext, -23.009443, 74.441186)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h35


# Create new component armature_winding_active_h34
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h34", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-33.80309, 73.384354)
plNext = AddPolyLine_Line_XY(plStart, -37.641705, 71.491359)
plNext = AddPolyLine_Line_XY(plNext, -36.367734, 68.908)
plNext = AddPolyLine_Line_XY(plNext, -32.529119, 70.800996)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h34


# Create new component armature_winding_active_h33
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h33", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-43.09248, 68.344353)
plNext = AddPolyLine_Line_XY(plStart, -46.65117, 65.966512)
plNext = AddPolyLine_Line_XY(plNext, -45.050902, 63.571541)
plNext = AddPolyLine_Line_XY(plNext, -41.492212, 65.949382)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h33


# Create new component armature_winding_active_h32
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h32", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-51.644546, 62.13496)
plNext = AddPolyLine_Line_XY(plStart, -54.862421, 59.31296)
plNext = AddPolyLine_Line_XY(plNext, -52.963236, 57.147355)
plNext = AddPolyLine_Line_XY(plNext, -49.745362, 59.969355)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h32


# Create new component armature_winding_active_h31
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h31", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-59.31296, 54.862421)
plNext = AddPolyLine_Line_XY(plStart, -62.13496, 51.644546)
plNext = AddPolyLine_Line_XY(plNext, -59.969355, 49.745362)
plNext = AddPolyLine_Line_XY(plNext, -57.147355, 52.963236)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h31


# Create new component armature_winding_active_h30
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h30", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-65.966512, 46.65117)
plNext = AddPolyLine_Line_XY(plStart, -68.344353, 43.09248)
plNext = AddPolyLine_Line_XY(plNext, -65.949382, 41.492212)
plNext = AddPolyLine_Line_XY(plNext, -63.571541, 45.050902)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h30


# Create new component armature_winding_active_h29
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h29", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-71.491359, 37.641705)
plNext = AddPolyLine_Line_XY(plStart, -73.384354, 33.80309)
plNext = AddPolyLine_Line_XY(plNext, -70.800996, 32.529119)
plNext = AddPolyLine_Line_XY(plNext, -68.908, 36.367734)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h29


# Create new component armature_winding_active_h28
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h28", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-75.792969, 27.988181)
plNext = AddPolyLine_Line_XY(plStart, -77.16873, 23.93532)
plNext = AddPolyLine_Line_XY(plNext, -74.441186, 23.009443)
plNext = AddPolyLine_Line_XY(plNext, -73.065425, 27.062304)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h28


# Create new component armature_winding_active_h27
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h27", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-78.79774, 17.85577)
plNext = AddPolyLine_Line_XY(plStart, -79.632727, 13.658009)
plNext = AddPolyLine_Line_XY(plNext, -76.807666, 13.09607)
plNext = AddPolyLine_Line_XY(plNext, -75.972679, 17.293831)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h27


# Create new component armature_winding_active_h26
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h26", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-80.45426, 7.417843)
plNext = AddPolyLine_Line_XY(plStart, -80.734186, 3.147006)
plNext = AddPolyLine_Line_XY(plNext, -77.859946, 2.958619)
plNext = AddPolyLine_Line_XY(plNext, -77.580021, 7.229455)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h26


# Create new component armature_winding_active_h25
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h25", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-80.734186, -3.147006)
plNext = AddPolyLine_Line_XY(plStart, -80.45426, -7.417843)
plNext = AddPolyLine_Line_XY(plNext, -77.580021, -7.229455)
plNext = AddPolyLine_Line_XY(plNext, -77.859946, -2.958619)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h25


# Create new component armature_winding_active_h24
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h24", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-79.632727, -13.658009)
plNext = AddPolyLine_Line_XY(plStart, -78.79774, -17.85577)
plNext = AddPolyLine_Line_XY(plNext, -75.972679, -17.293831)
plNext = AddPolyLine_Line_XY(plNext, -76.807666, -13.09607)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h24


# Create new component armature_winding_active_h23
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h23", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-77.16873, -23.93532)
plNext = AddPolyLine_Line_XY(plStart, -75.792969, -27.988181)
plNext = AddPolyLine_Line_XY(plNext, -73.065425, -27.062304)
plNext = AddPolyLine_Line_XY(plNext, -74.441186, -23.009443)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h23


# Create new component armature_winding_active_h22
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h22", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-73.384354, -33.80309)
plNext = AddPolyLine_Line_XY(plStart, -71.491359, -37.641705)
plNext = AddPolyLine_Line_XY(plNext, -68.908, -36.367734)
plNext = AddPolyLine_Line_XY(plNext, -70.800996, -32.529119)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h22


# Create new component armature_winding_active_h21
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h21", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-68.344353, -43.09248)
plNext = AddPolyLine_Line_XY(plStart, -65.966512, -46.65117)
plNext = AddPolyLine_Line_XY(plNext, -63.571541, -45.050902)
plNext = AddPolyLine_Line_XY(plNext, -65.949382, -41.492212)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h21


# Create new component armature_winding_active_h20
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h20", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-62.13496, -51.644546)
plNext = AddPolyLine_Line_XY(plStart, -59.31296, -54.862421)
plNext = AddPolyLine_Line_XY(plNext, -57.147355, -52.963236)
plNext = AddPolyLine_Line_XY(plNext, -59.969355, -49.745362)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h20


# Create new component armature_winding_active_h19
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h19", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-54.862421, -59.31296)
plNext = AddPolyLine_Line_XY(plStart, -51.644546, -62.13496)
plNext = AddPolyLine_Line_XY(plNext, -49.745362, -59.969355)
plNext = AddPolyLine_Line_XY(plNext, -52.963236, -57.147355)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h19


# Create new component armature_winding_active_h18
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h18", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-46.65117, -65.966512)
plNext = AddPolyLine_Line_XY(plStart, -43.09248, -68.344353)
plNext = AddPolyLine_Line_XY(plNext, -41.492212, -65.949382)
plNext = AddPolyLine_Line_XY(plNext, -45.050902, -63.571541)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h18


# Create new component armature_winding_active_h17
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h17", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-37.641705, -71.491359)
plNext = AddPolyLine_Line_XY(plStart, -33.80309, -73.384354)
plNext = AddPolyLine_Line_XY(plNext, -32.529119, -70.800996)
plNext = AddPolyLine_Line_XY(plNext, -36.367734, -68.908)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h17


# Create new component armature_winding_active_h16
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h16", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-27.988181, -75.792969)
plNext = AddPolyLine_Line_XY(plStart, -23.93532, -77.16873)
plNext = AddPolyLine_Line_XY(plNext, -23.009443, -74.441186)
plNext = AddPolyLine_Line_XY(plNext, -27.062304, -73.065425)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h16


# Create new component armature_winding_active_h15
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h15", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-17.85577, -78.79774)
plNext = AddPolyLine_Line_XY(plStart, -13.658009, -79.632727)
plNext = AddPolyLine_Line_XY(plNext, -13.09607, -76.807666)
plNext = AddPolyLine_Line_XY(plNext, -17.293831, -75.972679)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h15


# Create new component armature_winding_active_h14
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h14", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(-7.417843, -80.45426)
plNext = AddPolyLine_Line_XY(plStart, -3.147006, -80.734186)
plNext = AddPolyLine_Line_XY(plNext, -2.958619, -77.859946)
plNext = AddPolyLine_Line_XY(plNext, -7.229455, -77.580021)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h14


# Create new component armature_winding_active_h13
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h13", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(3.147006, -80.734186)
plNext = AddPolyLine_Line_XY(plStart, 7.417843, -80.45426)
plNext = AddPolyLine_Line_XY(plNext, 7.229455, -77.580021)
plNext = AddPolyLine_Line_XY(plNext, 2.958619, -77.859946)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h13


# Create new component armature_winding_active_h12
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h12", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(13.658009, -79.632727)
plNext = AddPolyLine_Line_XY(plStart, 17.85577, -78.79774)
plNext = AddPolyLine_Line_XY(plNext, 17.293831, -75.972679)
plNext = AddPolyLine_Line_XY(plNext, 13.09607, -76.807666)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h12


# Create new component armature_winding_active_h11
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h11", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(23.93532, -77.16873)
plNext = AddPolyLine_Line_XY(plStart, 27.988181, -75.792969)
plNext = AddPolyLine_Line_XY(plNext, 27.062304, -73.065425)
plNext = AddPolyLine_Line_XY(plNext, 23.009443, -74.441186)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h11


# Create new component armature_winding_active_h10
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h10", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(33.80309, -73.384354)
plNext = AddPolyLine_Line_XY(plStart, 37.641705, -71.491359)
plNext = AddPolyLine_Line_XY(plNext, 36.367734, -68.908)
plNext = AddPolyLine_Line_XY(plNext, 32.529119, -70.800996)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h10


# Create new component armature_winding_active_h9
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h9", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(43.09248, -68.344353)
plNext = AddPolyLine_Line_XY(plStart, 46.65117, -65.966512)
plNext = AddPolyLine_Line_XY(plNext, 45.050902, -63.571541)
plNext = AddPolyLine_Line_XY(plNext, 41.492212, -65.949382)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h9


# Create new component armature_winding_active_h8
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h8", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(51.644546, -62.13496)
plNext = AddPolyLine_Line_XY(plStart, 54.862421, -59.31296)
plNext = AddPolyLine_Line_XY(plNext, 52.963236, -57.147355)
plNext = AddPolyLine_Line_XY(plNext, 49.745362, -59.969355)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h8


# Create new component armature_winding_active_h7
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h7", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(59.31296, -54.862421)
plNext = AddPolyLine_Line_XY(plStart, 62.13496, -51.644546)
plNext = AddPolyLine_Line_XY(plNext, 59.969355, -49.745362)
plNext = AddPolyLine_Line_XY(plNext, 57.147355, -52.963236)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h7


# Create new component armature_winding_active_h6
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h6", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(65.966512, -46.65117)
plNext = AddPolyLine_Line_XY(plStart, 68.344353, -43.09248)
plNext = AddPolyLine_Line_XY(plNext, 65.949382, -41.492212)
plNext = AddPolyLine_Line_XY(plNext, 63.571541, -45.050902)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h6


# Create new component armature_winding_active_h5
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h5", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(71.491359, -37.641705)
plNext = AddPolyLine_Line_XY(plStart, 73.384354, -33.80309)
plNext = AddPolyLine_Line_XY(plNext, 70.800996, -32.529119)
plNext = AddPolyLine_Line_XY(plNext, 68.908, -36.367734)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h5


# Create new component armature_winding_active_h4
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h4", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(75.792969, -27.988181)
plNext = AddPolyLine_Line_XY(plStart, 77.16873, -23.93532)
plNext = AddPolyLine_Line_XY(plNext, 74.441186, -23.009443)
plNext = AddPolyLine_Line_XY(plNext, 73.065425, -27.062304)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h4


# Create new component armature_winding_active_h3
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h3", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(78.79774, -17.85577)
plNext = AddPolyLine_Line_XY(plStart, 79.632727, -13.658009)
plNext = AddPolyLine_Line_XY(plNext, 76.807666, -13.09607)
plNext = AddPolyLine_Line_XY(plNext, 75.972679, -17.293831)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h3


# Create new component armature_winding_active_h2
newComp = CreateNamedComponentWithColour_Radial("armature_winding_active_h2", -54.5, -96, 255, 215, 0, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(80.45426, -7.417843)
plNext = AddPolyLine_Line_XY(plStart, 80.734186, -3.147006)
plNext = AddPolyLine_Line_XY(plNext, 77.859946, -2.958619)
plNext = AddPolyLine_Line_XY(plNext, 77.580021, -7.229455)
ClosePolyLine_Line_XY(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_winding_active_h2

# Additional radial non-DXF components
newComp = CreateNamedCylinderComponent("shaft_front", 0, 0, 10, 0, -54.5, 54.5, 160, 160, 160, comp_Rotor)
newComp = CreateNamedCylinderComponent("shaft_rear", 0, 0, 10, 0, -150.5, -49.5, 160, 160, 160, comp_Rotor)
# Axial cross section formed components

# Create new component flange
newComp = CreateNamedComponentWithColour_Axial("flange", 105, 116, 255, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(11, 0)
plNext = AddPolyLine_Line_YZ(plStart, 22.5, 0)
plNext = AddPolyLine_Line_YZ(plNext, 76, 0)
plNext = AddPolyLine_Line_YZ(plNext, 76, 30)
plNext = AddPolyLine_Line_YZ(plNext, 11, 30)
ClosePolyLine_Line_YZ(plNext, plStart)
# End of Outline 1 PolyLine

# End of component flange


# Create new component bearing_front
newComp = CreateNamedComponentWithColour_Axial("bearing_front", 176, 192, 192, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(11, 0)
plNext = AddPolyLine_Line_YZ(plStart, 10, 0)
plNext = AddPolyLine_Line_YZ(plNext, 10, -12)
plNext = AddPolyLine_Line_YZ(plNext, 22.5, -12)
plNext = AddPolyLine_Line_YZ(plNext, 22.5, 0)
ClosePolyLine_Line_YZ(plNext, plStart)
# End of Outline 1 PolyLine

# End of component bearing_front


# Create new component endcap_front
newComp = CreateNamedComponentWithColour_Axial("endcap_front", 105, 116, 255, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(76, 0)
plNext = AddPolyLine_Line_YZ(plStart, 22.5, 0)
plNext = AddPolyLine_Line_YZ(plNext, 22.5, -12)
plNext = AddPolyLine_Line_YZ(plNext, 32.5, -12)
plNext = AddPolyLine_Line_YZ(plNext, 32.5, -10)
plNext = AddPolyLine_Line_YZ(plNext, 120, -10)
plNext = AddPolyLine_Line_YZ(plNext, 120, -26.5)
plNext = AddPolyLine_Line_YZ(plNext, 140, -26.5)
plNext = AddPolyLine_Line_YZ(plNext, 140, 0)
ClosePolyLine_Line_YZ(plNext, plStart)
# End of Outline 1 PolyLine

# End of component endcap_front


# Create new component armature_endwinding_front
newComp = CreateNamedComponentWithColour_Axial("armature_endwinding_front", 239, 240, 16, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(85.491019, -14.986047)
plNext = AddPolyLine_Arc_YZ(plStart, 80.113985, -17.213287, 77.886745, -22.590321)
plNext = AddPolyLine_Line_YZ(plNext, 77.886745, -54.5)
plNext = AddPolyLine_Line_YZ(plNext, 100.93, -54.5)
plNext = AddPolyLine_Line_YZ(plNext, 100.93, -22.590321)
plNext = AddPolyLine_Arc_YZ(plNext, 98.70276, -17.213287, 93.325726, -14.986047)
ClosePolyLine_Line_YZ(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_endwinding_front


# Create new component armature_endwinding_rear
newComp = CreateNamedComponentWithColour_Axial("armature_endwinding_rear", 241, 240, 16, comp_Stator)

# Outline 1 PolyLine
plStart = GetPoint(100.93, -150.5)
plNext = AddPolyLine_Line_YZ(plStart, 77.886745, -150.5)
plNext = AddPolyLine_Line_YZ(plNext, 77.886745, -176.47757)
plNext = AddPolyLine_Arc_YZ(plNext, 80.113985, -181.854604, 85.491019, -184.081844)
plNext = AddPolyLine_Line_YZ(plNext, 93.325726, -184.081844)
plNext = AddPolyLine_Arc_YZ(plNext, 98.70276, -181.854604, 100.93, -176.47757)
ClosePolyLine_Line_YZ(plNext, plStart)
# End of Outline 1 PolyLine

# End of component armature_endwinding_rear


# Create new component endcap_rear
newComp = CreateNamedComponentWithColour_Axial("endcap_rear", 112, 116, 255, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(140, -173.5)
plNext = AddPolyLine_Line_YZ(plStart, 120, -173.5)
plNext = AddPolyLine_Line_YZ(plNext, 120, -190)
plNext = AddPolyLine_Line_YZ(plNext, 32.5, -190)
plNext = AddPolyLine_Line_YZ(plNext, 32.5, -188)
plNext = AddPolyLine_Line_YZ(plNext, 22.5, -188)
plNext = AddPolyLine_Line_YZ(plNext, 22.5, -200)
plNext = AddPolyLine_Line_YZ(plNext, 140, -200)
ClosePolyLine_Line_YZ(plNext, plStart)
# End of Outline 1 PolyLine

# End of component endcap_rear


# Create new component bearing_rear
newComp = CreateNamedComponentWithColour_Axial("bearing_rear", 177, 192, 192, comp_Housing)

# Outline 1 PolyLine
plStart = GetPoint(22.5, -188)
plNext = AddPolyLine_Line_YZ(plStart, 10, -188)
plNext = AddPolyLine_Line_YZ(plNext, 10, -200)
plNext = AddPolyLine_Line_YZ(plNext, 22.5, -200)
ClosePolyLine_Line_YZ(plNext, plStart)
# End of Outline 1 PolyLine

# End of component bearing_rear


# End of geometry section

# Solidify Sketches
mode = InteractionMode.Solid
result = ViewHelper.SetViewMode(mode, None)
# EndBlock

# Detach all faces and delete any interior voids
for compItem in GetRootPart().Components:
   if compItem.Content.Bodies.Count == 1:
      primaryPerimeter = 0.0
      primaryBox = 0.0
      compBody = compItem.Content.Bodies[0]
      if compBody.Faces.Count > 1:
         for faceItem in compBody.Faces:
            boxMagnitude = faceItem.Shape.GetBoundingBox(Matrix.Identity).Size.Magnitude
            if boxMagnitude > primaryBox:
               primaryBox = boxMagnitude
               primaryPerimeter = faceItem.Perimeter

         selection = BodySelection.Create(compBody)
         DetachFaces.Execute(selection)

         # Delete any voids
         deleteList = list(())
         for bodyItem in compItem.Content.Bodies:
            facePerimeter =  bodyItem.Faces[0].Perimeter
            if facePerimeter != primaryPerimeter:
               deleteList.append(bodyItem)
         [bodyItem.Delete() for bodyItem in deleteList]

# Set Component Colour
def SetComponentColour(aComponent, aR, aG, aB):
   compSelection = ComponentSelection.Create(aComponent)
   options = SetColorOptions()
   options.UseAlpha = True
   options.Exact = True
   options.RandomColor = False
   options.RandomSeed = 0
   options.EdgeColorTarget = EdgeColorTarget.Body
   options.FaceColorTarget = FaceColorTarget.Body
   ColorHelper.SetColor(compSelection, options, Color.FromArgb(aR, aG, aB))
# EndBlock

# Extrusion procedures
def AxialExtrudeComponent(aComponent, aAxialDepth):
   extrudeOptions = ExtrudeFaceOptions()
   extrudeOptions.KeepMirror = True
   extrudeOptions.KeepLayoutSurfaces = False
   extrudeOptions.KeepCompositeFaceRelationships
   extrudeOptions.PullSymmetric = False
   extrudeOptions.OffsetMode = OffsetMode.IgnoreRelationships
   extrudeOptions.Copy = False
   extrudeOptions.ForceDoAsExtrude = False
   extrudeOptions.ExtrudeType = ExtrudeType.Cut

   for bodyItem in aComponent.Content.Bodies: 
      selection = FaceSelection.Create(bodyItem.Faces)
      result = ExtrudeFaces.Execute(selection, MM(aAxialDepth), extrudeOptions)

def CircularExtrudeComponent(aComponent, aSweepAngle = 360):
   extrudeOptions = RevolveFaceOptions()
   extrudeOptions.ExtrudeType = ExtrudeType.Add
   axisSelection = Selection.Create(GetRootPart().CoordinateSystems[0].Axes[2])

   for bodyItem in aComponent.Content.Bodies: 
      selection = FaceSelection.Create(bodyItem.Faces)
      axis = RevolveFaces.GetAxisFromSelection(selection, axisSelection)
      result = RevolveFaces.Execute(selection, axis, DEG(aSweepAngle), extrudeOptions)
# End of extrusion procedures

rotorList = list(())
statorList = list(())
housingList = list(())
for ccItem in compLookupList:
   SetComponentColour(ccItem[kComponent], ccItem[kColour_R], ccItem[kColour_G], ccItem[kColour_B])
   if ccItem[kPartType] == PartType.AXIAL_CIRCULAR:
      CircularExtrudeComponent(ccItem[kComponent])
   elif ccItem[kPartType] == PartType.RADIAL:
      AxialExtrudeComponent(ccItem[kComponent], ccItem[kAxialLength])

   if ccItem[kGroup] == comp_Rotor:
      rotorList.append(ccItem[kComponent])
   if ccItem[kGroup] == comp_Stator:
      statorList.append(ccItem[kComponent])
   if ccItem[kGroup] == comp_Housing:
      housingList.append(ccItem[kComponent])

MoveComponent(rotorList, comp_Rotor)
MoveComponent(statorList, comp_Stator)
MoveComponent(housingList, comp_Housing)


# Simplify boundaries
try:
   result = FixExtraEdges.FindAndFix()
except:
   pass

result = ComponentHelper.SetRootActive(None)
ViewHelper.ZoomToEntity(Selection.Create(GetRootPart()))

# Simplify boundaries
try:
   result = FixExtraEdges.FindAndFix()
except:
   pass

# Report warnings
warningMessage = ""

DiscoSketchErrors = 0
for status in range(InitialStatusMessageCount, ApplicationHelper.StatusHistory.Count):
   if ApplicationHelper.StatusHistory[status].Message == "One or more of the created curves was below the minimum size for use with Sketch Constraints":
      DiscoSketchErrors = DiscoSketchErrors + 1
if DiscoSketchErrors > 0:
   warningMessage = str(DiscoSketchErrors) + " curves failed to draw due to being below the minimum allowed size. "

if (LineFailureCount > 0) or (ArcFailureCount > 0):
   if LineFailureCount > 0:
      warningMessage = warningMessage + str(LineFailureCount) + " lines"
      if ArcFailureCount > 0:
         warningMessage = warningMessage + " and " + str(ArcFailureCount) + " arcs"
      warningMessage = warningMessage + " have been removed. "
   else:
      warningMessage = warningMessage + str(ArcFailureCount) + " arcs have been removed. "

if ArcReplacementCount > 0:
   warningMessage = warningMessage + str(ArcReplacementCount) + "arcs have been replaced by lines. "

if warningMessage != "":
   ApplicationHelper.ReportWarning(warningMessage)
   print(ApplicationHelper.LatestStatusMessage.Message)
