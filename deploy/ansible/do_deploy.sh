#!/bin/bash

if [[ -f $HOME/.cb_ansible.cfg ]]; then
    echo "Using config ~/.cb_ansible.cfg"
    ansible-playbook -vvvvvv -i production site.yml -e "@$HOME/.cb_ansible.cfg"
else
    echo "Using default config"
    ansible-playbook -i production site.yml
fi