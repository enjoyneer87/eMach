classdef GraphTable
    properties
        graph
    end

    methods
        function obj = GraphTable(table)
            
                obj.graph = table;
            
        end

        function plot(obj)
            plotJMAGResultDataStruct(obj.graph);
        end
    end
end