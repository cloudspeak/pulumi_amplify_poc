const { join } = require('path')
const simulator = require('amplify-dynamodb-simulator')

const log = require('logdown')('dynamoDbSimulator')

const port = 62226

// Starts an instance of the dynamo simulator which persists to disk
async function startDynamoDbSimulator() {
    const opts = {
        dbPath: join(process.cwd(), ".dynamodb"),
        inMemory: false,
        port
    }
    log.info("Running Dynamo simulator with options: ", opts)
    return await simulator.launch(opts);
}

module.exports = {
    port,
    startDynamoDbSimulator
}