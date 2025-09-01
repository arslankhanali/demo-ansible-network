cd /Users/arslankhan/Codes/demo.redhat.com/Ansible-AcademySessions/demo-ansible-network

## Git clone and test push

```sh
git clone https://github.com/arslankhanali/demo-ansible-network.git
cd demo-ansible-network

git config --global user.name "Arslan Khan"
git config --global user.email "arslankhanali@gmail.com"

git add .
git commit -m "update motd"
git push


# Gitignore setup
tee .gitignore > /dev/null <<EOL
.*
*.json
backup/
EOL

git rm -r --cached .

```

### Login to cisco router - CLI
```sh
ssh rtr1
sh run
exit
```

### Login to cisco router - Web
```sh
# Get IP for rtr1
cat /etc/hosts

https://3.137.184.95

# Create an account to login
ssh rtr1

conf t
username admin privilege 15 secret STRONGPASSWORD
ip http authentication local
end
wr mem
```
---

## Demo Start
When running a playbook with ansible-navigator run, you can use the --pae false (or --playbook-artifact-enable false)

### Set motd
```sh
ssh rtr1

conf t
banner motd #
Demo for Services Austraila
#
end
wr mem
```

### fetch config
```sh
ansible-navigator run 1-fetch.yaml --mode stdout --pae false
```

### apply config
```sh
ansible-navigator run 2-apply.yaml --mode stdout --pae false
```

### apply config from git
```sh
git add .
git commit -m "updated motd"
git push

ansible-navigator run  --mode stdout 3-apply-git.yaml --pae false

ssh rtr1

```
### delete
rm *.json
rm -r backup/


### Webhook
https://student1.ml647.example.opentlc.com/api/controller/v2/job_templates/17/github/
XB19ekQp6FvQPIOpbXY5GQmWaCprZnOxNqgvjAXdJKRVaWHJfu



### API
https://student1.ml647.example.opentlc.com/api/controller/v2/


curl --location --request POST 'https://<your_aap_url>/api/v2/projects/' \
--header 'Content-Type: application/json' \
--header 'Authorization: Bearer <your_access_token>' \
--data-raw '{
  "name": "My New Project",
  "organization": 1,
  "scm_type": "git",
  "scm_url": "https://github.com/my-user/my-repo.git"
}'

curl -u admin:43l7dlaf -k -X POST https://student1.ml647.example.opentlc.com/api/controller/v2/tokens/

uLeAKJPOevkDrl9fkkXiyNdymjHpQS


## app
pip install flask
pip install Werkzeug

chmod u+r rtr1_config.txt

python app.py


### PR
git checkout main
git pull
git checkout -b update-rtr1-config
git add rtr1_config.txt
git commit -m "Update hostname and banner in rtr1 config"
git push -u origin update-rtr1-config

git checkout main
git pull