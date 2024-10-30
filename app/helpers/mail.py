from fastapi_mail import ConnectionConfig, FastMail, MessageSchema, MessageType

from app.settings import EmailEnv

conf = ConnectionConfig(
    MAIL_USERNAME=EmailEnv.MAIL_USERNAME,
    MAIL_PASSWORD=EmailEnv.MAIL_PASSWORD,
    MAIL_FROM=EmailEnv.MAIL_FROM,
    MAIL_PORT=EmailEnv.MAIL_PORT,
    MAIL_SERVER=EmailEnv.MAIL_SERVER,
    MAIL_STARTTLS=EmailEnv.MAIL_STARTTLS,
    MAIL_SSL_TLS=EmailEnv.MAIL_SSL_TLS,
    USE_CREDENTIALS=EmailEnv.USE_CREDENTIAL,
    TEMPLATE_FOLDER="./app/templates",
)


async def send_mail(subject: str, email_to: str, body: dict, template: str):
    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message, template_name=f"{template}.html")
