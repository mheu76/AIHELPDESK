'use client';

import { useState } from 'react';
import { ticketApi, Ticket, User } from '@/lib/api';

interface TicketQuickActionsProps {
  ticket: Ticket;
  user: User;
  onUpdate: () => void;
}

export default function TicketQuickActions({ ticket, user, onUpdate }: TicketQuickActionsProps) {
  const [isUpdating, setIsUpdating] = useState(false);
  const isITStaff = user.role === 'it_staff' || user.role === 'admin';

  if (!isITStaff) return null;

  const handleAssignToMe = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsUpdating(true);

    try {
      await ticketApi.updateTicket(ticket.id, {
        assignee_id: user.id,
        status: 'in_progress',
      });
      onUpdate();
    } catch (err) {
      console.error('Failed to assign ticket:', err);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleMarkResolved = async (e: React.MouseEvent) => {
    e.stopPropagation();
    setIsUpdating(true);

    try {
      await ticketApi.updateTicket(ticket.id, {
        status: 'resolved',
      });
      onUpdate();
    } catch (err) {
      console.error('Failed to resolve ticket:', err);
    } finally {
      setIsUpdating(false);
    }
  };

  const isAssignedToMe = ticket.assignee_id === user.id;

  return (
    <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
      {!isAssignedToMe && ticket.status === 'open' && (
        <button
          onClick={handleAssignToMe}
          disabled={isUpdating}
          className="rounded-md bg-blue-100 px-3 py-1 text-xs text-blue-700 transition-colors hover:bg-blue-200 disabled:opacity-50"
          title="Assign this ticket to me and mark it in progress"
        >
          {isUpdating ? '...' : 'Assign'}
        </button>
      )}

      {isAssignedToMe && ticket.status === 'in_progress' && (
        <button
          onClick={handleMarkResolved}
          disabled={isUpdating}
          className="rounded-md bg-green-100 px-3 py-1 text-xs text-green-700 transition-colors hover:bg-green-200 disabled:opacity-50"
          title="Mark this ticket as resolved"
        >
          {isUpdating ? '...' : 'Resolve'}
        </button>
      )}
    </div>
  );
}
