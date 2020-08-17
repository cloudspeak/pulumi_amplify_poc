const { startDynamoDbSimulator } = require("./shared/dynamoDbSimulator");

startDynamoDbSimulator()
    .then(simulator => {
        console.log(`Running DynamoDB simulator on http://localhost:${simulator.opts.port}`)
    })
