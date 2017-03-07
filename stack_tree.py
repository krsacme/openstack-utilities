#!/usr/bin/env python

import logging
import os
import subprocess
import sys
import yaml

from heatclient.common import utils
from heatclient.v1 import client as heatclient
from keystoneauth1.identity import v2
from keystoneauth1 import session
from keystoneclient.v2_0 import client

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(message)s')
ch.setFormatter(formatter)
log.addHandler(ch)

_HEAT_SOFTWARE_CONFIG_TYPE = 'OS::Heat::SoftwareConfig'

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
  #log.info("KRS: token: %s" % token)

  endpoint = auth.get_endpoint(sess,
                               service_name='heat',
                               service_type='orchestration')
  #log.info("KRS: endpoint: %s" % endpoint)
  return heatclient.Client(
      endpoint=endpoint,
      token=token,
  )

def traverse(hc, stack_id, sc_list):
  global _HEAT_SOFTWARE_CONFIG_TYPE
  res_map = {}

  stack_id = stack_id.split('/')[0]

  resources = hc.resources.list(stack_id)
  for resource in resources:
    if 'resources' not in res_map:
      res_map['resources'] = {}

    log.debug("resource: type: %s" % resource.resource_type)

    res_info = {}
    nested_id = utils.resource_nested_identifier(resource)
    if nested_id:
      nested_id = nested_id.split('/')[0]
      nested_res_list = traverse(hc, nested_id, sc_list)
      res_info.update({'stacks': {nested_id: nested_res_list}})

    res_info.update({'type': resource.resource_type})
    if resource.resource_type == _HEAT_SOFTWARE_CONFIG_TYPE:
      for sc in sc_list:
        if resource.resource_name in sc.name:
          res_info.update({'software_config': sc.name})
          res_info.update({'group': sc.group})
          break

    res_map['resources'].update({resource.resource_name: res_info})

  return res_map

def main():
  hc = get_orchestration_client()
  stack_id = 'overcloud'
  stack = hc.stacks.get(stack_id)
  # software config list
  sc_list = hc.software_configs.list()
  log.info(stack.identifier)
  stack_tree = {}
  stack_tree.update(traverse(hc, stack_id, sc_list))
  log.info(yaml.safe_dump(stack_tree, encoding='utf-8', allow_unicode=True, default_flow_style=False))


if __name__ == "__main__":
  main()