# iacmail

## Setup

```bash
git clone git@github.com:AndreasAlbert/iacmail.git
cd iacmail
mamba env create
mamba activate iacmail
pip install -e --no-deps .
```

## Usage


Prepare an excel sheet containing one row for each recipient:

```bash
$ ls recipients.xlsx
```

For example, the sheet could look like this:

| name  | email           |
| ----- | --------------- |
| Alice | alice@gmail.com |
| Bob   | bob@gmail.com   |

We write our email body into a text file:

```bash
Hi {name},

your email address is {email}.

Best,

X
```

Fields enclosed in braces will be replaced with the appropriate values from the input sheet.

Then, we need a file containing one-off configurations:

```bash
$ cat user_config.yaml
> sender_email: me@myhost.com
> smtp_server: smtp.myhost.com
> smtp_port: 587
> password: "mypassword"
```

If you don't want to save your password in the configuration file, you can also omit it. In that case, the script will prompt you for your password at runtime. You will have to retype it for every run.

Finally, let's use the command line utility:

```bash
iacmail  --table-path ./recipients.xlsx \
         --address-column "email" \ 
         --message-file message.txt \
         --user-config-file user_config_aa.yml \
         --subject "My test subject" \
```

You can also use the `--html` flag if you want to use an html email body.

An SQLite database is used to keep track of sending attempts. If sending fails, simply re-execute the script. The same message will not be sent to the same recipient multiple times (as long as the message body is unchanged).

