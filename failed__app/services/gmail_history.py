from googleapiclient.errors import HttpError


def fetch_gmail_history(
    gmail_service,
    user_id: str,
    start_history_id: str,
):
    """
    Returns:
        (history_records, new_history_id)
    """
    try:
        response = gmail_service.users().history().list(
            userId=user_id,
            startHistoryId=start_history_id,
            historyTypes=["messageAdded"],
        ).execute()
    except HttpError as e:
        if e.resp.status == 404:
            raise HistoryExpiredError()
        raise

    history = response.get("history", [])
    new_history_id = response.get("historyId")
    return history, new_history_id


class HistoryExpiredError(Exception):
    pass
