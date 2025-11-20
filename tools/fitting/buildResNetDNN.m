function lgraph = buildResNetDNN(inputDim_geom, inputDim_curr)
    % 형상 feature subnetwork
    layersGeom = [
        featureInputLayer(inputDim_geom, 'Name', 'geom_input')
        fullyConnectedLayer(64, 'Name', 'fc_geom1')
        reluLayer('Name', 'relu_geom1')
        fullyConnectedLayer(32, 'Name', 'fc_geom2')
        reluLayer('Name', 'relu_geom2')
    ];

    % 전류 feature subnetwork with residual
    layersCurr = [
        featureInputLayer(inputDim_curr, 'Name', 'curr_input')
        fullyConnectedLayer(64, 'Name', 'fc_curr1')
        reluLayer('Name', 'relu_curr1')
        fullyConnectedLayer(64, 'Name', 'fc_curr2')
        additionLayer(2, 'Name', 'res_add')
        reluLayer('Name', 'res_relu')
        fullyConnectedLayer(32, 'Name', 'fc_curr3')
    ];

    % Concatenate and final output
    layersFinal = [
        concatenationLayer(1, 2, 'Name', 'concat')
        fullyConnectedLayer(32, 'Name', 'fc_final1')
        reluLayer('Name', 'relu_final1')
        fullyConnectedLayer(1, 'Name', 'output')
        regressionLayer('Name', 'regression_output')
    ];

    % Assemble graph
    lgraph = layerGraph(layersGeom);
    lgraph = addLayers(lgraph, layersCurr);
    lgraph = addLayers(lgraph, layersFinal);

    % Connect residual block
    lgraph = connectLayers(lgraph, 'fc_curr1', 'res_add/in1');
    lgraph = connectLayers(lgraph, 'fc_curr2', 'res_add/in2');

    % Connect subnetworks
    lgraph = connectLayers(lgraph, 'fc_geom2', 'concat/in1');
    lgraph = connectLayers(lgraph, 'fc_curr3', 'concat/in2');
end
