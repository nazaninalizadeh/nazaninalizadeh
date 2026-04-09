import React, { useEffect, useState } from 'react';
import axios from 'axios';
import { Bell, AlertCircle, Calendar, FileText, User } from 'lucide-react';
import { toast } from 'sonner';

const API_URL = process.env.REACT_APP_BACKEND_URL + '/api';

const Notifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchNotifications();
  }, []);

  const fetchNotifications = async () => {
    try {
      const { data } = await axios.get(`${API_URL}/notifications/pending`, {
        withCredentials: true,
      });
      setNotifications(data.notifications || []);
    } catch (error) {
      toast.error('Failed to load notifications');
    } finally {
      setLoading(false);
    }
  };

  const getIcon = (type) => {
    switch (type) {
      case 'rent_due':
        return <FileText size={20} />;
      case 'contract_expiry':
        return <Calendar size={20} />;
      case 'passport_expiry':
        return <User size={20} />;
      default:
        return <Bell size={20} />;
    }
  };

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'high':
        return 'bg-red-50 border-red-200 text-red-800';
      case 'medium':
        return 'bg-orange-50 border-orange-200 text-orange-800';
      case 'low':
        return 'bg-blue-50 border-blue-200 text-blue-800';
      default:
        return 'bg-slate-50 border-slate-200 text-slate-800';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-700 border-r-transparent" />
      </div>
    );
  }

  return (
    <div data-testid="notifications-page">
      <div className="mb-8">
        <h1 className="text-4xl font-semibold font-heading text-slate-900 mb-2" data-testid="notifications-title">
          Notifications & Reminders
        </h1>
        <p className="text-slate-600">Stay updated on rent due dates, contract expiry, and passport renewals</p>
      </div>

      {notifications.length === 0 ? (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-12 text-center">
          <Bell className="mx-auto text-slate-300 mb-4" size={64} />
          <h3 className="text-lg font-medium text-slate-900 mb-2">No Pending Notifications</h3>
          <p className="text-slate-600">You're all caught up! No reminders or alerts at the moment.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {notifications.map((notification, index) => (
            <div
              key={index}
              className={`p-4 rounded-lg border ${getPriorityColor(notification.priority)}`}
              data-testid={`notification-${index}`}
            >
              <div className="flex items-start gap-4">
                <div className="flex-shrink-0">
                  {getIcon(notification.type)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <h4 className="text-sm font-semibold">
                      {notification.type.replace('_', ' ').toUpperCase()}
                    </h4>
                    <span className="text-xs px-2 py-1 rounded-full bg-white/50">
                      {notification.priority} priority
                    </span>
                  </div>
                  <p className="text-sm">{notification.message}</p>
                  {(notification.due_date || notification.expiry_date) && (
                    <p className="text-xs mt-2 opacity-75">
                      Date: {notification.due_date || notification.expiry_date}
                    </p>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Notifications;
