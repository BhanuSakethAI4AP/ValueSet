

// Insert Severity Levels
db.value_sets.insertOne({
  key: "severity_levels",
  status: "active",
  module: "Core",
  description: "Defines severity levels for incidents and alerts",
  items: [
    { code: "LOW", labels: { en: "Low", hi: "निम्न" } },
    { code: "MEDIUM", labels: { en: "Medium", hi: "मध्यम" } },
    { code: "HIGH", labels: { en: "High", hi: "उच्च" } },
    { code: "CRITICAL", labels: { en: "Critical", hi: "महत्वपूर्ण" } }
  ],
  createdAt: new Date(),
  createdBy: "system",
  updatedAt: null,
  updatedBy: null
});

// Insert Ticket Status
db.value_sets.insertOne({
  key: "ticket_status",
  status: "active",
  module: "Support",
  description: "Lifecycle statuses for support tickets",
  items: [
    { code: "OPEN", labels: { en: "Open", hi: "खुला" } },
    { code: "IN_PROGRESS", labels: { en: "In Progress", hi: "प्रगति में" } },
    { code: "RESOLVED", labels: { en: "Resolved", hi: "समाधान" } },
    { code: "CLOSED", labels: { en: "Closed", hi: "बंद" } }
  ],
  createdAt: new Date(),
  createdBy: "system",
  updatedAt: null,
  updatedBy: null
});

// Insert Priority Levels
db.value_sets.insertOne({
  key: "priority_levels",
  status: "active",
  module: "Core",
  description: "Defines priority levels for tasks and tickets",
  items: [
    { code: "P1", labels: { en: "Priority 1", hi: "प्राथमिकता 1" } },
    { code: "P2", labels: { en: "Priority 2", hi: "प्राथमिकता 2" } },
    { code: "P3", labels: { en: "Priority 3", hi: "प्राथमिकता 3" } },
    { code: "P4", labels: { en: "Priority 4", hi: "प्राथमिकता 4" } }
  ],
  createdAt: new Date(),
  createdBy: "system",
  updatedAt: null,
  updatedBy: null
});
