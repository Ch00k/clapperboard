#!/bin/bash

if [[ -f ~/.cb_ansible.cfg ]]; then
    echo "Using config ~/.cb_ansible.cfg"
    ansible-playbook -i production site.yml -e "@~/.cb_ansible.cfg"
else
    echo "Using default config"
    ansible-playbook -i production site.yml
fi