#!/usr/bin/env python3

from jinja2 import Template
import json
import os, sys, os.path
import random
import string
import urllib.request
import argparse
import configparser

def random_gen(size=32, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
  return ''.join(random.choice(chars) for x in range(size))

def load_template(template_url):
  # load_template - downloads from url provided and returns the data
  with urllib.request.urlopen(template_url) as response:
    data = response.read()
    result = data.decode('utf-8')
  return result

def save_config(configData, confFile):
  with open(confFile, 'w') as outfile:
    #out.write(data, outfile)
    outfile.write(configData)
  return

walletconfj2_url = "https://raw.githubusercontent.com/BlocknetDX/blocknet-docs/master/json-config-templates/wallet.conf.j2"
xbridgeconfj2_url = "https://raw.githubusercontent.com/BlocknetDX/blocknet-docs/master/json-config-templates/xbridge.conf.j2"

def chain_lookup(s):
  return "https://raw.githubusercontent.com/BlocknetDX/blocknet-docs/master/json-config-templates/{}.json.j2".format(s.lower())

def generate_confs(blockchain, p2pport, rpcport, configname, username, password, chaindir, blocknetdir, blockdxdir):
  if blockchain:
    if len(blockchain) > 1:
      if p2pport:
        print("Warning: parameter --p2pport ignored because multiple blockchains were selected.")
      if rpcport:
        print("Warning: parameter --rpcport ignored because multiple blockchains were selected.")
      if chaindir:
        print("Warning: parameter --chaindir ignored because multiple blockchains were selected.")
      if configname:
        print("Warning: parameter --configname ignored because multiple blockchains were selected.")
      p2pport = rpcport = configname = chaindir = None
    if chaindir is None:
      chaindir = '.'
    if blocknetdir is None:
      blocknetdir = '.'
    if blockdxdir is None:
      blockdxdir = '.'
    for blockchain in blockchain:
      if username is None:
        rpcuser = random_gen()
      else:
        rpcuser = username
      if password is None:
        rpcpass = random_gen()
      else:
        rpcpass = password
      # find the URL for the chain
      try:
        xbridge_text = load_template(chain_lookup(blockchain))
      except urllib.error.HTTPError as e:
        print("Config for currency {} not found".format(blockchain))
        continue
      xbridge_json = json.loads(xbridge_text)
      xtemplate = Template(xbridge_text)
      params = {}
      if args.p2pport:
        params['p2pPort'] = p2pport
      if args.rpcport:
        params['rpcPort'] = rpcport
      xresult = xtemplate.render(rpcusername=rpcuser, rpcpassword=rpcpass, **params)
      xbridge_json = json.loads(xresult)

      confFile = list(xbridge_json.values())[0]['Title'].lower()
      if configname:
        confFile = args.configname.lower()
      
      # generate wallet config
      for x in xbridge_json: p2pport = (xbridge_json[x]['p2pPort'])
      for x in xbridge_json: rpcport = (xbridge_json[x]['rpcPort']) 
      res_conf = load_template(walletconfj2_url)  
      template = Template(res_conf)
      result = template.render(rpcusername=rpcuser, rpcpassword=rpcpass, p2pPort=p2pport, rpcPort=rpcport)
      if args.daemon:
        result += "\ndaemon=1"
      save_config(result, os.path.join(chaindir, '%s.conf' % confFile))
        
      # generate xbridge config
      xbridge_config = load_template(xbridgeconfj2_url)
      #f = open("xbridge.conf.j2", "r")
      #xbridge_config = f.read()
      xbridge_template = Template(xbridge_config)
      xbridge_result = xbridge_template.render(blockchain=blockchain, val=list(xbridge_json.values())[0])
      save_config(xbridge_result, os.path.join(blocknetdir, confFile+'-xbridge.conf'))
      
      if blockchain == "BLOCK":
        # Generate meta.json here
        d = {
                "addresses": {},
                "tos": True,
                "port": int(rpcport),
                "password": rpcpass,
                "user": rpcuser
            }
        save_config(json.dumps(d, indent=4), os.path.join(blockdxdir, 'meta.json'))
        
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='blockdx-conf-gen')
  parser.add_argument('--verbose', action='store_true', help='verbose flag' )

  # Add arguments
  parser.add_argument('-c', '--blockchain', type=str, help='Blockchain config to download', required=True, nargs = '*')
  parser.add_argument('-p2p', '--p2pport', type=str, help='p2pport override', required=False, default=None)
  parser.add_argument('-rpc', '--rpcport', type=str, help='rpcport override', required=False, default=None)
  parser.add_argument('-n', '--configname', type=str, help='config file name', required=False, default=None)
  parser.add_argument('-u', '--username', type=str, help='RPC username, random by default', required=False, default=None)
  parser.add_argument('-p', '--password', type=str, help='RPC password, random by default', required=False, default=None)
  parser.add_argument('-cdir', '--chaindir', type=str, help='Chain config directory', required=False, default=None)
  parser.add_argument('-bdir', '--blocknetdir', type=str, help='Blocknet config directory', required=False, default=None)
  parser.add_argument('-ddir', '--blockdxdir', type=str, help='BlockDX config directory', required=False, default=None)
  parser.add_argument('--daemon', action='store_true', help='Run as daemon', required=False)

  args = parser.parse_args()
  generate_confs(args.blockchain, args.p2pport, args.rpcport, args.configname, args.username, args.password, args.chaindir, args.blocknetdir, args.blockdxdir)
