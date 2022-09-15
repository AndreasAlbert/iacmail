# iacmail

## Setup

```bash
git clone git@github.com:AndreasAlbert/iacmail.git
cd iacmail
mamba env create
pip install -e --no-deps .
```

## Usage

Prepare a file containting the message body:

```bash
$ cat message.txt
> Hi,
> this is a test message
```

Prepare a file containg the recipient addresses one per line:

```bash
$ cat addresses.txt
> some@email.com
> some_other@email.com
```

Prepare a file containing one-off configurations:

```bash
$ cat user_config.yaml
> sender_email: me@myhost.com
> smtp_server: smtp.myhost.com
> smtp_port: 587
> password: "mypassword"
```

If you don't want to save your password in the configuration file, you can also omit it. In that case, the script will prompt you for your password at runtime. You will have to retype it for every run.

Use the command line utility:

```bash
iacmail --address-file=address_file.txt --message-file=message.txt --subject="test subject 123" --user-config-file=user_config.yml
```

The tool will send the same email body and subject to each recipient in the address file.
An SQLite database is used to keep track of sending attempts. If sending fails, simply re-execute the script. The same message will not be sent to the same recipient multiple times (as long as the message body is unchanged).