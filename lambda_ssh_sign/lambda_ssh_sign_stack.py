from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
    CfnParameter,
    Duration,
    aws_kms as kms,
    aws_lambda as lambda_,
    aws_lambda_python_alpha as pylambda
)
from constructs import Construct

class LambdaSshSignStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        timer = self.node.try_get_context('max_token_lifetime')
        shared_user = self.node.try_get_context('shared_user_account_name')

        key = kms.Key.from_key_arn(scope=self, id="CAKey", key_arn=self.node.try_get_context('kms_key_arn'))
        
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
                "KMS_KEY_ARN": key.key_arn,
                "MAX_VALID_MINUTES": str(timer),
                "SHARED_USER_ID": str(shared_user)
                },
            timeout=Duration.seconds(30)
            )

        # Perms
        key.grant(func, 'kms:Sign')
