def extract_inbound_messages(payload: dict) -> list[dict]:
    results = []

    for entry in payload.get("entry", []):
        for change in entry.get("changes", []):
            value = change.get("value", {})
            messages = value.get("messages", [])
            for msg in messages:
                msg_type = msg.get("type")
                if msg_type != "text":
                    continue

                results.append(
                    {
                        "wa_message_id": msg.get("id"),
                        "from": msg.get("from"),
                        "text": msg.get("text", {}).get("body", ""),
                        "timestamp": msg.get("timestamp"),
                    }
                )

    return results