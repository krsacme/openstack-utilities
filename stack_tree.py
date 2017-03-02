#!/usr/bin/env python

import logging
import os
import subprocess
import sys

from heatclient.v1 import client as heatclient
from keystoneauth1.identity import v2
from keystoneauth1 import session
from keystoneclient.v2_0 import client

logging.basicConfig(level=logging.WARN)

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

def get_orchestration_client():
  OS_AUTH_URL = os.environ['OS_AUTH_URL']
  OS_USERNAME = os.environ['OS_USERNAME']
  OS_TENANT_NAME = os.environ['OS_TENANT_NAME']
  OS_PASSWORD = os.environ['OS_PASSWORD']
  auth = v2.Password(auth_url=OS_AUTH_URL,
                     username=OS_USERNAME,
                     password=OS_PASSWORD,
                     tenant_name=OS_TENANT_NAME)
  sess = session.Session(auth=auth)
  keystone = client.Client(session=sess)

  token = auth.get_token(session=sess)
  log.info("KRS: token: %s" % token)

  endpoint = auth.get_endpoint(sess,
                             service_name='heat', service_type='orchestration')
  log.info("KRS: endpoint: %s" % endpoint)
  return heatclient.Client(
      endpoint=endpoint,
      token=token,
  )

def main():
  log.info("KRS: Testing")
  hc = get_orchestration_client()
  stacks = hc.stacks.get('overcloud')
  log.info(stacks)


if __name__ == "__main__":
  main()