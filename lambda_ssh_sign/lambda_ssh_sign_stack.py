from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    CfnParameter,
    Duration,
    aws_secretsmanager as secretsmanager,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as pylambda
)
from constructs import Construct

class LambdaSshSignStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        arn = CfnParameter(self, "secret-arn", type='String')
        timer = self.node.try_get_context('max_token_lifetime')
        shared_user = self.node.try_get_context('shared_user_account_name')

        keys = secretsmanager.Secret.from_secret_complete_arn(self, id="CAKeysSecret", secret_complete_arn=arn.value_as_string)
        
        # Lambda
        params_and_secrets = lambda_.ParamsAndSecretsLayerVersion.from_version(lambda_.ParamsAndSecretsVersions.V1_0_103,
            cache_size=500,
            log_level=lambda_.ParamsAndSecretsLogLevel.DEBUG
        )
        layer = pylambda.PythonLayerVersion(self, "MyLayer", entry="./lambda_layer/", compatible_runtimes=[lambda_.Runtime.PYTHON_3_11])
        func = pylambda.PythonFunction(self, "SSH-Key-Signer", entry="./lambda_source/", 
            layers=[layer] ,runtime=lambda_.Runtime.PYTHON_3_11, index="signinglambda.py", 
            params_and_secrets=params_and_secrets, 
            environment={
                "SecretARN": arn.value_as_string,
                "MAX_VALID_MINUTES": str(timer),
                "SHARED_USER_ID": str(shared_user)
                },
            timeout=Duration.seconds(30)
            )

        # Perms
        keys.grant_read(func)
