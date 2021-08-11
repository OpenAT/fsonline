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

  1. explicitly setting --env=['DEV' | 'STG' | 'PRD'] for supported invoke tasks
  2. an environment variable called FSONLINE_ENVIRONMENT="['DEV' | 'STG' | 'PRD']"
  3. in any of the environment files FSONLINE_ENVIRONMENT="['DEV' | 'STG' | 'PRD']"
  4. if none of the above is set the default will be "DEV"

## Tools overview
The tools in use. Make sure you have at least a basic understanding of what they are for.

- python *(3.9 for tooling on the dev host and > 3.6 for odoo venv)*
    - pip
    - venv
    - pipx
    - poetry
    - pydantic
    - invoke
    - copier
    - click (for click-odoo stuff)
- git 
- github
- docker / docker-compose
- pydantic
- yaml, jina, *.env, *.conf, markdown
- odoo
- click-odoo
- click-odoo-contrib
- pycharm
- vs-code

Additional tools
    
- [flake8](https://flake8.pycqa.org/en/latest/)
- [black](https://black.readthedocs.io/en/stable/)
- [pre-commit](https://pre-commit.com/)
- [pylint](http://pylint.pycqa.org/en/latest/#)
- [duplicity](http://duplicity.nongnu.org/)
- [docker-duplicity](https://github.com/Tecnativa/docker-duplicity)
- [nginx](https://nginx.org/en/docs/)
- [traefik(2)](https://doc.traefik.io/traefik/)
- [postgresql](https://www.postgresql.org/docs/)
