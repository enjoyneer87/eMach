function plot_xpk(td)
%% 1d array
%     plot all
    prop=properties(td);
    for i=1:length(prop)
        ch_prop=td.(char(prop(i)));
        dcheck=size(ch_prop);
    
        if dcheck(1) == 1 & dcheck(2) ~= 1
            disp(strcat(num2str(i),'change to mesh grid'))
            [td.current,td.beta]=meshgrid(td.current, td.beta);

        end
    end

%% nd array

%% 
    
    objname=inputname(1); 
    for i=16:-1:1

    
    disname=strcat(mat2str(td.current(1,i)),'[A]_{pk}'," - ",objname);
    
    plot(td.beta(:,i),td.torque_map(:,i),DisplayName=disname);
    hold on
    legend
    grid on
    box on
    ax=gca;
    ax.XLabel.String="phase advance [˚]";
    ax.YLabel.String='Torque[Nm]';

    end

%%  
% %   plot(td.Strain,td.Stress,varargin{:})
%       title(['Stress/Strain plot for Sample',...
%          num2str(td.SampleNumber)])
%       ylabel('Stress (psi)')
%       xlabel('Strain %')
  end