import datetime
import json


def parse_jsonl_live_chat(live_chat_file):
    with open(live_chat_file) as f:
        for line in f:
            obj = json.loads(line)
            yield from handle_live_chat_obj(obj)


def handle_live_chat_obj(obj):
    chat_item = obj["replayChatItemAction"]
    actions = chat_item["actions"]
    offset_time = chat_item["videoOffsetTimeMsec"]
    assert len(actions) == 1
    action = actions[0]
    for key, value in action.items():
        assert key in {
            "addChatItemAction",
            "addLiveChatTickerItemAction",
            "addBannerToLiveChatCommand",
            "clickTrackingParams",
        }
        if key == "addChatItemAction":
            if res := handle_add_chat_item_action(value):
                res["timestamp"] = datetime.timedelta(seconds=int(offset_time) // 1000)
                yield res


def handle_add_chat_item_action(obj):
    assert obj.keys() <= {"clientId", "item"}
    item = obj["item"]
    assert len(item) == 1
    key, value = next(iter(item.items()))
    assert key in {
        "liveChatTextMessageRenderer",
        "liveChatPaidMessageRenderer",
        "liveChatViewerEngagementMessageRenderer",
        "liveChatMembershipItemRenderer",
        "liveChatPlaceholderItemRenderer",
        "liveChatSponsorshipsGiftPurchaseAnnouncementRenderer",
        "liveChatSponsorshipsGiftRedemptionAnnouncementRenderer",
        "liveChatPaidStickerRenderer",
    }, key
    if key == "liveChatTextMessageRenderer":
        timestamp = value["timestampText"]["simpleText"]
        author = value["authorName"]["simpleText"]
        message = "".join(handle_message_run(r) for r in value["message"]["runs"])
        return {"timestamp": timestamp, "author": author, "message": message}


def handle_message_run(run, emoji_codes=False):
    assert run.keys() <= {"text", "emoji", "navigationEndpoint"}, str(run.keys())
    text = ""
    for key, value in run.items():
        if key == "text":
            text += value
        if key == "emoji":
            if value.get("isCustomEmoji") or emoji_codes:
                if "shortcuts" in value:
                    # Some emojis don't have shortcuts (e.g: custom skin color)
                    text += min(value["shortcuts"], key=len)
            else:
                text += value["emojiId"]
    return text
