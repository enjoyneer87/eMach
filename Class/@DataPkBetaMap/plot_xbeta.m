function plot_xbeta(td, data, plot_type)
    % Initialize colormap index
    persistent cmap_idx
    cmap_idx = 1;

    
    % Initialize colormap
    persistent cmap
    if isempty(cmap)
        cmap = colormap('lines');
    end
    
    % Check if plot_type is given, otherwise default to 'plot'
    if nargin < 3
        plot_type = 'plot';
    end
    
    % Plot 1D array
    prop = properties(td);
    for i = 1:length(prop)
        ch_prop = td.(char(prop(i)));
        dcheck = size(ch_prop);
        % If 1D, convert to meshgrid
        if dcheck(1) == 1 && dcheck(2) ~= 1
            [td.current, td.beta] = meshgrid(td.current, td.beta);
        end
    end
    
    %% 출력이름
    objname = inputname(1); % 내장 함수
    % Extract the substring after the last underscore in objname
    split_name = strsplit(objname, '_');
    objname = split_name{end};
    

    % Plot ND array
    
    
    if strcmp(data, 'beta')
        for i = width(td.beta):-1:1
            % Get color
            color = cmap(cmap_idx, :);
            
            % Create 

            if strcmp(plot_type, 'scatter')
                scatter(td.beta(:, i), td.beta(:, i), 'DisplayName', ...
                    strcat(mat2str(td.current(1, i)), '[A]_{pk}', " - ", objname), ...
                    'MarkerEdgeColor', color);
            else
                plot(td.beta(:, i), td.beta(:, i), 'DisplayName', ...
                    strcat(mat2str(td.current(1, i)), '[A]_{pk}', " - ", objname), ...
                    'Color', color,'LineStyle', '-', 'Marker', 'x');
            end
            formatter_sci
    
            hold on
            legend
            grid on
            box on
            ax = gca;
            ax.XLabel.String = 'phase advance [˚]';
            ax.YLabel.String = 'beta[˚]';
            
            % Increment colormap index and wrap around if necessary
            cmap_idx = cmap_idx + 1;
            if cmap_idx > size(cmap, 1)
                cmap_idx = 1;
            end
        end
    elseif strcmp(data, 'torque')
        for i = width(td.beta):-1:1
            % Get color
            color = cmap(cmap_idx, :);
            
            % Create plot
            if strcmp(plot_type, 'scatter')
                scatter(td.beta(:, i), td.torque_map(:, i), 'DisplayName', ...
                    strcat(mat2str(td.current(1, i)), '[A]_{pk}', " - ", objname), ...
                    'MarkerEdgeColor', color);
            else
                plot(td.beta(:, i), td.torque_map(:, i), 'DisplayName', ...
                    strcat(mat2str(td.current(1, i)), '[A]_{pk}', " - ", objname), ...
                    'Color', color,'LineStyle', '-', 'Marker', 'x');
            end
            hold on
            legend
            grid on
            box on
            ax = gca;
            ax.XLabel.String = 'phase advance [˚]';
            ax.YLabel.String = 'Torque[Nm]';
            
            % Increment colormap index and wrap around if necessary
            cmap_idx = cmap_idx + 1;
            if cmap_idx > size(cmap, 1)
                cmap_idx = 1;
            end
        end
    elseif strcmp(data, 'voltage')
        for i = width(td.beta):-1:1
            % Get color
            color = cmap(cmap_idx, :);
            
           % Create plot for Vd
    subplot(2, 1, 1)
    if strcmp(plot_type, 'scatter')
    scatter(td.beta(:, i), td.voltage.Vd(:, i), 'DisplayName', ...
    strcat(mat2str(td.current(1, i)), '[A]{pk}', " - ", objname), ...
    'MarkerEdgeColor', color);
    else
    plot(td.beta(:, i), td.voltage.Vd(:, i), 'DisplayName', ...
    strcat(mat2str(td.current(1, i)), '[A]{pk}', " - ", objname), ...
    'Color', color,'LineStyle', '-', 'Marker', 'x');
    end
    formatter_sci
    hold on
    legend
    grid on
    box on
    ax = gca;
    ax.XLabel.String = 'phase advance [˚]';
    ax.YLabel.String = 'Voltage[V]';
    
     % Create plot for Vq
        subplot(2, 1, 2)
        if strcmp(plot_type, 'scatter')
            scatter(td.beta(:, i), td.voltage.Vq(:, i), 'DisplayName', ...
                strcat(mat2str(td.current(1, i)), '[A]_{pk}', " - ", objname), ...
                'MarkerEdgeColor', color);
        else
            plot(td.beta(:, i), td.voltage.Vq(:, i), 'DisplayName', ...
                strcat(mat2str(td.current(1, i)), '[A]_{pk}', " - ", objname), ...
                'Color', color,'LineStyle', '-', 'Marker', 'x');
        end
        formatter_sci
        hold on
        legend
        grid on
        box on
        ax = gca;
        ax.XLabel.String = 'phase advance [˚]';
        ax.YLabel.String = 'Voltage[V]';
        
        % Increment colormap index and wrap around if necessary
        cmap_idx = cmap_idx + 1;
        if cmap_idx > size(cmap, 1)
            cmap_idx = 1;
        end
        end
        end
end