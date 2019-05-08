# CTFd OCTP Plugin
Aims to easily integrate into CTFd, without the need for hacky solutions.

# Testing the plugin
Testing the plugin simple requires you to build the Dockerfile using 

```
docker build -t ctfd-octp .
```

Now create a file called `envfile`, with the following input (change to your needs):

```
OCTP_ENABLE=true
OCTP_URL=http://127.0.0.1:8000
OCTP_ENABLE_LABS=true
OCTP_ENABLE_FRONTENDS=true
OCTP_ENABLE_INTERCEPT=false
```

Where after the following command can be run, which will override the octp plugin directory in the container.

```
docker run --rm -it -v $(pwd)/src:/opt/CTFd/CTFd/plugins/octp --net=host --env-file envfile --entrypoint=sh ctfd-octp
```

Now just run `python server.py`, and you should be able to visit `http://127.0.0.1:4000`, enjoy!
