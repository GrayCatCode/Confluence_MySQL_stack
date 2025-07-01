#!/bin/bash

# Add the `stack` user to the OS:
sudo useradd -s /bin/bash -d /opt/stack -m stack

# Make the `stack` user's home directory executable:
sudo chmod +x /opt/stack

# Put the `stack` user in the `wheel` group for sudo access:
echo "stack ALL=(ALL) NOPASSWD: ALL" | sudo tee /etc/sudoers.d/stack

# Change to the `stack` user:
sudo -u stack -i

# Make a directory for git repos:
mkdir Git_repos
cd Git_repos

# Download DevStack:
#git clone https://opendev.org/openstack/devstack
git clone https://git.openstack.org/openstack-dev/devstack

# Copy the `local.conf` file into the `devstack` directory:
cp ~/local.conf devstack

# Change into the `devstack` directory:
cd devstack