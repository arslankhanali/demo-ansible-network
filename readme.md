### New user to login
```sh
conf t
username admin privilege 15 secret STRONGPASSWORD
ip http authentication local
end
wr mem
```

### Set motd
```sh
ssh rtr1

conf t
banner motd
Welcome to demo
end
wr mem
```


### fetch config
ansible-navigator run 1-fetch.yaml --mode stdout


### apply config
ansible-navigator run 2-apply.yaml --mode stdout