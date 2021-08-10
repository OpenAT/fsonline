# FS-Online Docker Image

## Install submodules with odoo addons and/or odoo itself
```
# 1.) Create a folder for each github account in src (e.g. OCA)
# 2.) cd into the Github Account Folder and add the addon repos of the github account like this:
cd src/OCA
git submodule add -b "14.0" https://github.com/OCA/OCB.git
git submodule add -b "14.0" https://github.com/OCA/web.git
git submodule add -b "14.0" https://github.com/OCA/project.git
...
```

## Setting the environment
You can set/force the environment to use/load either by

  1. explicitly setting the argument when creating the env (env="")
  2. an environment variable called FSONLINE_ENVIRONMENT=""
  3. an environment file called ".env" with FSONLINE_ENVIRONMENT="" in it
  4. if none is given the default for env is "DEV"
