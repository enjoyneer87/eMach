
% object make
HDEVdata=DataDqMap(6);
HDEVdata.current_dq_map.id=SatuMap_SplaidRef.Id_Peak(:,1)';
HDEVdata.current_dq_map.iq=SatuMap_SplaidRef.Iq_Peak(1,:)';
HDEVdata.flux_linkage_map.in_d=SatuMap_SplaidRef.Flux_Linkage_D' 
HDEVdata.flux_linkage_map.in_q=SatuMap_SplaidRef.Flux_Linkage_Q' 

size(SatuMap_SplaidRef.Id_Peak(:,1))
HDEVdata.plot_xdyq('flux')

%% Duplicate
SplaidRefObject=HDEVdata;
SplaidscaleObject=SplaidRefObject;

SplaidscaleObject.flux_linkage_map.in_d=0.9*SplaidscaleObject.flux_linkage_map.in_d
SplaidscaleObject.flux_linkage_map.in_q=0.9*SplaidscaleObject.flux_linkage_map.in_q
SplaidscaleObject.plot_xdyq('flux')

td=  SplaidRefObject;
        disname='d';
        subplot(2,1,1)
        % surf(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_d,DisplayName=disname);
        hold on
        % stem3(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_d,'DisplayName',disname,"LineStyle","none");

        % contourf(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_d,'EdgeColor', 'k','LineStyle','--');
        % contourf(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_d);

        contour3(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_d','EdgeColor', 'k','LineStyle','--');

        legend
        grid on
        box on
        ax=gca;
        ax.XLabel.String="id[A]";
        ax.YLabel.String='iq[A]';
        view(2)
        subplot(2,1,2)
        disname='q';
        % surf(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_q,DisplayName=disname);
                    hold on
        % stem3(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_q,'DisplayName',disname,"LineStyle","none");

        % contourf(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_q,'EdgeColor', 'k','LineStyle','--');
        % contourf(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_q);

        contour3(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_q','EdgeColor', 'k','LineStyle','--');

        legend
        grid on
        box on
        ax=gca;
        ax.XLabel.String="id[A]";
        ax.YLabel.String='iq[A]';
        view(2)
        % title(data)

td=SplaidscaleObject;
                disname='d';
        subplot(2,1,1)
        % surf(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_d,DisplayName=disname);
        hold on
        % stem3(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_d,'DisplayName',disname,"LineStyle","none");

        % contourf(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_d,'EdgeColor', 'k','LineStyle','--');
        % contourf(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_d);

        contour3(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_d','EdgeColor', 'r','LineStyle','--');

        legend
        grid on
        box on
        ax=gca;
        ax.XLabel.String="id[A]";
        ax.YLabel.String='iq[A]';
        view(2)
        subplot(2,1,2)
        disname='q';
        % surf(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_q,DisplayName=disname);
                    hold on
        % stem3(td.current_dq_map.id,td.current_dq_map.iq,td.flux_linkage_map.in_q,'DisplayName',disname,"LineStyle","none");

        % contourf(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_q,'EdgeColor', 'k','LineStyle','--');
        % contourf(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_q);

        contour3(td.current_dq_map.id, td.current_dq_map.iq, td.flux_linkage_map.in_q','EdgeColor', 'r','LineStyle','--');

        legend
        grid on
        box on
        ax=gca;
        ax.XLabel.String="id[A]";
        ax.YLabel.String='iq[A]';
        view(2)
        % title(data)