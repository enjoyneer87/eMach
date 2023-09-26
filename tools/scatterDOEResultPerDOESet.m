function scatterDOEResultPerDOESet(DOEResult, color, legendName, useFilled)
    DOE1 = DOEResult;
    Fieldlist1 = fieldnames(DOE1);
    
    % Initialize legend_labels and legend_colors arrays
    legend_labels = {};
    legend_colors = {};
    figure(1)
    for i = 1:length(Fieldlist1)
        FieldName = Fieldlist1{i};
        if ~isempty(DOE1.(FieldName)) && isfield(DOE1.(FieldName), 'Weight') && isfield(DOE1.(FieldName), 'SumofTotalLoss')
            o_Weight_Act = DOE1.(FieldName).Weight.o_Weight_Act;
            if isfield(DOE1.(FieldName).SumofTotalLoss,'SumOfTotalLoss')
                SumOfTotalLoss = DOE1.(FieldName).SumofTotalLoss.SumOfTotalLoss;
            end
            if isfield(DOE1.(FieldName).SumofTotalLoss,'SumofTotalLoss')
                SumOfTotalLoss = DOE1.(FieldName).SumofTotalLoss.SumofTotalLoss;
            end
            % Check if 'useFilled' option is provided and set the marker face accordingly
            if  useFilled==1
                h1 = scatter3(o_Weight_Act, SumOfTotalLoss, str2num(strrep(FieldName,'Design','')), color,'filled' ,'DisplayName', FieldName, 'LineWidth', 2);
            else
                h1 = scatter3(o_Weight_Act, SumOfTotalLoss, str2num(strrep(FieldName,'Design','')), color, 'DisplayName', FieldName, 'LineWidth', 2);
            end
            hold on;

%             % Store legend labels and colors for the first call
%             if i == 1
%                 legend_labels = [legend_labels, legendName];
%                 legend_colors = [legend_colors, h1];            
%             end
        end
    end

%     % Set the legend for the first call
%     if ~isempty(legend_labels)
%         legend(legend_colors, legend_labels);
%     end

    figure(2)
    for i = 1:length(Fieldlist1)
        FieldName = Fieldlist1{i};
        if ~isempty(DOE1.(FieldName)) && isfield(DOE1.(FieldName), 'Weight') && isfield(DOE1.(FieldName), 'SumofTotalLoss')
            if isfield(DOE1.(FieldName).Weight, 'TotalMotorGearWeight')
                TotalMotorGearWeight = DOE1.(FieldName).Weight.TotalMotorGearWeight;
            end
            if isfield(DOE1.(FieldName).Weight, 'TotalEDUWeight')
                TotalMotorGearWeight = DOE1.(FieldName).Weight.TotalEDUWeight;
            end

            if isfield(DOE1.(FieldName).SumofTotalLoss,'SumOfTotalLoss')
                SumOfTotalLoss = DOE1.(FieldName).SumofTotalLoss.SumOfTotalLoss;
            end
            if isfield(DOE1.(FieldName).SumofTotalLoss,'SumofTotalLoss')
                SumOfTotalLoss = DOE1.(FieldName).SumofTotalLoss.SumofTotalLoss;
            end
            % Check if 'useFilled' option is provided and set the marker face accordingly
            if useFilled==1
                h1 = scatter3(TotalMotorGearWeight, SumOfTotalLoss, str2num(strrep(FieldName,'Design','')), color, 'filled', 'DisplayName', FieldName, 'LineWidth', 2);
            else
                h1 = scatter3(TotalMotorGearWeight, SumOfTotalLoss, str2num(strrep(FieldName,'Design','')), color, 'DisplayName', FieldName, 'LineWidth', 2);
            end
            hold on;

            % Store legend labels and colors for the first call
            if i == 1
                legend_labels = [legend_labels, legendName];
                legend_colors = [legend_colors, h1];            
            end
        end

%     % Set the legend for the first call
%     if ~isempty(legend_labels)
%         figure(2)
%         legend(legend_colors, legend_labels);
%     end

    end
end
