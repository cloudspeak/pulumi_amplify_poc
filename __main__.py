from os import environ
from pathlib import Path
from re import match
from typing import Any, Optional, Dict

import pulumi
from pulumi import Input, ResourceOptions, get_stack
from pulumi_aws import appsync, cognito, config, dynamodb, iam, s3, Provider
from pulumi_aws.get_caller_identity import get_caller_identity
from amplify_exports_file import AmplifyExportsFile


# Modify the variable below if you add new GraphQL types to the schema.

graphql_types = [
    "Note"
]

amplify_api_name = "notespulumi"

######

# The following environment variables can be set when running this script:
# NUAGE_LOCAL_AWS         If true, assumes that this Pulumi script is deploying to a local
#                         cloud stack.  It causes the provider to skip various validation
#                         measures, use custom endpoints (if provided), and will not
#                         generate a graphQL API (because the local AppSync simulator
#                         works in a different manner).
# NUAGE_DYNAMO_ENDPOINT   A custom endpoint for the DynamoDB API.

aws_region = config.region
account_id = get_caller_identity().account_id

amplify_api_build_dir = Path("amplify/backend/api").joinpath(amplify_api_name).joinpath("build")
schema_path = amplify_api_build_dir.joinpath("schema.graphql")
schema = schema_path.read_text()

is_local = environ.get("NUAGE_LOCAL_AWS") == "true"


# Provider

provider = None

if is_local:
    provider = Provider("aws_local",
        skip_credentials_validation=True,
        skip_metadata_api_check=True,
        skip_requesting_account_id=True,
        region=aws_region,
        endpoints=[{
            "dynamodb": environ.get("NUAGE_DYNAMO_ENDPOINT")
        }]
    )
else:
    provider = Provider("aws", region=aws_region)


# Resources

user_pool = cognito.UserPool("MyUserPool")

user_pool_client = cognito.UserPoolClient("MyUserPoolClient",
        user_pool_id=user_pool.id,
        opts=ResourceOptions(provider=provider)
)

stack_name = f"{amplify_api_name}_{get_stack()}"

# We do not create the graphQL API locally via Pulumi, we pass configuration to the
# AppSync simulator instead.
if not is_local:
    graphql_api = appsync.GraphQLApi(f"{stack_name}_graphql_api",
            authentication_type="AMAZON_COGNITO_USER_POOLS",
            user_pool_config={
                "default_action": "ALLOW",
                "user_pool_id": user_pool.id,
                "app_id_client_regex": user_pool_client.id
            },
            schema=schema
    )

def generate_dynamo_data_source(type_name):
    """
    Generates a DynamoDB data source for the given GraphQL type.  This includes the
    Dynamo table, the AppSync data source, a data source role, and the resolvers.

    NOTE: This function generates Dynamo tables with a hash key called `id`, but no other keys.

    :param type_name    The name of the GraphQL type.  This is the identifier which appears after
                        the `type` keyword in the schema.
    """

    table = dynamodb.Table(f"{stack_name}_{type_name}_table",
            name=f"{stack_name}.{type_name}",
            hash_key="id",
            attributes=[
                {
                    "name": "id",
                    "type": "S"
                }
            ],
            #stream_view_type="NEW_AND_OLD_IMAGES",
            billing_mode="PAY_PER_REQUEST",
            opts=ResourceOptions(provider=provider)
    )

    if not is_local:
        data_source_iam_role = iam.Role(f"{stack_name}_{type_name}_role",
                assume_role_policy="""{
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "appsync.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }"""
        )

        data_source_iam_role_policy = iam.RolePolicy(f"{stack_name}_{type_name}_role_policy",
                role=data_source_iam_role.name,
                name="MyDynamoDBAccess",
                policy=table.name.apply(lambda table_name: f"""{{
            "Version": "2012-10-17",
            "Statement": [
                {{
                    "Effect": "Allow",
                    "Action": [
                        "dynamodb:BatchGetItem",
                        "dynamodb:BatchWriteItem",
                        "dynamodb:PutItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:GetItem",
                        "dynamodb:Scan",
                        "dynamodb:Query",
                        "dynamodb:UpdateItem"
                    ],
                    "Resource": [
                        "arn:aws:dynamodb:{aws_region}:{account_id}:table/{table_name}",
                        "arn:aws:dynamodb:{aws_region}:{account_id}:table/{table_name}/*"
                    ]
                }}
            ]
        }}""")
        )

        data_source = appsync.DataSource(f"{stack_name}_{type_name}_data_source",
                api_id=graphql_api.id,
                name=f"{type_name}TableDataSource",
                type="AMAZON_DYNAMODB",
                service_role_arn=data_source_iam_role.arn,
                dynamodb_config={
                    "table_name": table.name
                },
                opts=ResourceOptions(depends_on=[data_source_iam_role])
        )

        resolvers = generate_resolvers(type_name, data_source)

        return {
            "table": table,
            "data_source_iam_role": data_source_iam_role,
            "data_source_iam_role_policy": data_source_iam_role_policy,
            "data_source": data_source,
            "resolvers": resolvers
        }
    
    return {
        "table": table
    }

def generate_resolvers(type_name, data_source):
    """
    Creates AppSync resolvers for the given GraphQL type.  Resolvers are created by iterating
    through the `resolvers` directory in the API's build folder and parsing the resolver
    template filenames to find the operation name and type.

    :param type_name    The name of the GraphQL type.  This is the identifier which appears after
                        the `type` keyword in the schema.
    :param data_source  The AppSync data source Pulumi resource for the type.
    """
    resolvers_dir = amplify_api_build_dir.joinpath("resolvers")
    resolvers = []

    for req_file in resolvers_dir.iterdir():
        regex_match = match(f"^([a-zA-Z]+)\.([a-zA-Z]+{type_name}s?)\.req\.vtl$", str(req_file.name))

        if regex_match:
            operation_type = regex_match.group(1)
            operation_name = regex_match.group(2)
            res_file = resolvers_dir.joinpath(f"{operation_type}.{operation_name}.res.vtl")

            resolver = appsync.Resolver(f"{stack_name}_{operation_name}_resolver",
                api_id=graphql_api.id,
                data_source=data_source.name,
                field=operation_name,
                type=operation_type,
                request_template=req_file.read_text(),
                response_template=res_file.read_text()
            )

            resolvers.append(resolver)
    
    return resolvers

for type in graphql_types:
    resources = generate_dynamo_data_source(type)


exports_file = AmplifyExportsFile(f"{stack_name}_exports_file", {
    "aws_project_region": aws_region,
    "aws_cognito_region": aws_region,
    "aws_user_pools_id": user_pool.id,
    "aws_user_pools_web_client_id": user_pool_client.id,
    "aws_appsync_graphqlEndpoint": graphql_api.uris["GRAPHQL"] if not is_local else "http://localhost:62225/graphql",
    "aws_appsync_dangerously_connect_to_http_endpoint_for_testing": True if is_local else None,
    "aws_appsync_region": aws_region,
    "aws_appsync_authenticationType": "AMAZON_COGNITO_USER_POOLS",
})

if not is_local:
    pulumi.export('graphql_api_uri',  graphql_api.uris["GRAPHQL"])
pulumi.export('user_pool_id',  user_pool.id)
pulumi.export('user_pool_client_id',  user_pool_client.id)
