# iacmail

## Setup

```bash
git clone git@github.com:AndreasAlbert/iacmail.git
cd iacmail
mamba env create
mamba activate iacmail
pip install -e --no-deps .
```

## One-off configuration

We need a file containing one-off configurations:

```yaml
sender_email: me@myhost.com
smtp_server: smtp.myhost.com
smtp_port: 587
password: mypassword
```

If you don't want to save your password in the configuration file, you can also omit it. In that case, the script will prompt you for your password at runtime. You will have to retype it for every run.


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

Finally, let's use the command line utility:

```bash
iacmail  --table-path ./recipients.xlsx \
         --address-column "email" \
         --message-file message.txt \
         --user-config-file user_config_aa.yml \
         --subject "My test subject"
```

An SQLite database is used to keep track of sending attempts. If sending fails, simply re-execute the script. The same message will not be sent to the same recipient multiple times (as long as the message body is unchanged).

## Using an HTML body

The email body will be rendered as HTML if you specify the `--html` flag on the commandline

## Adding attachments

### Same attachment for every recipient
You can attach files by specifying `--attachments` on the commandline, e.g."
```
iacmail ... --attachments /path/to/the/attachment.whatever
```

In this case, all recipients will get the same file sent to them

### Different attachments for different recipients

You can specify `--attachment-from-column ${NAME_OF_COLUMN}` on the commandline to automatically read the path to the attachment file from the input sheet. In this case, you can specify a different attachment path for every recipient in the input sheet. For example, your sheet could look like this:

| name  | email           | attachment |
| ----- | --------------- | ---------- |
| Alice | alice@gmail.com | /path/to/file1.txt |
| Bob   | bob@gmail.com   | /path/to/file2.pdf |

In this case, you would call `iacmail ... --attachment-from-column "attachment"`.