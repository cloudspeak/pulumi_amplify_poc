from pathlib import Path

import pulumi
from pulumi import ResourceOptions
from pulumi_aws import appsync, s3, cognito, dynamodb, iam, config
from pulumi_aws.get_caller_identity import get_caller_identity

aws_region = config.region
account_id = get_caller_identity().account_id

schema = Path("schema.graphql").read_text()

user_pool = cognito.UserPool("MyUserPool")

user_pool_client = cognito.UserPoolClient("MyUserPoolClient",
        user_pool_id=user_pool.id
)

graphql_api = appsync.GraphQLApi("MyGraphQLApi",
        authentication_type="API_KEY",
        # authentication_type="AMAZON_COGNITO_USER_POOLS",
        # user_pool_config={
        #     "default_action": "DENY",
        #     "user_pool_id": user_pool.id,
        #     "app_id_client_regex": user_pool_client.id
        # },
        schema=schema
)

notes_table = dynamodb.Table("MyNotesTable",
        name="NotesPulumi.Notes",
        hash_key="id",
        attributes=[
            {
                "name": "id",
                "type": "S"
            }
        ],
        #stream_view_type="NEW_AND_OLD_IMAGES",
        billing_mode="PAY_PER_REQUEST"       
)


# Amplify makes a role for each type but for now I'll just make one for all types
data_source_iam_role = iam.Role("MyDataSourceRole",    
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

data_source_iam_role_policy = iam.RolePolicy("MyDataSourceRolePolicy",
        role=data_source_iam_role.name,
        name="MyDynamoDBAccess",
        policy=notes_table.name.apply(lambda table_name: f"""{{
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

notes_data_source = appsync.DataSource("MyDataSource",
        api_id=graphql_api.id,
        name="NoteTableDataSource",
        type="AMAZON_DYNAMODB",
        service_role_arn=data_source_iam_role.arn,
        dynamodb_config={
            "table_name": notes_table.name
        },
        opts=ResourceOptions(depends_on=data_source_iam_role)
)

get_notes_resolver = appsync.Resolver("MyGetNotesResolver",
        api_id=graphql_api.id,
        data_source=notes_data_source.name,
        field="getNote",
        type="Query"
)

list_notes_resolver = appsync.Resolver("ListGetNotesResolver",
        api_id=graphql_api.id,
        data_source=notes_data_source.name,
        field="listNotes",
        type="Query"
)


notes_table.name.apply(lambda table_name: print(f"""{{
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
}}"""))


pulumi.export('graphql_api_uri',  graphql_api.uris["GRAPHQL"])
pulumi.export('user_pool_id',  user_pool.id)
pulumi.export('user_pool_client_id',  user_pool_client.id)
