import aws_cdk as core
import aws_cdk.assertions as assertions

from lambda_ssh_sign.lambda_ssh_sign_stack import LambdaSshSignStack

# example tests. To run these tests, uncomment this file along with the example
# resource in lambda_ssh_sign/lambda_ssh_sign_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = LambdaSshSignStack(app, "lambda-ssh-sign")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
