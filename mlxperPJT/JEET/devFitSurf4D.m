bufit=fitresults'
fitresults{4}=[];
fitresults=removeEmptyCells(fitresults)
z_assigned=[4000 8000 12000]
grid_size = [20, 20];

[gpr_model, fID,fIQ]= fitTrivariateByTPS(fitresults, z_assigned, grid_size)

compareRBFwithfitresult(gpr_model, fitresults,z_assigned)

y_pred = predict(gpr_model, [fID, fIQ 18000*ones(len(fIQ),1)]);

plot(bufit{4})
scatter3(fID,fIQ,y_pred)
hold on
