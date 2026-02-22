import React, { useState, useEffect } from 'react';
import { X, Plus, Search } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:5000';
const STORAGE_KEY = 'eventManagerEvents';

const EventManager = () => {
  // Initialize events from localStorage or empty array
  const [events, setEvents] = useState(() => {
    const stored = localStorage.getItem(STORAGE_KEY);
    return stored ? JSON.parse(stored) : [];
  });
  const [searchTerm, setSearchTerm] = useState('');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingId, setEditingId] = useState(null);
  const [activeTab, setActiveTab] = useState(1);
  const [loading, setLoading] = useState(false);
  const [notification, setNotification] = useState(null);

  // Sync events to localStorage whenever they change
  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(events));
  }, [events]);

  // Fetch events from backend on component mount
  useEffect(() => {
    fetchEventsFromBackend();
  }, []);

  // Helper function to show notifications
  const showNotification = (message, type = 'success') => {
    setNotification({ message, type });
    setTimeout(() => setNotification(null), 3000);
  };

  // Fetch all events from backend
  const fetchEventsFromBackend = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${BACKEND_URL}/api/events`);
      
      if (response.ok) {
        const result = await response.json();
        if (result.data && Array.isArray(result.data)) {
          // Transform backend events to frontend format
          const transformedEvents = result.data.map(event => ({
            id: event.eventId,
            name: event.name,
            type: event.type,
            region: event.region,
            priority: event.priority,
            managers: event.eventManagers || []
          }));
          setEvents(transformedEvents);
        }
      }
    } catch (error) {
      console.log('Offline mode: Using localStorage events');
      // Fail silently if backend is not available - use localStorage
    } finally {
      setLoading(false);
    }
  };
  
  const [formData, setFormData] = useState({
    name: '',
    type: 'real time',
    region: 'US',
    priority: 'medium',
    eventManagers: '',
    source: '',
    channels: [],
    channelContent: {},
    lookups: {}
  });

  const channels = ['SMS', 'Email', 'Push Notification', 'Webhook'];
  const lookupOptions = ['Lookup1', 'Lookup2', 'Lookup3', 'Lookup4'];
  const regions = ['US', 'EU', 'APAC', 'Global'];
  const priorities = ['low', 'medium', 'high', 'critical'];
  const types = ['real time', 'scheduled'];

  const filteredEvents = events.filter(event =>
    event.name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleCreateNew = () => {
    setEditingId(null);
    setFormData({
      name: '',
      type: 'real time',
      region: 'US',
      priority: 'medium',
      eventManagers: '',
      source: '',
      channels: [],
      channelContent: {},
      lookups: {}
    });
    setActiveTab(1);
    setShowCreateModal(true);
  };

  const handleEditEvent = (event) => {
    setEditingId(event.id);
    setFormData({
      name: event.name,
      type: event.type,
      region: event.region,
      priority: event.priority,
      eventManagers: event.managers.join(', '),
      source: '',
      channels: [],
      channelContent: {},
      lookups: {}
    });
    setActiveTab(1);
    setShowCreateModal(true);
  };

  const handleChannelToggle = (channel) => {
    setFormData(prev => {
      const newChannels = prev.channels.includes(channel)
        ? prev.channels.filter(c => c !== channel)
        : [...prev.channels, channel];
      
      const newChannelContent = { ...prev.channelContent };
      if (!newChannels.includes(channel)) {
        delete newChannelContent[channel];
      }
      
      return { ...prev, channels: newChannels, channelContent: newChannelContent };
    });
  };

  const handleChannelContentChange = (channel, content) => {
    setFormData(prev => ({
      ...prev,
      channelContent: { ...prev.channelContent, [channel]: content }
    }));
  };

  const handleLookupChange = (channel, lookup) => {
    setFormData(prev => ({
      ...prev,
      lookups: { ...prev.lookups, [channel]: lookup }
    }));
  };

  const buildPublishPayload = () => {
    return {
      eventId: editingId || Date.now(),
      name: formData.name,
      type: formData.type,
      region: formData.region,
      priority: formData.priority,
      eventManagers: formData.eventManagers.split(',').map(m => m.trim()).filter(m => m),
      source: formData.source,
      notificationConfig: {
        channels: formData.channels.map(channel => ({
          name: channel,
          content: formData.channelContent[channel] || '',
          lookup: formData.lookups[channel] || null
        }))
      },
      timestamp: new Date().toISOString()
    };
  };

  const handlePublish = async () => {
    const payload = buildPublishPayload();
    console.log('Publishing payload:', JSON.stringify(payload, null, 2));
    
    try {
      setLoading(true);
      
      // Try to send to backend
      try {
        const response = await fetch(`${BACKEND_URL}/api/events/publish`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(payload)
        });

        if (response.ok) {
          const result = await response.json();
          console.log('Event published to backend:', result);
          showNotification('Event published to backend successfully!', 'success');
        } else {
          console.warn('Backend returned error, saving locally');
          showNotification('Saved locally (backend unavailable)', 'warning');
        }
      } catch (backendError) {
        console.log('Backend not available, saving locally');
        showNotification('Saved locally (backend unavailable)', 'warning');
      }

      // Always update local state and localStorage
      if (editingId) {
        setEvents(events.map(e => e.id === editingId 
          ? { 
              id: editingId,
              name: formData.name, 
              type: formData.type, 
              region: formData.region, 
              priority: formData.priority, 
              managers: formData.eventManagers.split(',').map(m => m.trim()).filter(m => m)
            }
          : e
        ));
      } else {
        setEvents([...events, {
          id: payload.eventId,
          name: formData.name,
          type: formData.type,
          region: formData.region,
          priority: formData.priority,
          managers: formData.eventManagers.split(',').map(m => m.trim()).filter(m => m)
        }]);
      }
      
      setShowCreateModal(false);
    } catch (error) {
      console.error('Error publishing event:', error);
      showNotification('Error: ' + error.message, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ fontFamily: 'system-ui, -apple-system, sans-serif', backgroundColor: '#f8f8f8', minHeight: '100vh', padding: '20px' }}>
      {/* Notification */}
      {notification && (
        <div style={{
          position: 'fixed',
          top: '20px',
          right: '20px',
          padding: '12px 16px',
          borderRadius: '4px',
          backgroundColor: notification.type === 'success' ? '#10b981' : notification.type === 'error' ? '#ef4444' : '#f59e0b',
          color: 'white',
          zIndex: 2000,
          boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
          fontSize: '14px'
        }}>
          {notification.message}
        </div>
      )}

      <div style={{ maxWidth: '1200px', margin: '0 auto' }}>
        {/* Header */}
        <div style={{ marginBottom: '30px' }}>
          <h1 style={{ margin: '0 0 20px 0', fontSize: '28px', fontWeight: '600' }}>Event Manager</h1>
          
          {/* Search and Create */}
          <div style={{ display: 'flex', gap: '12px', marginBottom: '20px' }}>
            <div style={{ flex: 1, position: 'relative' }}>
              <Search style={{ position: 'absolute', left: '12px', top: '10px', width: '18px', height: '18px', color: '#999' }} />
              <input
                type="text"
                placeholder="Search events by name..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{
                  width: '100%',
                  padding: '10px 10px 10px 38px',
                  border: '1px solid #ddd',
                  borderRadius: '4px',
                  fontSize: '14px',
                  boxSizing: 'border-box'
                }}
              />
            </div>
            <button
              onClick={handleCreateNew}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '10px 16px',
                backgroundColor: '#2563eb',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500'
              }}
            >
              <Plus size={18} /> Create Event
            </button>
          </div>
        </div>

        {/* Events List */}
        <div style={{ backgroundColor: 'white', borderRadius: '4px', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          {filteredEvents.length === 0 ? (
            <div style={{ padding: '40px', textAlign: 'center', color: '#666' }}>
              No events found
            </div>
          ) : (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #eee', backgroundColor: '#f9f9f9' }}>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', fontSize: '13px' }}>Event Name</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', fontSize: '13px' }}>Type</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', fontSize: '13px' }}>Region</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', fontSize: '13px' }}>Priority</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', fontSize: '13px' }}>Managers</th>
                  <th style={{ padding: '12px', textAlign: 'left', fontWeight: '600', fontSize: '13px' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filteredEvents.map(event => (
                  <tr key={event.id} style={{ borderBottom: '1px solid #eee', hover: { backgroundColor: '#f5f5f5' } }}>
                    <td style={{ padding: '12px' }}>{event.name}</td>
                    <td style={{ padding: '12px' }}><span style={{ fontSize: '12px', backgroundColor: '#e8f0fe', padding: '4px 8px', borderRadius: '3px' }}>{event.type}</span></td>
                    <td style={{ padding: '12px' }}>{event.region}</td>
                    <td style={{ padding: '12px' }}>
                      <span style={{
                        fontSize: '12px',
                        padding: '4px 8px',
                        borderRadius: '3px',
                        backgroundColor: event.priority === 'critical' ? '#fee2e2' : event.priority === 'high' ? '#fef3c7' : '#dbeafe'
                      }}>
                        {event.priority}
                      </span>
                    </td>
                    <td style={{ padding: '12px', fontSize: '13px' }}>{event.managers.join(', ')}</td>
                    <td style={{ padding: '12px' }}>
                      <button
                        onClick={() => handleEditEvent(event)}
                        style={{
                          padding: '6px 12px',
                          backgroundColor: '#f3f4f6',
                          border: '1px solid #d1d5db',
                          borderRadius: '4px',
                          cursor: 'pointer',
                          fontSize: '12px',
                          fontWeight: '500'
                        }}
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      </div>

      {/* Create/Edit Modal */}
      {showCreateModal && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0,0,0,0.5)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 1000
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '4px',
            width: '90%',
            maxWidth: '800px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 4px 6px rgba(0,0,0,0.1)'
          }}>
            {/* Modal Header */}
            <div style={{
              padding: '16px',
              borderBottom: '1px solid #eee',
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <h2 style={{ margin: 0, fontSize: '18px', fontWeight: '600' }}>
                {editingId ? 'Edit Event' : 'Create Event'}
              </h2>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px' }}
              >
                <X size={20} />
              </button>
            </div>

            {/* Tab Navigation */}
            <div style={{
              display: 'flex',
              borderBottom: '1px solid #eee',
              backgroundColor: '#fafafa'
            }}>
              {[1, 2, 3].map(tabNum => (
                <button
                  key={tabNum}
                  onClick={() => setActiveTab(tabNum)}
                  style={{
                    flex: 1,
                    padding: '12px',
                    border: 'none',
                    backgroundColor: activeTab === tabNum ? 'white' : 'transparent',
                    borderBottom: activeTab === tabNum ? '2px solid #2563eb' : 'none',
                    cursor: 'pointer',
                    fontWeight: activeTab === tabNum ? '600' : '500',
                    fontSize: '14px',
                    color: activeTab === tabNum ? '#2563eb' : '#666'
                  }}
                >
                  {tabNum === 1 && 'Event Details'}
                  {tabNum === 2 && 'Channels & Lookups'}
                  {tabNum === 3 && 'Content'}
                </button>
              ))}
            </div>

            {/* Modal Content */}
            <div style={{ flex: 1, overflow: 'auto', padding: '20px' }}>
              {/* Tab 1: Event Details */}
              {activeTab === 1 && (
                <div>
                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500', fontSize: '14px' }}>Event Name *</label>
                    <input
                      type="text"
                      value={formData.name}
                      onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '14px',
                        boxSizing: 'border-box'
                      }}
                      placeholder="e.g., User Signup"
                    />
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500', fontSize: '14px' }}>Type *</label>
                      <select
                        value={formData.type}
                        onChange={(e) => setFormData({ ...formData, type: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          fontSize: '14px',
                          boxSizing: 'border-box'
                        }}
                      >
                        {types.map(t => <option key={t} value={t}>{t}</option>)}
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500', fontSize: '14px' }}>Region *</label>
                      <select
                        value={formData.region}
                        onChange={(e) => setFormData({ ...formData, region: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          fontSize: '14px',
                          boxSizing: 'border-box'
                        }}
                      >
                        {regions.map(r => <option key={r} value={r}>{r}</option>)}
                      </select>
                    </div>
                  </div>

                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '16px' }}>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500', fontSize: '14px' }}>Priority *</label>
                      <select
                        value={formData.priority}
                        onChange={(e) => setFormData({ ...formData, priority: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          fontSize: '14px',
                          boxSizing: 'border-box'
                        }}
                      >
                        {priorities.map(p => <option key={p} value={p}>{p}</option>)}
                      </select>
                    </div>
                    <div>
                      <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500', fontSize: '14px' }}>Source</label>
                      <input
                        type="text"
                        value={formData.source}
                        onChange={(e) => setFormData({ ...formData, source: e.target.value })}
                        style={{
                          width: '100%',
                          padding: '8px 12px',
                          border: '1px solid #ddd',
                          borderRadius: '4px',
                          fontSize: '14px',
                          boxSizing: 'border-box'
                        }}
                        placeholder="e.g., User Service"
                      />
                    </div>
                  </div>

                  <div style={{ marginBottom: '16px' }}>
                    <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500', fontSize: '14px' }}>Event Managers</label>
                    <input
                      type="text"
                      value={formData.eventManagers}
                      onChange={(e) => setFormData({ ...formData, eventManagers: e.target.value })}
                      style={{
                        width: '100%',
                        padding: '8px 12px',
                        border: '1px solid #ddd',
                        borderRadius: '4px',
                        fontSize: '14px',
                        boxSizing: 'border-box'
                      }}
                      placeholder="Comma-separated names, e.g., John, Jane"
                    />
                  </div>
                </div>
              )}

              {/* Tab 2: Channels & Lookups */}
              {activeTab === 2 && (
                <div>
                  <div style={{ marginBottom: '20px' }}>
                    <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', fontWeight: '600' }}>Select Channels</h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      {channels.map(channel => (
                        <label key={channel} style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer', fontSize: '14px' }}>
                          <input
                            type="checkbox"
                            checked={formData.channels.includes(channel)}
                            onChange={() => handleChannelToggle(channel)}
                            style={{ cursor: 'pointer' }}
                          />
                          {channel}
                        </label>
                      ))}
                    </div>
                  </div>

                  {formData.channels.length > 0 && (
                    <div>
                      <h3 style={{ margin: '20px 0 12px 0', fontSize: '14px', fontWeight: '600' }}>Channel Lookups</h3>
                      {formData.channels.map(channel => (
                        <div key={channel} style={{ marginBottom: '16px' }}>
                          <label style={{ display: 'block', marginBottom: '6px', fontWeight: '500', fontSize: '13px' }}>
                            {channel} Lookup
                          </label>
                          <select
                            value={formData.lookups[channel] || ''}
                            onChange={(e) => handleLookupChange(channel, e.target.value)}
                            style={{
                              width: '100%',
                              padding: '8px 12px',
                              border: '1px solid #ddd',
                              borderRadius: '4px',
                              fontSize: '14px',
                              boxSizing: 'border-box'
                            }}
                          >
                            <option value="">-- None --</option>
                            {lookupOptions.map(lookup => (
                              <option key={lookup} value={lookup}>{lookup}</option>
                            ))}
                          </select>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Tab 3: Content */}
              {activeTab === 3 && (
                <div>
                  {formData.channels.length === 0 ? (
                    <p style={{ color: '#666', fontSize: '14px' }}>Please select at least one channel in the "Channels & Lookups" tab</p>
                  ) : (
                    formData.channels.map(channel => (
                      <div key={channel} style={{ marginBottom: '20px' }}>
                        <label style={{ display: 'block', marginBottom: '8px', fontWeight: '600', fontSize: '14px' }}>
                          {channel} Content
                        </label>
                        <textarea
                          value={formData.channelContent[channel] || ''}
                          onChange={(e) => handleChannelContentChange(channel, e.target.value)}
                          placeholder={`Enter ${channel} content here...`}
                          style={{
                            width: '100%',
                            padding: '12px',
                            border: '1px solid #ddd',
                            borderRadius: '4px',
                            fontSize: '14px',
                            fontFamily: 'monospace',
                            minHeight: '120px',
                            boxSizing: 'border-box',
                            resize: 'vertical'
                          }}
                        />
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div style={{
              padding: '16px',
              borderTop: '1px solid #eee',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: '12px'
            }}>
              <button
                onClick={() => setShowCreateModal(false)}
                style={{
                  padding: '8px 16px',
                  backgroundColor: '#f3f4f6',
                  border: '1px solid #d1d5db',
                  borderRadius: '4px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                Cancel
              </button>
              {activeTab > 1 && (
                <button
                  onClick={() => setActiveTab(activeTab - 1)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#f3f4f6',
                    border: '1px solid #d1d5db',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  Previous
                </button>
              )}
              {activeTab < 3 && (
                <button
                  onClick={() => setActiveTab(activeTab + 1)}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: '#2563eb',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  Next
                </button>
              )}
              {activeTab === 3 && (
                <button
                  onClick={handlePublish}
                  disabled={!formData.name || formData.channels.length === 0 || loading}
                  style={{
                    padding: '8px 16px',
                    backgroundColor: !formData.name || formData.channels.length === 0 || loading ? '#ccc' : '#10b981',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: !formData.name || formData.channels.length === 0 || loading ? 'not-allowed' : 'pointer',
                    fontSize: '14px',
                    fontWeight: '500'
                  }}
                >
                  {loading ? 'Publishing...' : 'Publish'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EventManager;
