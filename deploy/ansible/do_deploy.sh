#!/bin/bash

if [[ -f $HOME/.cb_ansible.cfg ]]; then
    echo "Using config ~/.cb_ansible.cfg"
    ansible-playbook -i production site.yml -e "@$HOME/.cb_ansible.cfg" --ask-sudo-pass
else
    echo "Using default config"
    ansible-playbook -i production site.yml --ask-sudo-pass
fi