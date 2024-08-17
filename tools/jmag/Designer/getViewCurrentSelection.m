function sel=getViewCurrentSelection(JView)

%%
xstart=0;
ystart=0;
zstart=0;
xMax=400;
yMax=400;
zMax=400;

%%
JView.SelectByCircleWorldPos(xstart, ystart,zstart, xMax, yMax, zMax, 0);
sel=JView.GetCurrentSelection;

end