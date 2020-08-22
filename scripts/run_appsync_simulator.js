const { ModelAuthTransformer } = require('graphql-auth-transformer')
const { ModelConnectionTransformer } = require('graphql-connection-transformer')
const { DynamoDBModelTransformer } = require('graphql-dynamodb-transformer')
const { GraphQLTransform } = require('graphql-transformer-core')

// TODO: we should not rely on this as it is an internal API
const { processTransformerStacks } = require('../node_modules/amplify-util-mock/lib/CFNParser/appsync-resource-processor.js')
const { AmplifyAppSyncSimulator } = require("amplify-appsync-simulator")
const fs = require("fs");

/**
 * This script runs a local AppSync simulator.
 * 
 * Usage: node ./run_appsync_simulator.js
 */

// NOTE: currently the API name is hardcoded below.  This will change in the future.
const apiName = "notespulumi"
const awsRegion = "eu-west-1"

const transformer = new GraphQLTransform({
    transformers: [
      new DynamoDBModelTransformer(),
      new ModelConnectionTransformer(),
      new ModelAuthTransformer({
        authConfig: {
          defaultAuthentication: {
            authenticationType: 'AMAZON_COGNITO_USER_POOLS',
          },
          additionalAuthenticationProviders: [],
        },
      }),
    ],
    transformConfig: {
      Version: 5
    }
  });

async function main() {

  const dynamoDbSimulator = require("./shared/dynamoDbSimulator");
  const port = 62225
  const schemaPath = `./amplify/backend/api/${apiName}/schema.graphql`
  const schema = fs.readFileSync(schemaPath).toString();
  const transformedSchema = transformer.transform(schema)

  simulatorConfig = processTransformerStacks(transformedSchema)
  
  // Parse the generated config to get the table name
  // This is not a long term solution
  simulatorConfig.dataSources = simulatorConfig.dataSources.map(dataSource => ({
    ...dataSource,
    config: {
      ...dataSource.config,
      endpoint: `http://localhost:${dynamoDbSimulator.port}`,
      region: awsRegion,
      tableName: `${apiName}_local.${dataSource.name.substring( 0, dataSource.name.indexOf( "Table" ))}`
    }
  }))

  let simulator = new AmplifyAppSyncSimulator({ port });
  await simulator.start()
  await simulator.init(simulatorConfig)
  console.log(`Running AppSync simulator on http://localhost:${port}`)
}

main()