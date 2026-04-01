'use client';

import { useState } from 'react';
import { ticketApi, User, Ticket } from '@/lib/api';

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
    e.stopPropagation(); // Prevent row click

    setIsUpdating(true);
    try {
      await ticketApi.updateTicket(ticket.id, {
        assignee_id: user.id,
        status: 'in_progress'
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
        status: 'resolved'
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
          className="px-3 py-1 text-xs bg-blue-100 text-blue-700 hover:bg-blue-200 rounded-md transition-colors disabled:opacity-50"
          title="나에게 할당하고 진행중으로 변경"
        >
          {isUpdating ? '...' : '담당하기'}
        </button>
      )}

      {isAssignedToMe && ticket.status === 'in_progress' && (
        <button
          onClick={handleMarkResolved}
          disabled={isUpdating}
          className="px-3 py-1 text-xs bg-green-100 text-green-700 hover:bg-green-200 rounded-md transition-colors disabled:opacity-50"
          title="티켓을 해결됨으로 표시"
        >
          {isUpdating ? '...' : '해결완료'}
        </button>
      )}
    </div>
  );
}
