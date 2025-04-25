import email
import imaplib
import os
import sys
from email.header import decode_header

from mcp.server.fastmcp import FastMCP
from rich import print


def download_attachments_by_message_id(
    mail_server, username, password, message_id, download_folder
) -> list[str]:
    """
    Download attachments from a Gmail message by message_id to a specified download_folder.
    Args:
        mail_server (str): The IMAP server address.
        username (str): The email account username.
        password (str): The email account password.
        message_id (str): The message ID of the email to download attachments from.
        download_folder (str): The folder to save the downloaded attachments.
    Returns:
        list[str]: A list of file paths of the downloaded attachments.
    Raises:
        ValueError: If the message ID is not a valid hexadecimal string.
        imaplib.IMAP4.error: If there is an error with the IMAP connection.
    """
    try:
        message_id_int = int(message_id, 16)

        mail = imaplib.IMAP4_SSL(mail_server)
        mail.login(username, password)
        mail.select("inbox")

        # Gmail stores the message-id in the X-GM-MSGID attribute, search like this:
        search_criteria = f'X-GM-MSGID "{message_id_int}"'
        typ, data = mail.search(None, search_criteria)

        # Fetch the mail if found
        if data[0]:
            for num in data[0].split():
                typ, msg_data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])

                # Save attachments
                for part in msg.walk():
                    content_disposition = part.get("Content-Disposition")
                    if part.get_content_maintype() == "multipart":
                        continue
                    if content_disposition:
                        dispositions = content_disposition.strip().split(";")
                        if any(
                            disposition.strip().lower() == "attachment"
                            for disposition in dispositions
                        ):
                            filename = part.get_filename()
                            if filename:
                                filename, enc = decode_header(filename)[0]
                                if isinstance(filename, bytes):
                                    filename = filename.decode(enc if enc else "utf-8")
                                filepath = os.path.join(download_folder, filename)
                                with open(filepath, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                                print(
                                    "Downloaded attachment to file ",
                                    filepath,
                                    file=sys.stderr,
                                )
            return [
                os.path.join(download_folder, part.get_filename())
                for part in msg.walk()
                if part.get_content_disposition()
            ]
        else:
            print("No email found with that message ID.", file=sys.stderr)
            return []

    except ValueError:
        print(
            "Invalid message ID format. Please provide a valid hexadecimal string.",
            file=sys.stderr,
        )
    except imaplib.IMAP4.error as e:
        print(f"IMAP error: {e}", file=sys.stderr)
    finally:
        mail.logout()


mcp = FastMCP(
    "gmail-attachment-mcp-server",
)


@mcp.tool()
def download_attachments_tool(
    message_id: str, download_folder="./attachments"
) -> list[str]:
    """
    Download attachments from a Gmail message by message_id to a specified download_folder.
    """

    mail_server = os.getenv("GMAIL_IMAP_SERVER", "imap.gmail.com")
    username = os.getenv("GMAIL_USERNAME")
    password = os.getenv("GMAIL_PASSWORD")

    if not username or not password:
        raise ValueError("Username and password must be provided")

    if not message_id:
        raise ValueError("Message ID must be provided")

    os.makedirs(download_folder, exist_ok=True)

    return download_attachments_by_message_id(
        mail_server=mail_server,
        username=username,
        password=password,
        message_id=message_id,
        download_folder=download_folder,
    )


if __name__ == "__main__":
    mcp.run()
