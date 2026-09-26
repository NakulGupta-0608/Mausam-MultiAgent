import React from 'react';
import { Bell, X, CheckCheck, AlertTriangle, AlertCircle, Info, ShieldAlert } from 'lucide-react';

const SEVERITY_ICONS = {
  warning: <AlertTriangle className="w-4 h-4 text-amber-400 shrink-0" />,
  danger: <AlertCircle className="w-4 h-4 text-rose-400 shrink-0" />,
  info: <Info className="w-4 h-4 text-cyan-400 shrink-0" />,
  success: <CheckCheck className="w-4 h-4 text-emerald-400 shrink-0" />,
};

export default function NotificationCenter({
  isOpen,
  onClose,
  notifications,
  onMarkRead,
  onMarkAllRead,
}) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fadeIn">
      {/* Click outside to close */}
      <div className="flex-1" onClick={onClose} />

      <div className="w-full max-w-md bg-slate-900 border-l border-slate-800 h-full flex flex-col shadow-2xl overflow-hidden">
        {/* Header */}
        <div className="p-5 border-b border-slate-800 flex items-center justify-between bg-slate-950/60">
          <div className="flex items-center space-x-2">
            <Bell className="w-5 h-5 text-cyan-400" />
            <h3 className="font-bold text-white text-base">Weather Notification Center</h3>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Action bar */}
        <div className="px-5 py-2.5 bg-slate-950/30 border-b border-slate-800/80 flex items-center justify-between text-xs">
          <span className="text-slate-400">
            {notifications.filter((n) => !n.read).length} Unread Advisories
          </span>
          <button
            onClick={onMarkAllRead}
            className="text-cyan-400 hover:text-cyan-300 font-medium flex items-center gap-1 transition-colors"
          >
            <CheckCheck className="w-3.5 h-3.5" /> Mark all as read
          </button>
        </div>

        {/* Notification list */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {notifications.length === 0 ? (
            <div className="py-16 text-center text-slate-500 space-y-2">
              <ShieldAlert className="w-10 h-10 mx-auto text-slate-600" />
              <p className="text-sm">No active weather warnings or alerts</p>
            </div>
          ) : (
            notifications.map((item) => (
              <div
                key={item.id}
                onClick={() => onMarkRead(item.id)}
                className={`p-3.5 rounded-xl border text-xs cursor-pointer transition-all space-y-1.5 ${
                  item.read
                    ? 'bg-slate-900/40 border-slate-800/60 opacity-75'
                    : 'bg-slate-850/80 border-cyan-500/30 shadow-md ring-1 ring-cyan-500/10'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    {SEVERITY_ICONS[item.severity] || SEVERITY_ICONS.info}
                    <span className="font-semibold text-slate-100">{item.title}</span>
                  </div>
                  {!item.read && (
                    <span className="w-2 h-2 rounded-full bg-cyan-400 animate-pulse" />
                  )}
                </div>

                <p className="text-slate-300 leading-relaxed pl-6">
                  {item.message}
                </p>

                <div className="flex items-center justify-between text-[10px] text-slate-500 pl-6 pt-1">
                  <span>{item.location || 'Regional Envelope'}</span>
                  <span>{new Date(item.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                </div>
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}
