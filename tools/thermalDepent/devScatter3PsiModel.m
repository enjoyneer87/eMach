function devScatter3PsiModel(id,iq,PsiModelData)
    subplot1 = subplot(2,1,1);
    scatter3(id, iq, PsiModelData.PsiDModel_Lab);
    xlabel('id');
    ylabel('iq');
    zlabel('PsiD');
    hold on
    % for i = 1:length(id)
    %     text(id(i), iq(i), PsiModelData.PsiDModel_Lab(i), num2str(PsiModelData.PsiDModel_Lab(i)), 'FontSize', 8, 'HorizontalAlignment', 'center');
    % end
    set(subplot1,'YAxisLocation','right');
    formatter_sci
    %
    subplot2 = subplot(2,1,2);
    scatter3(id, iq, PsiModelData.PsiQModel_Lab);
    xlabel('id');
    ylabel('iq');
    zlabel('PsiQ');
    hold on
    set(subplot2,'YAxisLocation','right');
end