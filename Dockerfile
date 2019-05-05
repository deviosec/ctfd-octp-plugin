FROM ctfd/ctfd:latest

# add python-octp api
RUN python -m pip install --user git+https://github.com/deviosec/python-octp.git

# copy plugin into plugins and rename it
COPY src /opt/CTFd/CTFd/plugins/octp

