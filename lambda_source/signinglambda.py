# Every certificate needs two parts, the subject (user or host) public key and the CA Private key
from sshkey_tools.cert import SSHCertificate, CertificateFields
from sshkey_tools.keys import PrivateKey, PublicKey
from sshkey_tools.fields import RsaSignatureField
from cryptography.hazmat.primitives.serialization.base import load_der_public_key
from datetime import datetime, timedelta
import requests
import json
import boto3
import os
import sys
from urllib.parse import urlparse
import xml.etree.ElementTree as ET


headers = {"X-Aws-Parameters-Secrets-Token": os.environ.get('AWS_SESSION_TOKEN')}
MAX_LEN = int(os.environ.get('MAX_VALID_MINUTES', 1440)) # 24 hrs
TEST_KEY = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC2iBW+s0Aadn/ncA9fUZUcQha7FEJJ0/892MW3Wy9bXTrMNMPf5sLsLIp+K3OO7QP+ynnCSZhTE+6F37wtYGpsPnsHf9tpc8aZKCd/eUCwnTCiWlTdEvo4AyL+hlqkpedGyBLbI6NMt/l3PEtqSirUt7pCmb9+Fg+VTKII1UUU8Rl4MGJAtHtltTwvtarJDTbhaoorlJYP4CEAR6z9MBaJXo09FffJQDhcOOAhawUHVRXdnD9aaLYpIc2QXnVx8k+i2aO95IWyd+sVUmEoHmdFoSXf6LR3TGeeoYfSwotLSOogK+MBfTWbq+5mm43TLhB2tr6BQEQnkMAJcZFb9T+LqM67pH0S3jBs2PlnMXlyCKHxrJBv6Bkjl1lWQ2BEj5UuFDQkqr5gXwXCsubpg6pG0g65vhohb7L2pOe2zOw++3jQDmDFS/22rnoxG2X2O0o+3uNTK1bzkS/2PzwMs2VgpY/iZTNFnSOxs7paSn+yaJJQQ87MwF3Gn1kFpC7qgSs= kali@kali"
SHARED_USER = os.environ.get('SHARED_USER_ID')
USE_FRIENDLY = bool(os.environ.get('USE_FRIENDLY_KEY_ID', False))
KEY_ARN = os.environ.get('KMS_KEY_ARN')

def handler(event, context):
    print(event, context)

    if 'length' in event.keys():
        # Make sure that we're not issuing lifetime certificates
        duration = min(MAX_LEN, event['length'])
    else:
        duration = MAX_LEN    

    # Use STS to get authoritive data on who we're creating certs for
    if urlparse(event['stsurl']).netloc.lower() != 'sts.amazonaws.com':
        # Prevent people forging certs by sending requests to attacker-controlled hosts
        return "'stsurl' must use 'sts.amazonaws.com'"
    sts_response = requests.post(event['stsurl'])
    tree = ET.fromstring(sts_response.content)
    full_user_id = tree.find('.//{https://sts.amazonaws.com/doc/2011-06-15/}UserId').text

    cert_fields = CertificateFields(
        serial=0,
        cert_type=1,
        key_id="someuser@somehost", #todo fix
        principals=[],
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

    cert_fields.principals.value.append(full_user_id)
    cert_fields.key_id.value = full_user_id

    if SHARED_USER is not None:
        cert_fields.principals.value.append(SHARED_USER)
    try:
        cert_fields.principals.value.append(full_user_id.split(':')[1])
        if USE_FRIENDLY:
            cert_fields.key_id.value=full_user_id.split(':')[1]
    except:
        # Must not be an identity center user?
        pass

    # Log what we're signing for tracability
    print(cert_fields)
    certificate = SSHCertificate.create(
        subject_pubkey=PublicKey.from_string(event['pubkey']),
        fields=cert_fields,
    )

    kms = boto3.client('kms')

    _kms_pubkey = kms.get_public_key(KeyId=KEY_ARN)
    k = load_der_public_key(_kms_pubkey['PublicKey'], None)
    PubKey = PublicKey.from_class(k)
    certificate.footer.ca_pubkey = PubKey
    sig = kms.sign(KeyId=KEY_ARN, Message=certificate.get_signable(), MessageType='RAW', SigningAlgorithm='RSASSA_PKCS1_V1_5_SHA_512')
    sf = RsaSignatureField(signature=sig['Signature'])
    certificate.footer.signature = sf
    # TODO log cert fingerpring
    if not certificate.verify():
        sys.exit(1) # TODO
    return certificate.to_string()
