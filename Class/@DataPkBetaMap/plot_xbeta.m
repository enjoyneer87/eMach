function plot_xbeta(td,data)
%% 1d array
%     plot all
    prop=properties(td);
    for i=1:length(prop)
        ch_prop=td.(char(prop(i)));
        dcheck=size(ch_prop);
    %1열짜리면 meshgrid 형태로 만들기
        if dcheck(1) == 1 & dcheck(2) ~= 1
            disp(strcat(num2str(i),'change to mesh grid'))
            [td.current,td.beta]=meshgrid(td.current, td.beta);

        end
    end

%% nd array

%% 
    
    objname=inputname(1); 
    if strcmp(data,'beta')
        for i=width(td.beta):-1:1
            disname=strcat(mat2str(td.current(1,i)),'[A]_{pk}'," - ",objname);
            plot(td.beta(:,i),td.beta(:,i),DisplayName=disname);
            formatter_sci

            hold on
            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="phase advance [˚]";
            ax.YLabel.String='beta[˚]';
        end
    elseif  strcmp(data,'torque')
        for i=width(td.beta):-1:1
            disname=strcat(mat2str(td.current(1,i)),'[A]_{pk}'," - ",objname);
            plot(td.beta(:,i),td.torque_map(:,i),DisplayName=disname);
            hold on
            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="phase advance [˚]";
            ax.YLabel.String='torque[Nm]';
        end
    elseif strcmp(data,'voltage')
        for i=width(td.beta):-1:1
            disname=strcat(mat2str(td.current(1,i)),'[A]_{pk}'," - ",objname);
            subplot(2,1,1)
            plot(td.beta(:,i),td.voltage.Vd(:,i),DisplayName=disname);
            formatter_sci

            hold on
            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="phase advance [˚]";
            ax.YLabel.String='voltage[V]';
            subplot(2,1,2)
            formatter_sci
            plot(td.beta(:,i),td.voltage.Vq(:,i),DisplayName=disname);
            hold on
            legend
            grid on
            box on
            ax=gca;
            ax.XLabel.String="phase advance [˚]";
            ax.YLabel.String='voltage[V]';
        end
    end
    

    end

%%  
% %   plot(td.Strain,td.Stress,varargin{:})
%       title(['Stress/Strain plot for Sample',...
%          num2str(td.SampleNumber)])
%       ylabel('Stress (psi)')
%       xlabel('Strain %')
