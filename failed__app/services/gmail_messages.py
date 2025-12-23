def fetch_gmail_message(gmail_service, user_id: str, message_id: str):
    return gmail_service.users().messages().get(
        userId=user_id,
        id=message_id,
        format="full",
    ).execute()
