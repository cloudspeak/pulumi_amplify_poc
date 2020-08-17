const path = require('path')
const simulator = require('amplify-dynamodb-simulator')
const { spawn }  = require('child_process')
const log = require('logdown')('run_pulumi_local')

/**
 * This script is required to run Pulumi when deploying cloud resources to a local
 * DynamoDB instance.  It launches the Dyanmo simulator process, then runs Pulumi
 * with a set of environment variables containing the local database config,
 * before terminating the instance again.
 * 
 * Usage: node ./run_pulumi_local.js [pulumi args]
 * 
 * Example:
 *  node ./run_pulumi_local.js up -s local
 */


// Starts an instance of the dynamo simulator which persists to disk
async function startDynamoDB() {
    const opts = {
        dbPath: path.join(process.cwd(), ".dynamodb"),
        inMemory: false,
        port: 62226
    }
    log.info("Running Dynamo simulator with options: ", opts)
    return await simulator.launch(opts);
}


// Executes `pulumi up` for the `local` stack, passing in environment
// variables which allow overriding endpoints to refer to the local
// DynamoDB instance.
function runPulumi(dynamoEndpoint, pulumiArgs) {
    log.info("Running pulumi up with dynamo endpoint: ", dynamoEndpoint)
    return new Promise(resolve => {
        const subProcess = spawn("pulumi", pulumiArgs, {
            stdio: 'inherit',
            env: {
                ...process.env,
                "NUAGE_LOCAL_AWS": "true",
                "NUAGE_DYNAMO_ENDPOINT": dynamoEndpoint
            }
        })
        subProcess.on('close', code => resolve(code))         
    })
}

async function main() {
    let dynamo = await startDynamoDB()
    const port = dynamo.opts.port
    const dynamoEndpoint = `http://localhost:${port}`
    const pulumiArgs = process.argv.slice(2)
    const exitCode = await runPulumi(dynamoEndpoint, pulumiArgs)
    await dynamo.terminate()
    process.exit(exitCode)
}

main()
