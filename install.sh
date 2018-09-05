#!/bin/bash
pip install -r requirements.txt --user

echo ""
read -n1 -p "Install nvidia-smi to monitor GPU RAM? [y,n]" gpu
case $gpu in
  y|Y) sudo apt install nvidia-smi ;;
  *) echo "" ;;
esac
