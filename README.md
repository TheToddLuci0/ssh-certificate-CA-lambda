# What the hell is this?
SSH is great. Using keys is great. Managing ssh keys is not.

Fortunatly, SSH has a handy little tool to let us bypass that problem: certificate auth.

It works like this: you install a certificate on your host and tell SSH that anything signed by that cert is legit, let 'em in.
That just leaves one problem: how to sign the cert? That's where this comes in.

## Deploying

Note: you need to deploy a secret manager secret with the CA keys in it first.

```json
{
    "public_key": "asdasdadasdasdasd",
    "private_key": "-------BEGIN PRIVATE KEY---------- asdwqdas...."
}
```

Once you have that it's as simple as running `cdk deploy --parameters secretarn=arn:aws:....`

Note: The parameter is only required the first time you deploy. After that, you can apply updates with just `cdk deploy`

## Invoking
We now have a client!

[![asciicast](https://asciinema.org/a/ZEtn43ImOdvQpW6wQHF5jXUva.svg)](https://asciinema.org/a/ZEtn43ImOdvQpW6wQHF5jXUva)

### Manual
Call `invoke` via your favorite AWS lambda interface, with the following event data:

```json

{
    "length": 15, // How long the cert should be valid for. If you pass a value larger than the lambda max, that will be used
    "username": "bob@corp.com", // Who to indicate the cert is for TODO: replace this with non-user supplied info
    "pubkey": "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC2iBW+s0Aadn/ncA9fUZUcQha7FEJJ0/892MW3Wy9bXTrMNMPf5sLsLIp+K3OO7QP+ynnCSZhTE+6F37wtYGpsPnsHf9tpc8aZKCd/eUCwnTCiWlTdEvo4AyL+hlqkpedGyBLbI6NMt/l3PEtqSirUt7pCmb9+Fg+VTKII1UUU8Rl4MGJAtHtltTwvtarJDTbhaoorlJYP4CEAR6z9MBaJXo09FffJQDhcOOAhawUHVRXdnD9aaLYpIc2QXnVx8k+i2aO95IWyd+sVUmEoHmdFoSXf6LR3TGeeoYfSwotLSOogK+MBfTWbq+5mm43TLhB2tr6BQEQnkMAJcZFb9T+LqM67pH0S3jBs2PlnMXlyCKHxrJBv6Bkjl1lWQ2BEj5UuFDQkqr5gXwXCsubpg6pG0g65vhohb7L2pOe2zOw++3jQDmDFS/22rnoxG2X2O0o+3uNTK1bzkS/2PzwMs2VgpY/iZTNFnSOxs7paSn+yaJJQQ87MwF3Gn1kFpC7qgSs= kali@kali" // Do I really need to explain this one?
}
```

CLI example:
```bash
aws lambda invoke --function-name arn:aws:lambda:us-east-1:XXXXXXXX:function:LambdaSshSignStack-SSHKeySigner8 --payload file://payload.json test.out
```

# TODO
- [x] Write a client for the normies
- [x] Determine usernames based on the IAM identity of the caller, rather than user-supplied
- [ ] Document server setup