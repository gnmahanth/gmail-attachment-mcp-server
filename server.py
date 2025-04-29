import email
import imaplib
import logging
import os
import sys
from email.header import decode_header
from typing import List, Optional

from mcp.server.fastmcp import FastMCP

# Configure logging to log to stderr with file name and line number
logger = logging.getLogger()
if not logger.hasHandlers():
    handler = logging.StreamHandler(sys.stderr)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def save_attachment(part, download_folder: str, message_id: str) -> Optional[str]:
    filename = part.get_filename()
    if filename:
        filename_decoded, enc = decode_header(filename)[0]
        if isinstance(filename_decoded, bytes):
            try:
                filename = filename_decoded.decode(enc or "utf-8")
            except Exception:
                filename = filename_decoded.decode("utf-8", errors="replace")
        else:
            filename = filename_decoded

        unique_filepath = os.path.join(download_folder, f"{message_id}_{filename}")
        if os.path.exists(unique_filepath):
            logger.warning(
                f"Attachment file {unique_filepath} already exists and will be overwritten."
            )

        with open(unique_filepath, "wb") as f:
            f.write(part.get_payload(decode=True))

        logger.info(f"Attachment {filename} saved to {unique_filepath}")

        return unique_filepath

    return None


def download_attachments_by_message_id(
    mail_server: str,
    username: str,
    password: str,
    message_id: str,
    download_folder: str,
) -> List[str]:
    """
    Download attachments from a Gmail message by message_id to a specified download_folder.
    Returns:
        List[str]: A list of file paths of the downloaded attachments.
    """
    mail = None
    saved_files = []
    try:
        try:
            message_id_int = int(message_id, 16)
        except ValueError:
            logger.error(
                "Invalid message ID format. Please provide a valid hexadecimal string."
            )
            return []
        mail = imaplib.IMAP4_SSL(mail_server)
        mail.login(username, password)
        mail.select("inbox")

        # Gmail uses X-GM-MSGID for search
        search_criteria = f'X-GM-MSGID "{message_id_int}"'
        typ, data = mail.search(None, search_criteria)

        if data[0]:
            for num in data[0].split():
                typ, msg_data = mail.fetch(num, "(RFC822)")
                msg = email.message_from_bytes(msg_data[0][1])
                for part in msg.walk():
                    if part.get_content_maintype() == "multipart":
                        continue
                    content_disposition = part.get("Content-Disposition")
                    if content_disposition:
                        dispositions = content_disposition.strip().split(";")
                        if any(d.strip().lower() == "attachment" for d in dispositions):
                            filepath = save_attachment(
                                part, download_folder, message_id
                            )
                            if filepath:
                                saved_files.append(filepath)
            if not saved_files:
                logger.info("No attachments found in the email.")
            return saved_files
        else:
            logger.error("No email found with that message ID.")
            return []
    except imaplib.IMAP4.error as e:
        logger.error(f"IMAP error: {e}")
        return []
    finally:
        if mail is not None:
            try:
                mail.logout()
            except Exception:
                pass


mcp = FastMCP(
    "gmail-attachment-mcp-server",
)


@mcp.tool()
def download_attachments_tool(
    message_id: str, download_folder="./attachments"
) -> List[str]:
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
