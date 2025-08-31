# fetch config
ansible-navigator run fetch.yaml --mode stdout

git config --global user.name "Arslan Khan"
git config --global user.email "arslankhanali@gmail.com"

git init
git commit -m "first commit"
git branch -M main
git remote add origin https://github.com/arslankhanali/demo-ansible-network.git
git push -u origin main