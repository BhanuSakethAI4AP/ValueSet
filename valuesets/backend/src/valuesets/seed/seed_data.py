seed_value_sets = [
    {
        "key": "errorSeverity",
        "status": "active",
        "description": "Severity levels for errors",
        "items": [
            {"code": "CRITICAL", "labels": {"en": "Critical", "hi": "गंभीर"}},
            {"code": "HIGH", "labels": {"en": "High", "hi": "उच्च"}},
            {"code": "MEDIUM", "labels": {"en": "Medium", "hi": "मध्यम"}},
            {"code": "LOW", "labels": {"en": "Low", "hi": "कम"}}
        ]
    },
    {
        "key": "errorType",
        "status": "active",
        "description": "Types of errors in the system",
        "items": [
            {"code": "Business", "labels": {"en": "Business Error", "hi": "व्यावसायिक त्रुटि"}},
            {"code": "System", "labels": {"en": "System Error", "hi": "सिस्टम त्रुटि"}},
            {"code": "Integration", "labels": {"en": "Integration Error", "hi": "एकीकरण त्रुटि"}}
        ]
    },
    {
        "key": "sourceType",
        "status": "active",
        "description": "Source types for errors and events",
        "items": [
            {"code": "api", "labels": {"en": "API", "hi": "एपीआई"}},
            {"code": "function", "labels": {"en": "Function", "hi": "फंक्शन"}},
            {"code": "screen", "labels": {"en": "Screen", "hi": "स्क्रीन"}},
            {"code": "job", "labels": {"en": "Background Job", "hi": "पृष्ठभूमि कार्य"}}
        ]
    },
    {
        "key": "environment",
        "status": "active",
        "description": "Application environment types",
        "items": [
            {"code": "prod", "labels": {"en": "Production", "hi": "उत्पादन"}},
            {"code": "stg", "labels": {"en": "Staging", "hi": "स्टेजिंग"}},
            {"code": "dev", "labels": {"en": "Development", "hi": "विकास"}}
        ]
    },
    {
        "key": "otpChannel",
        "status": "active",
        "description": "OTP delivery channels",
        "items": [
            {"code": "sms", "labels": {"en": "SMS", "hi": "एसएमएस"}},
            {"code": "email", "labels": {"en": "Email", "hi": "ईमेल"}},
            {"code": "whatsapp", "labels": {"en": "WhatsApp", "hi": "व्हाट्सएप"}}
        ]
    }
]