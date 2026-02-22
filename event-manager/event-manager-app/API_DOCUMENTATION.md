# Event Manager API Documentation

## Overview
The Event Manager UI allows users to create and configure events for notification distribution across multiple channels (SMS, Email, Push, Webhook). This document outlines the JSON payload structure and API integration details.

## JSON Payload Structure

### Example Payload
```json
{
  "eventId": 1707123456789,
  "name": "User Signup",
  "type": "real time",
  "region": "US",
  "priority": "high",
  "eventManagers": ["John", "Jane"],
  "source": "User Service",
  "notificationConfig": {
    "channels": [
      {
        "name": "SMS",
        "content": "Hello {{firstName}}, welcome to our platform!",
        "lookup": "Lookup1"
      },
      {
        "name": "Email",
        "content": "Welcome email body with HTML content...",
        "lookup": "Lookup2"
      },
      {
        "name": "Push Notification",
        "content": "Quick welcome notification",
        "lookup": null
      }
    ]
  },
  "timestamp": "2024-02-22T10:30:45.123Z"
}
```

## Field Descriptions

### Top Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| eventId | number | Yes | Unique event identifier. Generated as timestamp if creating new, or existing ID if editing |
| name | string | Yes | Event name (e.g., "User Signup", "Payment Failed") |
| type | string | Yes | Either "real time" or "scheduled" - determines when event triggers |
| region | string | Yes | Geographic region: "US", "EU", "APAC", or "Global" |
| priority | string | Yes | Event priority: "low", "medium", "high", or "critical" |
| eventManagers | array | No | List of manager names responsible for the event |
| source | string | No | Source system or service that triggers the event |
| notificationConfig | object | Yes | Contains channel configuration details |
| timestamp | string | Yes | ISO 8601 formatted timestamp when event was created/updated |

### notificationConfig Object

Contains an array of `channels`, each with:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| name | string | Yes | Channel type: "SMS", "Email", "Push Notification", or "Webhook" |
| content | string | Yes | The actual content/template to send via this channel |
| lookup | string | No | Optional lookup reference (e.g., "Lookup1", "Lookup2") for additional configuration |

## API Endpoint

### Create/Update Event

**Endpoint:** `POST /api/events/publish`

**Headers:**
```
Content-Type: application/json
```

**Request Body:** JSON payload as shown above

**Success Response (200 OK):**
```json
{
  "success": true,
  "eventId": 1707123456789,
  "message": "Event published successfully",
  "status": "active"
}
```

**Error Response (400/500):**
```json
{
  "success": false,
  "error": "Event name is required",
  "code": "VALIDATION_ERROR"
}
```

## Implementation Notes

### Validation Rules
- Event name must not be empty
- At least one channel must be selected
- Channel content should not be empty for selected channels
- Event type must be one of: "real time", "scheduled"
- Region must be one of: "US", "EU", "APAC", "Global"
- Priority must be one of: "low", "medium", "high", "critical"

### Content Template Variables
Event managers can use template variables in channel content using `{{variableName}}` syntax:
- `{{firstName}}` - User's first name
- `{{lastName}}` - User's last name
- `{{email}}` - User's email address
- `{{eventName}}` - Name of the event
- Custom variables as needed

### Lookup References
Lookups provide a way to reference additional configuration or template data:
- Each channel can have an optional lookup
- Lookups are stored separately and retrieved by the backend
- Example: "Lookup1" might reference a template collection for SMS messages

## UI to Backend Flow

1. **User Fills Form**
   - Tab 1: Event details (name, type, region, priority, managers, source)
   - Tab 2: Select channels and assign lookups
   - Tab 3: Enter content for each selected channel

2. **Build Payload**
   - JavaScript code constructs the JSON payload from form data
   - Validates required fields before submission

3. **Submit API Call**
   - POST request sent to `/api/events/publish`
   - User gets confirmation or error message

4. **Update UI**
   - Event is added/updated in the events list
   - Modal closes
   - Success notification displays

## Backend Integration Checklist

- [ ] Create `/api/events/publish` endpoint
- [ ] Validate incoming payload structure
- [ ] Store event configuration in database
- [ ] Create event record with unique ID
- [ ] Store channel-specific content
- [ ] Link lookups to channels
- [ ] Return success/error response
- [ ] Implement event retrieval for search/list
- [ ] Add event update functionality
- [ ] Implement notification sending based on event config

## Notes for Backend Developers

- The UI currently stores events in-memory for demo purposes
- In production, events should be persisted in a database
- Consider implementing soft-delete for events
- Add timestamps for created_at and updated_at
- Consider adding event versioning for change tracking
- Implement audit logs for who created/modified events
- Add webhooks or pub/sub for event triggers
