
```
(base) localhost:profile-platform wy$ git push origin main
ssh: connect to host github.com port 22: Operation timed out
fatal: Could not read from remote repository.

Please make sure you have the correct access rights
and the repository exists.
```


```
(base) localhost:.ssh wy$ ssh -T -p 443 git@ssh.github.com
The authenticity of host '[ssh.github.com]:443 ([20.205.243.160]:443)' can't be established.
ED25519 key fingerprint is SHA256:+DiY3wvvV6TuJJhbpZisF/zLDA0zPMSvHdkr4UvCOqU.
This host key is known by the following other names/addresses:
    ~/.ssh/known_hosts:2: github.com
Are you sure you want to continue connecting (yes/no/[fingerprint])? yes
Warning: Permanently added '[ssh.github.com]:443' (ED25519) to the list of known hosts.
Hi sjf0115! You've successfully authenticated, but GitHub does not provide shell access
```
