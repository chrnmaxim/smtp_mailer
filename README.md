# SMTP Mailer

Asynchronous SMTP mailer that uses `aiosmtplib`

## Usage as executable
1. Download `smtp_mailer.exe` from releases page and place it in a separate directory.

2. Create `config.ini` based on `config_example.ini` entering your SMTP server credentials and place it next to the `smtp_mailer.exe`
> [!NOTE]
> Read your SMTP setup guide to find the correct hostname and port.
>
> By default, hostname and port are set for [mail.ru SMTP](https://help.mail.ru/mail/faq/other/tune/).
>
> You might need to create a new password for an external application. Here's an [example for mail.ru](https://help.mail.ru/mail/mailer/password/).

3. Create `recipients.csv` based on the existing `recipients_example.csv` and specify the path to it in the `config.ini`.

The `recipient_name` field is optional. It is used to format the email body. For example, if there is `{name}` argument in message body:
```
Hello, {name}!
```
It would be replaced with `recipient_name`:
```
Hello, world!
```

If there is no `recipient_name` for a recipient, but message body contains `{name}`, then `{name}` would be replaced with and empty string:
```
Hello, !
```

> [!IMPORTANT]
> The number of recipients is unlimited, so it is essential to consider your SMTP provider's limitations and terms of usage. Mail.ru, for example, has detailed [rules for sending emails](https://help.mail.ru/developers/mailing_rules/).
