AddName='SC_';
app.View().Fit()
app.View().SetStep(61)

app.SetCurrentStudy([AddName,'e10_Coil_Load'])
curStudyObj=app.GetCurrentStudy;
MVPContObj=curStudyObj.GetContour("untitled 3");
if MVPContObj.IsValid
    MVPContObj.SetName("MVP")
end
MVPContObj=curStudyObj.GetContour("MVP");

MVPContObj.SetRange("0", "0.05")
MVPContObj.SetAutoScale(false)
MVPContObj.SetDisplayMinimumLabel(false)
MVPContObj.SetDisplayMaximumLabel(false)
MVPContObj.SetUseSpecifiedPosition(true)
MVPContObj.SetScaleBarPosition("0", "100")
%% Contour
appViewObj=app.View();
appViewObj.SetContourView(true);
curStudyObj.SetCurrentContour("MVP")


%FluxLine
curStudyObj.SetCurrentContour("MVP")
app.SetCurrentStudy([AddName,'e10_Coil_Load'])
app.View().SetFluxLineView(false)

%%
PNGDir="Z:/01_Codes_Projects/Thesis_skku/Thesis_SKKU/figure/JEET/rev1/";
PNGFilePath=fullfile(PNGDir,[AddName,'MS_Acontour.png']);
app.ExportImageWithSize(PNGFilePath, 2000, 1500)



