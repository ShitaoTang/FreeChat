This is a chatroom for chatting freely.

Just input the follwing command in your termianl (on Linux, MacOS or Windows):

```bash
ssh -t chat@www.tstwiki.cn [username]
```

where the "[username]" is optional. If left blank, your nick name would be "Anonymous".

Actually, there is another command, but this Alibaba Cloud server (domain name tstwiki.cn) will expire on June 19, 2024. However, the domain name www.tstwiki.cn still has one year left. When the former expires, I will also use the domain name tstwiki.cn for the latter server.

```bash
ssh -t chat@tstwiki.cn [username]
```

## File Structure

```
FreeChat
├── client.py           # 聊天室客户端代码
├── Dockerfile          # 部署Docker的配置文件
├── LICENSE
├── readme.md
├── requirements.txt    # 依赖库
└── server.py           # 聊天室服务器代码
```

## usage

Python version: 3.11.3

```bash
git clone -b local_debian git@github.com:ShitaoTang/FreeChat.git

cd FreeChat

# create python virtual environment
python -m venv .venv

# acticate the venv
# if using bash shell or zsh shell
source .venv/bin/activate
# if using fish shell
source .venv/bin/activate.fish

# install modules
pip install -r requirements.txt
```

Run the server.
```bash
python server.py
```

Open a new terminal in a new window and make sure it is the full mode. Then run the client.
```bash
python client.py
```
