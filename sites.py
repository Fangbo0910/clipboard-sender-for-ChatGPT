# Target sites in priority order with input selectors.
SITE_PRIORITY = [
    {
        "name": "chatgpt",
        "match": ["chatgpt.com"],
        "selectors": [
            "textarea#prompt-textarea",
            "textarea[data-id='prompt-textarea']",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
        ],
    },
    {
        "name": "aigoogle",
        "match": ["ai.google.com"],
        "selectors": [
            "div[contenteditable='true'][role='textbox']",
            "textarea[aria-label]",
            "div[contenteditable='true']",
        ],
    },
    {
        "name": "deepseek",
        "match": ["chat.deepseek.com"],
        "selectors": [
            "textarea",
            "div[contenteditable='true'][role='textbox']",
            "div[contenteditable='true']",
        ],
    },
]

CDP_URL = "http://127.0.0.1:9222"
EDGE_DEBUG_COMMAND = "msedge.exe --remote-debugging-port=9222 --user-data-dir=\"C:\\EdgeDebug\""
