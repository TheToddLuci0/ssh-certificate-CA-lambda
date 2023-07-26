import boto3
import argparse
import configparser
import logging
import os
import json


def main(config):
    profile = None
    region = None
    if config['DEFAULT']['profile'] is not None:
        profile = config['DEFAULT']['profile']
    if config['DEFAULT']['region'] is not None:
        region = config['DEFAULT']['region']
    session = boto3.Session(profile_name=profile, region_name=region)
    _lambda = session.client('lambda')
    sts = session.client('sts')
    req = sts.generate_presigned_url('get_caller_identity')
    with open(os.path.expanduser(config['DEFAULT']['identity_file']), 'r') as keyfile:
        key = keyfile.read()
    payload = {
        'stsurl': req,
        'length': int(config['DEFAULT']['valid_for']),
        'pubkey': key,
        'username': os.getlogin()
    }
    response = _lambda.invoke(FunctionName=config['DEFAULT']['lambda_arn'], Payload=json.dumps(payload))
    cert = response['Payload'].read()
    cert_file = os.path.expanduser(config['DEFAULT']['identity_file']).replace('.pub', '-cert.pub')
    if not cert_file.endswith('-cert.pub'):
        logging.error("Something has gone horribly wrong, bailing to not destroy secret keys!")
        os.exit(99)
    logging.info("Writing cert to " + cert_file)
    with open(cert_file, 'w') as f:
        f.write(cert.decode('utf-8').replace('"', ""))
    


if __name__ == '__main__':
    config = configparser.ConfigParser()
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--valid-for', help="How long the cert should be valid for. Note: if the server has a lower max set than you request, the server will win.")
    parser.add_argument('-i', '--identity-file', help="Public key to sign")
    parser.add_argument('--lambda-arn', help="ARN of the signing lambda")
    parser.add_argument('--profile', help="AWS profile to use")
    parser.add_argument('--region', help="AWS region name (ie us-east-1)")
    
    # Options for config file
    config_opts = parser.add_argument_group("Config Options")
    config_opts.add_argument('--save', action='store_true', help="Save the command line args to a config file")
    config_opts.add_argument('-c', '--config', default='~/.config/ssh-key-sign.ini', help="Config file to use")


    args = parser.parse_args()
    config_path = os.path.expanduser(args.config)
    config.read(config_path)
    logging.debug(args.__dict__)
    config.read_dict({"DEFAULT": {k:v for k,v in args.__dict__.items() if v is not None}})
    if args.save:
        logging.info("Writing config to {}".format(config_path))
        # We don't need to save these
        config.remove_option('DEFAULT', 'config')
        config.remove_option('DEFAULT', 'save')
        with open(config_path, 'w+') as conffile:
            config.write(conffile)
    logging.debug(config.__dict__)
    if config['DEFAULT']['identity_file'] is None:
        logging.error("Must have a key to sign!")
        os.exit(5)
    main(config)