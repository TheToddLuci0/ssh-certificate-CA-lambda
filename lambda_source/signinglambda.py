# Every certificate needs two parts, the subject (user or host) public key and the CA Private key
from sshkey_tools.cert import SSHCertificate, CertificateFields, Ed25519Certificate
from sshkey_tools.keys import PrivateKey, PublicKey
from datetime import datetime, timedelta
import requests
import json
import os
headers = {"X-Aws-Parameters-Secrets-Token": os.environ.get('AWS_SESSION_TOKEN')}
secrets_extension_endpoint = "http://localhost:" + \
    os.environ.get('PARAMETERS_SECRETS_EXTENSION_HTTP_PORT') + \
    "/secretsmanager/get?secretId=" + \
    os.environ.get('SecretARN')

MAX_LEN = os.environ.get('MAX_VALID_MINUTES', 1440) # 24 hrs
TEST_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC2iBW+s0Aadn/ncA9fUZUcQha7FEJJ0/892MW3Wy9bXTrMNMPf5sLsLIp+K3OO7QP+ynnCSZhTE+6F37wtYGpsPnsHf9tpc8aZKCd/eUCwnTCiWlTdEvo4AyL+hlqkpedGyBLbI6NMt/l3PEtqSirUt7pCmb9+Fg+VTKII1UUU8Rl4MGJAtHtltTwvtarJDTbhaoorlJYP4CEAR6z9MBaJXo09FffJQDhcOOAhawUHVRXdnD9aaLYpIc2QXnVx8k+i2aO95IWyd+sVUmEoHmdFoSXf6LR3TGeeoYfSwotLSOogK+MBfTWbq+5mm43TLhB2tr6BQEQnkMAJcZFb9T+LqM67pH0S3jBs2PlnMXlyCKHxrJBv6Bkjl1lWQ2BEj5UuFDQkqr5gXwXCsubpg6pG0g65vhohb7L2pOe2zOw++3jQDmDFS/22rnoxG2X2O0o+3uNTK1bzkS/2PzwMs2VgpY/iZTNFnSOxs7paSn+yaJJQQ87MwF3Gn1kFpC7qgSs= kali@kali"

def handler(event, context):
    print(event, context)
    res = requests.get(secrets_extension_endpoint, headers=headers).json()

    if 'length' in event.keys():
        duration = min(MAX_LEN, event['length'])
    else:
        duration = MAX_LEN    

    cert_fields = CertificateFields(
        serial=0,
        cert_type=1,
        key_id="someuser@somehost",
        principals=[event['username'], "converge"], # JESUS FUCK CHANGE THIS
        valid_after=datetime.now(),
        valid_before=datetime.now() + timedelta(minutes=duration),
        critical_options=[],
        extensions=[
            "permit-pty",
            "permit-X11-forwarding",
            "permit-agent-forwarding",
            "permit-port-forwarding",
            "permit-user-rc"
        ],
    )

    secret_value = json.loads(res['SecretString'])
    ca_privkey = PrivateKey.from_string(secret_value['private_key'])
    certificate = SSHCertificate.create(
        subject_pubkey=PublicKey.from_string(event['pubkey']),
        ca_privkey=ca_privkey,
        fields=cert_fields,
    )
    certificate.sign()
    return certificate.to_string()
