cd ../../
if [[ -e "root_uclchem" ]]; then
echo "you already installed root uclchem"
else
git clone git@github.com:uclchem/uclchem root_uclchem
fi