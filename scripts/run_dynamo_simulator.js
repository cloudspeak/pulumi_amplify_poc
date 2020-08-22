const { startDynamoDbSimulator } = require("./shared/dynamoDbSimulator");

/**
 * This script runs a DynamoDB simulator stored in a local directory.
 * 
 * Usage: node ./run_dynamo_simulator.js
 */

startDynamoDbSimulator()
    .then(simulator => {
        console.log(`Running DynamoDB simulator on http://localhost:${simulator.opts.port}`)
    })
