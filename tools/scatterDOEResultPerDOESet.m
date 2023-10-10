function [legend_colorsh1,legend_colorsh2]=scatterDOEResultPerDOESet(DOEResult, color, legendName, useFilled, varargin)
    DOE1 = DOEResult;
    Fieldlist1 = fieldnames(DOE1);

    % 초기 범례 라벨 및 색상 배열 초기화
    legend_labels = {};
    legend_colorsh1 = {};
    legend_colorsh2 = {};


    % 기본 마커 정의
    defaultMarker = 'o';

    % 사용자가 마커를 지정했는지 확인
    if ~isempty(varargin)
        customMarker = varargin{1};
    else
        customMarker = defaultMarker;  % 사용자가 마커를 지정하지 않으면 기본 마커 사용
    end

    figure(1)
    xlabel('Motor Active Weight[kg]');
    ylabel('WLTP3 Motor Engery Consumption [Wh]');
    zlabel('Design Number');

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
            % 'useFilled' 옵션이 제공되었는지 확인하고 마커 표면을 채움
            if useFilled==1
                h1 = scatter3(o_Weight_Act, SumOfTotalLoss, str2num(strrep(FieldName,'Design','')),'Marker', customMarker,'MarkerEdgeColor', color, 'MarkerFaceColor',color, 'DisplayName', FieldName, 'LineWidth', 2);
            else
                h1 = scatter3(o_Weight_Act, SumOfTotalLoss, str2num(strrep(FieldName,'Design','')),'Marker', customMarker,'MarkerEdgeColor',color, 'DisplayName', FieldName, 'LineWidth', 2);
            end
            hold on;
                        % 첫 번째 호출에 대한 범례 라벨 및 색상 저장
            if i == 1
                legend_labels = [legend_labels, legendName];
                legend_colorsh1 = [legend_colorsh1, h1];     
                legend_colorsh1.DisplayName=legendName;
            end
        end
    end
    formatter_sci

    figure(2)
    xlabel('Motor and GearBox Weight[kg]');
    ylabel('WLTP3 Motor Engery Consumption [Wh]');
    zlabel('Design Number');

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

            % 'useFilled' 옵션이 제공되었는지 확인하고 마커 표면을 채움
            if useFilled==1
                h2 = scatter3(TotalMotorGearWeight, SumOfTotalLoss, str2num(strrep(FieldName,'Design','')),'Marker', customMarker,'MarkerEdgeColor', color, 'MarkerFaceColor',color,  'DisplayName', FieldName, 'LineWidth', 2);
            else
                h2 = scatter3(TotalMotorGearWeight, SumOfTotalLoss, str2num(strrep(FieldName,'Design','')),'Marker', customMarker, 'MarkerEdgeColor', color,  'DisplayName', FieldName, 'LineWidth', 2);
            end
            hold on;

            % 첫 번째 호출에 대한 범례 라벨 및 색상 저장
            if i == 1
                legend_labels = [legend_labels, legendName];
                legend_colorsh2 = [legend_colorsh2, h2];   
                legend_colorsh2.DisplayName=legendName;
            end
        end
    end
    formatter_sci
end