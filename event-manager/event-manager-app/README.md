# Event Manager App

A React-based event management UI for creating and managing notification events across multiple channels.

## Project Structure

```
event-manager-app/
├── public/
│   └── index.html
├── src/
│   ├── components/
│   │   └── EventManager.js
│   ├── App.js
│   └── index.js
├── package.json
├── README.md
└── .gitignore
```

## Features

- **Event Search**: Filter events by name in real-time
- **Event CRUD**: Create, read, and edit notification events
- **Multi-Tab Form**:
  - **Tab 1**: Event details (name, type, region, priority, managers, source)
  - **Tab 2**: Channel selection and lookup configuration
  - **Tab 3**: Content creation for each selected channel
- **Channel Support**: SMS, Email, Push Notification, Webhook
- **API Integration**: Publishes events to backend API

## Installation

### Prerequisites
- Node.js (v14 or higher)
- npm or yarn

### Setup Steps

1. **Install dependencies**:
   ```bash
   npm install
   ```

2. **Start development server**:
   ```bash
   npm start
   ```
   The app will open at `http://localhost:3000`

3. **Build for production**:
   ```bash
   npm build
   ```

## API Integration

The app sends event data to: `POST /api/events/publish`

### JSON Payload Structure

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
        "content": "Welcome to our platform",
        "lookup": "Lookup1"
      },
      {
        "name": "Email",
        "content": "Welcome email body...",
        "lookup": null
      }
    ]
  },
  "timestamp": "2024-02-22T10:30:45.123Z"
}
```

## Configuration

### Available Channels
- SMS
- Email
- Push Notification
- Webhook

### Event Types
- Real time
- Scheduled

### Regions
- US
- EU
- APAC
- Global

### Priorities
- Low
- Medium
- High
- Critical

### Lookups
- Lookup1
- Lookup2
- Lookup3
- Lookup4

## Usage

1. **Create Event**: Click "Create Event" button
2. **Fill Details**: Enter event information in Tab 1
3. **Select Channels**: Choose notification channels in Tab 2
4. **Assign Lookups**: Optional - select lookup values for each channel
5. **Add Content**: Enter notification content for each channel in Tab 3
6. **Publish**: Click "Publish" to send to API

## Dependencies

- **react**: UI library
- **react-dom**: React DOM rendering
- **lucide-react**: Icon library
- **react-scripts**: Build and development tools

## Development

### Available Scripts

- `npm start` - Run development server
- `npm build` - Create optimized production build
- `npm test` - Run tests
- `npm eject` - Eject from create-react-app (irreversible)

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Notes

- Events are stored in memory (frontend state) - data persists during session only
- API calls use fetch API - no external HTTP library required
- Console logging shows the JSON payload before API submission
- Responsive design works on desktop and tablet screens

## API Documentation

Refer to `API_DOCUMENTATION.md` for detailed backend integration requirements.

## License

Proprietary
