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
