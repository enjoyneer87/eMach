function compareRBFwithfitresult(gpr_model, fitresults,zArray)

    figure;
    h = plot(fitresults{1});
    id_range = [min(min(h.XData)), max(max(h.XData))];
    iq_range = [min(min(h.YData)), max(max(h.YData))];
    close all;

    grid_size=[20 20];
    % id, iq 그리드 생성
    id_vals = linspace(id_range(1), id_range(2), grid_size(1));
    iq_vals = linspace(iq_range(1), iq_range(2), grid_size(2));
    [ID, IQ] = meshgrid(id_vals, iq_vals);
    fID=ID(:)
    fIQ=IQ(:)

    for zIndex=1:len(zArray)
        plot(fitresults{zIndex})
        hold on
        y_pred = predict(gpr_model, [fID, fIQ zArray(zIndex)*ones(len(fIQ),1)]);
        scatter3(fID,fIQ,y_pred,'DisplayName',['GP Fitted:',num2str(zArray(zIndex))])
    end
end