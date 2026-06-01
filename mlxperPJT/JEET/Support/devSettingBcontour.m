AddName='SC_'
app.View().Fit()
app.View().SetStep(61)
app.SetCurrentStudy([AddName,'e10_Coil_Load'])
curStudyObj=app.GetCurrentStudy;

TotalBContObj=curStudyObj.GetContour("untitled 1");
if TotalBContObj.IsValid
    TotalBContObj.SetName("TotalB")
end
TotalBContObj=curStudyObj.GetContour("TotalB");
TotalBContObj.SetRange("0", "2")
TotalBContObj.SetAutoScale(false)
TotalBContObj.SetDisplayMinimumLabel(false)
TotalBContObj.SetDisplayMaximumLabel(false)
TotalBContObj.SetUseSpecifiedPosition(true)
TotalBContObj.SetScaleBarPosition("0", "100")

curStudyObj.SetCurrentContour("TotalB")
appViewObj=app.View();
appViewObj.SetContourView(true);
appViewObj.ShowMeshGeometry()
%% Flux Line
FluxLineObj=curStudyObj.GetFluxLine(0);
FluxLineObj.SetLines(int32(70))
app.View().SetFluxLineView(true)

PNGDir="Z:/01_Codes_Projects/Thesis_skku/Thesis_SKKU/figure/JEET/rev1/";
PNGFilePath=fullfile(PNGDir,[AddName,'MS_Bcontour.png']);
app.ExportImageWithSize(PNGFilePath, 2000, 1500)

%% [TB]Slot B
app.View().SetStep(121)
%% get AirRegion Make B For Slot
curStudyObj.SetAirRegionVisibility(1, 1);

% Vector
if ~curStudyObj.GetVector("VectorB").IsValid
    curStudyObj.CreateVector("VectorB")
end
curStudyObj.GetVector("VectorB").SetResultType("MagneticFluxDensity", "")
curStudyObj.GetVector("VectorB").SetRange("0", "0.8")
curStudyObj.GetVector("VectorB").SetAutoScale(false)
curStudyObj.GetVector("VectorB").SetDisplayShellBeam(false)
curStudyObj.GetVector("VectorB").SetUseSpecifiedPosition(true)
curStudyObj.GetVector("VectorB").SetScaleBarPosition("100", "100")
curStudyObj.GetVector("VectorB").SetStyle("Wire")
curStudyObj.GetVector("VectorB").SetSize("10")
curStudyObj.GetVector("VectorB").SetNumVectors("0")
curStudyObj.GetVector("VectorB").SetGridSize("5")
app.View().ShowMesh()
curStudyObj.GetContour("SlotB").SetScaleBarPosition("100", "100")
curStudyObj.GetContour("VectorB").SetScaleBarPosition("100", "100")

ContourObj=curStudyObj.GetContour("SlotB");
% ContourObj.
appViewObj=app.View();
appViewObj.SetVectorView(true);
curStudyObj.SetCurrentVector("VectorB")

%% Flux Line
FluxLineObj=curStudyObj.GetFluxLine(0);
FluxLineObj.SetLines(int32(200))
appViewObj.SetFluxLineView(true)

% View
app.View().SetView([AddName,'Slot6View'])
%% Hide StatorCore

%%
PNGDir="Z:/01_Codes_Projects/Thesis_skku/Thesis_SKKU/figure/JEET/rev1/";
PNGFilePath=fullfile(PNGDir,[AddName,'MS_SlotBcontour.png']);

app.ExportImageWithSize(PNGFilePath, 2000, 1500)


